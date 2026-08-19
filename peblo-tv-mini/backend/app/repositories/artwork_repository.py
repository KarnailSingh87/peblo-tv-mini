from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.artwork import Artwork

class ArtworkRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_entity_and_type(self, entity_type: str, entity_id: str, artwork_type: str) -> Optional[Artwork]:
        return self.db.query(Artwork).filter(
            Artwork.entity_type == entity_type.lower(),
            Artwork.entity_id == str(entity_id),
            Artwork.artwork_type == artwork_type.lower()
        ).first()

    def list_by_entity(self, entity_type: str, entity_id: str) -> List[Artwork]:
        return self.db.query(Artwork).filter(
            Artwork.entity_type == entity_type.lower(),
            Artwork.entity_id == str(entity_id)
        ).all()

    def create_or_update(self, artwork: Artwork) -> Artwork:
        self.db.add(artwork)
        self.db.commit()
        self.db.refresh(artwork)
        return artwork
