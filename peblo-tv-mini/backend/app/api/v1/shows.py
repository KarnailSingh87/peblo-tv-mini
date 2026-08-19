import math
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.db.session import get_db
from backend.app.models.entities import Show, Season, Episode, User
from backend.app.schemas.crud_schemas import (
    ShowCreate, ShowUpdate, ShowDetailResponse, ShowListResponse,
    SeasonCreate, SeasonResponse, PaginatedResponse
)
from backend.app.api.deps import require_editor_or_admin, get_current_user

router = APIRouter(prefix="/shows", tags=["Shows & Seasons"])

def _find_show(show_id_or_slug: str, db: Session) -> Show:
    """Finds a show by UUID or slug, or raises 404."""
    show = None
    try:
        val_uuid = uuid.UUID(show_id_or_slug)
        show = db.query(Show).filter(Show.id == val_uuid).first()
    except (ValueError, AttributeError):
        pass

    if not show:
        show = db.query(Show).filter(Show.slug == show_id_or_slug).first()

    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Show '{show_id_or_slug}' was not found in the catalogue."
        )
    return show

# 1. GET /shows (Paginated + Filtered)
@router.get("", response_model=PaginatedResponse[ShowListResponse])
def list_shows(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    section: Optional[str] = Query(None, description="Filter by section (featured, series, minisodes, songs)"),
    status: Optional[str] = Query(None, description="Filter by status (draft, published)"),
    category: Optional[str] = Query(None, description="Filter by category tag"),
    search: Optional[str] = Query(None, description="Search across title, slug, or synopsis"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Show)

    if section:
        query = query.filter(Show.section == section)
    if status:
        query = query.filter(Show.status == status)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Show.title.ilike(search_pattern),
                Show.slug.ilike(search_pattern),
                Show.synopsis.ilike(search_pattern)
            )
        )

    all_shows = query.order_by(Show.title.asc()).all()

    # In-memory category filter if requested
    if category:
        all_shows = [s for s in all_shows if category.lower() in [c.lower() for c in (s.categories or [])]]

    total = len(all_shows)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    paged_shows = all_shows[offset : offset + page_size]

    items = []
    for s in paged_shows:
        eps = db.query(Episode).filter(Episode.show_id == s.id).all()
        langs = sorted(list(set(e.language for e in eps)))
        items.append(ShowListResponse(
            id=s.id,
            title=s.title,
            slug=s.slug,
            section=s.section,
            categories=s.categories or [],
            synopsis=s.synopsis,
            status=s.status,
            episode_count=len(eps),
            languages=langs,
            created_at=s.created_at,
            updated_at=s.updated_at
        ))

    return PaginatedResponse[ShowListResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

# 2. POST /shows (Create Show)
@router.post("", response_model=ShowDetailResponse, status_code=status.HTTP_201_CREATED)
def create_show(
    payload: ShowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin)
):
    # Rule 1: Unique slug
    if db.query(Show).filter(Show.slug == payload.slug).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The slug '{payload.slug}' is already in use by another show. Please provide a unique slug."
        )

    # Rule 2: Published show requires section
    if payload.status == "published" and not payload.section:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A published show must be assigned to a section (featured, series, minisodes, songs)."
        )

    show = Show(
        title=payload.title,
        slug=payload.slug,
        section=payload.section,
        categories=payload.categories,
        synopsis=payload.synopsis,
        status=payload.status
    )
    db.add(show)
    db.flush()

    # Automatically create Season 0 (Trailers) and Season 1
    s0 = Season(show_id=show.id, season_number=0, title="Trailers")
    s1 = Season(show_id=show.id, season_number=1, title="Season 1")
    db.add_all([s0, s1])
    db.commit()
    db.refresh(show)

    return show

# 3. GET /shows/{id}
@router.get("/{id}", response_model=ShowDetailResponse)
def get_show(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return _find_show(id, db)

# 4. PUT /shows/{id}
@router.put("/{id}", response_model=ShowDetailResponse)
def update_show(
    id: str,
    payload: ShowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin)
):
    show = _find_show(id, db)

    # Check slug uniqueness if updating slug
    if payload.slug and payload.slug != show.slug:
        if db.query(Show).filter(Show.slug == payload.slug).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The slug '{payload.slug}' is already in use by another show."
            )

    new_status = payload.status or show.status
    new_section = payload.section if payload.section is not None else show.section

    # Published show requires section
    if new_status == "published" and not new_section:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot publish show without assigning a valid section (featured, series, minisodes, songs)."
        )

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(show, field, val)

    db.commit()
    db.refresh(show)
    return show

# 5. DELETE /shows/{id}
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_show(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin)
):
    show = _find_show(id, db)
    db.delete(show)
    db.commit()
    return None

# --- Seasons Endpoints on Show ---

# 6. GET /shows/{show_id}/seasons
@router.get("/{show_id}/seasons", response_model=List[SeasonResponse])
def list_show_seasons(
    show_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    show = _find_show(show_id, db)
    seasons = db.query(Season).filter(Season.show_id == show.id).order_by(Season.season_number.asc()).all()
    return seasons

# 7. POST /shows/{show_id}/seasons
@router.post("/{show_id}/seasons", response_model=SeasonResponse, status_code=status.HTTP_201_CREATED)
def create_show_season(
    show_id: str,
    payload: SeasonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin)
):
    show = _find_show(show_id, db)

    existing = db.query(Season).filter(
        Season.show_id == show.id,
        Season.season_number == payload.season_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Season number {payload.season_number} already exists for show '{show.title}'."
        )

    season = Season(
        show_id=show.id,
        season_number=payload.season_number,
        title=payload.title or ("Trailers" if payload.season_number == 0 else f"Season {payload.season_number}")
    )
    db.add(season)
    db.commit()
    db.refresh(season)
    return season
