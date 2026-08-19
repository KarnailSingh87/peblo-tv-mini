from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.episode import Episode
from backend.app.models.season import Season

class EpisodeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, episode_id: str) -> Optional[Episode]:
        return self.db.query(Episode).filter(
            (Episode.custom_id == episode_id) | (Episode.id == (int(episode_id) if episode_id.isdigit() else -1))
        ).first()

    def get_by_content_group_and_lang(self, content_group: str, language: str) -> Optional[Episode]:
        return self.db.query(Episode).filter(
            Episode.content_group == content_group,
            Episode.language == language
        ).first()

    def list_episodes(
        self,
        show_id: Optional[int] = None,
        season_number: Optional[int] = None,
        language: Optional[str] = None,
        status: Optional[str] = None,
        content_group: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Episode]:
        query = self.db.query(Episode).join(Season, Episode.season_id == Season.id)
        if show_id:
            query = query.filter(Episode.show_id == show_id)
        if season_number is not None:
            query = query.filter(Season.season_number == season_number)
        if language:
            query = query.filter(Episode.language == language)
        if status:
            query = query.filter(Episode.status == status)
        if content_group:
            query = query.filter(Episode.content_group == content_group)
        if search:
            pattern = f"%{search}%"
            query = query.filter((Episode.episode_title.ilike(pattern)) | (Episode.content_group.ilike(pattern)))
        return query.order_by(Episode.show_id.asc(), Season.season_number.asc(), Episode.episode_number.asc()).all()

    def create(self, episode: Episode) -> Episode:
        self.db.add(episode)
        self.db.commit()
        self.db.refresh(episode)
        return episode

    def update(self, episode: Episode) -> Episode:
        self.db.commit()
        self.db.refresh(episode)
        return episode

    def delete(self, episode: Episode) -> None:
        self.db.delete(episode)
        self.db.commit()
