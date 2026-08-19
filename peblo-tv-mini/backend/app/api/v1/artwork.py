import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import Show, Episode, Artwork, User
from backend.app.services.artwork_service import ArtworkService
from backend.app.storage import get_storage
from backend.app.api.deps import require_editor_or_admin

router = APIRouter(prefix="/artwork", tags=["Artwork Management"])

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_artwork(
    artwork_type: str = Form(..., description="poster, banner, or thumbnail"),
    entity_type: str = Form(..., description="show or episode"),
    entity_id: str = Form(..., description="Show or Episode UUID / identifier"),
    file: UploadFile = File(..., description="Artwork image file"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin)
):
    # 1. Read binary bytes
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )

    # 2. Server-side validation
    art_type_clean = artwork_type.lower().strip()
    ent_type_clean = entity_type.lower().strip()

    if ent_type_clean not in ["show", "episode"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="entity_type must be either 'show' or 'episode'."
        )

    val_res = ArtworkService.validate_artwork(file_bytes, art_type_clean, file.filename or "")
    if not val_res.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Artwork validation failed.",
                "artwork_type": art_type_clean,
                "reasons": val_res.errors
            }
        )

    # 3. Locate target entity in PostgreSQL
    show_id: Optional[uuid.UUID] = None
    episode_id: Optional[uuid.UUID] = None
    episode_obj: Optional[Episode] = None

    if ent_type_clean == "show":
        show = None
        try:
            show = db.query(Show).filter(Show.id == uuid.UUID(entity_id)).first()
        except (ValueError, AttributeError):
            show = db.query(Show).filter(Show.slug == entity_id).first()

        if not show:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Show '{entity_id}' not found."
            )
        show_id = show.id
    else:
        try:
            episode_obj = db.query(Episode).filter(Episode.id == uuid.UUID(entity_id)).first()
        except (ValueError, AttributeError):
            episode_obj = db.query(Episode).filter(Episode.custom_id == entity_id).first()

        if not episode_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode '{entity_id}' not found."
            )
        episode_id = episode_obj.id

    # 4. Generate safe storage filename and path
    storage = get_storage()
    file_ext = (file.filename or "").split(".")[-1].lower()
    if file_ext not in ["jpg", "jpeg", "png", "webp"]:
        file_ext = "jpg"

    safe_filename = f"{art_type_clean}_{uuid.uuid4().hex[:12]}.{file_ext}"
    relative_path = f"uploads/{ent_type_clean}s/{str(show_id or episode_id)}/{safe_filename}"

    # 5. Persist bytes via Storage interface
    url = storage.upload(file_bytes, relative_path, content_type=val_res.mime_type)

    # 6. Upsert metadata in PostgreSQL
    existing_artwork = None
    if show_id:
        existing_artwork = db.query(Artwork).filter(
            Artwork.show_id == show_id,
            Artwork.artwork_type == art_type_clean
        ).first()
    else:
        existing_artwork = db.query(Artwork).filter(
            Artwork.episode_id == episode_id,
            Artwork.artwork_type == art_type_clean
        ).first()

    if existing_artwork:
        # Delete old storage file
        if existing_artwork.file_path and existing_artwork.file_path != relative_path:
            storage.delete(existing_artwork.file_path)

        existing_artwork.file_path = relative_path
        existing_artwork.url = url
        existing_artwork.width = val_res.width
        existing_artwork.height = val_res.height
        existing_artwork.file_size_bytes = val_res.file_size_bytes
        existing_artwork.mime_type = val_res.mime_type
        artwork_record = existing_artwork
    else:
        artwork_record = Artwork(
            entity_type=ent_type_clean,
            show_id=show_id,
            episode_id=episode_id,
            artwork_type=art_type_clean,
            file_path=relative_path,
            url=url,
            width=val_res.width,
            height=val_res.height,
            file_size_bytes=val_res.file_size_bytes,
            mime_type=val_res.mime_type
        )
        db.add(artwork_record)

    # If episode, update artwork_available list
    if episode_obj:
        avail = list(episode_obj.artwork_available or [])
        if art_type_clean not in avail:
            avail.append(art_type_clean)
            episode_obj.artwork_available = avail

    db.commit()
    db.refresh(artwork_record)

    return {
        "id": str(artwork_record.id),
        "entity_type": artwork_record.entity_type,
        "entity_id": str(show_id or episode_id),
        "artwork_type": artwork_record.artwork_type,
        "url": artwork_record.url,
        "file_path": artwork_record.file_path,
        "width": artwork_record.width,
        "height": artwork_record.height,
        "file_size_bytes": artwork_record.file_size_bytes,
        "mime_type": artwork_record.mime_type
    }
