from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.show import Show
from backend.app.models.season import Season

class ShowRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, show_id: int) -> Optional[Show]:
        return self.db.query(Show).filter(Show.id == show_id).first()

    def get_by_slug(self, slug: str) -> Optional[Show]:
        return self.db.query(Show).filter(Show.slug == slug).first()

    def list_shows(
        self,
        section: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Show]:
        query = self.db.query(Show)
        if section:
            query = query.filter(Show.section == section)
        if status:
            query = query.filter(Show.status == status)
        if search:
            pattern = f"%{search}%"
            query = query.filter((Show.title.ilike(pattern)) | (Show.synopsis.ilike(pattern)))
        return query.order_by(Show.id.asc()).all()

    def create(self, show: Show) -> Show:
        self.db.add(show)
        self.db.commit()
        self.db.refresh(show)
        return show

    def update(self, show: Show) -> Show:
        self.db.commit()
        self.db.refresh(show)
        return show

    def delete(self, show: Show) -> None:
        self.db.delete(show)
        self.db.commit()
