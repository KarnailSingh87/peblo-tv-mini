import math
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.db.session import get_db
from backend.app.models.entities import Show, Season, Episode, User, Artwork
from backend.app.schemas.crud_schemas import (
    EpisodeCreate, EpisodeUpdate, EpisodeResponse, PaginatedResponse
)
from backend.app.api.deps import require_editor_or_admin, get_current_user

router = APIRouter(tags=["Episodes & Seasons"])

def _find_episode(episode_id: str, db: Session) -> Episode:
    """Finds an episode by UUID or custom_id ('ep_0001'), or raises 404."""
    ep = None
    try:
        val_uuid = uuid.UUID(episode_id)
        ep = db.query(Episode).filter(Episode.id == val_uuid).first()
    except (ValueError, AttributeError):
        pass

    if not ep:
        ep = db.query(Episode).filter(Episode.custom_id == episode_id).first()

    if not ep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode '{episode_id}' was not found in the catalogue."
        )
    return ep

def _find_season(season_id: str, db: Session) -> Season:
    """Finds a season by UUID or raises 404."""
    try:
        val_uuid = uuid.UUID(season_id)
        season = db.query(Season).filter(Season.id == val_uuid).first()
    except (ValueError, AttributeError):
        season = None

    if not season:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Season '{season_id}' was not found."
        )
    return season

# 1. GET /seasons/{season_id}/episodes
@router.get("/seasons/{season_id}/episodes", response_model=List[EpisodeResponse])
def list_season_episodes(
    season_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    season = _find_season(season_id, db)
    return db.query(Episode).filter(Episode.season_id == season.id).order_by(Episode.episode_number.asc()).all()

# 2. POST /seasons/{season_id}/episodes
@router.post("/seasons/{season_id}/episodes", response_model=EpisodeResponse, status_code=status.HTTP_201_CREATED)
def create_season_episode(
    season_id: str,
    payload: EpisodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin)
):
    season = _find_season(season_id, db)

    # Rule 1: Check uniqueness of (content_group, language)
    conflict = db.query(Episode).filter(
        Episode.content_group == payload.content_group,
        Episode.language == payload.language
    ).first()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An episode with content group '{payload.content_group}' and language '{payload.language}' already exists (Episode ID: '{conflict.custom_id or conflict.id}', title: '{conflict.episode_title}'). Audio language variants within a content group must be unique."
        )

    # Rule 2: Check custom_id uniqueness if provided
    if payload.custom_id and db.query(Episode).filter(Episode.custom_id == payload.custom_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The custom ID '{payload.custom_id}' is already in use by another episode."
        )

    # Rule 3: Published episode requires positive duration
    if payload.status == "published":
        if not payload.duration_seconds or payload.duration_seconds <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A published episode must have a valid positive duration in seconds."
            )
        if not payload.artwork_available:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A published episode must have artwork available (e.g. thumbnail, poster)."
            )

    ep = Episode(
        custom_id=payload.custom_id,
        show_id=season.show_id,
        season_id=season.id,
        episode_number=payload.episode_number,
        episode_title=payload.episode_title,
        duration_seconds=payload.duration_seconds,
        language=payload.language,
        content_group=payload.content_group,
        status=payload.status,
        artwork_available=payload.artwork_available
    )
    db.add(ep)
    db.commit()
    db.refresh(ep)
    return ep

# 3. GET /episodes/{id}
@router.get("/episodes/{id}", response_model=EpisodeResponse)
def get_episode(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return _find_episode(id, db)

# 4. PUT /episodes/{id}
@router.put("/episodes/{id}", response_model=EpisodeResponse)
def update_episode(
    id: str,
    payload: EpisodeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin)
):
    ep = _find_episode(id, db)

    new_cg = payload.content_group or ep.content_group
    new_lang = payload.language or ep.language
    new_status = payload.status or ep.status
    new_duration = payload.duration_seconds if payload.duration_seconds is not None else ep.duration_seconds
    new_art = payload.artwork_available if payload.artwork_available is not None else ep.artwork_available

    # Check (content_group, language) uniqueness if altered
    if (new_cg != ep.content_group) or (new_lang != ep.language):
        conflict = db.query(Episode).filter(
            Episode.content_group == new_cg,
            Episode.language == new_lang,
            Episode.id != ep.id
        ).first()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update episode: Content group '{new_cg}' with language '{new_lang}' already exists on episode '{conflict.custom_id or conflict.id}'."
            )

    # Check published constraints
    if new_status == "published":
        if not new_duration or new_duration <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot publish episode without a positive runtime duration in seconds."
            )
        # Check artwork uploaded or specified in artwork_available
        has_art = bool(new_art) or db.query(Artwork).filter(Artwork.episode_id == ep.id).first() is not None
        if not has_art:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot publish episode without at least one artwork asset (thumbnail)."
            )

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(ep, field, val)

    db.commit()
    db.refresh(ep)
    return ep

# 5. DELETE /episodes/{id}
@router.delete("/episodes/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_episode(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin)
):
    ep = _find_episode(id, db)
    db.delete(ep)
    db.commit()
    return None

# 6. GET /episodes (Search & Paginated List)
@router.get("/episodes", response_model=PaginatedResponse[EpisodeResponse])
def list_episodes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    language: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    content_group: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Episode)
    if language:
        query = query.filter(Episode.language == language)
    if status:
        query = query.filter(Episode.status == status)
    if content_group:
        query = query.filter(Episode.content_group == content_group)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Episode.episode_title.ilike(search_pattern),
                Episode.content_group.ilike(search_pattern),
                Episode.custom_id.ilike(search_pattern)
            )
        )

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    items = query.order_by(Episode.created_at.desc()).offset(offset).limit(page_size).all()

    return PaginatedResponse[EpisodeResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
