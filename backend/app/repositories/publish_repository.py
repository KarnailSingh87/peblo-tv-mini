from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.publish_run import PublishRun

class PublishRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_success(self) -> Optional[PublishRun]:
        return self.db.query(PublishRun).filter(PublishRun.status == "success").order_by(PublishRun.version.desc()).first()

    def get_by_id(self, run_id: int) -> Optional[PublishRun]:
        return self.db.query(PublishRun).filter(PublishRun.id == run_id).first()

    def list_history(self, limit: int = 50) -> List[PublishRun]:
        return self.db.query(PublishRun).order_by(PublishRun.id.desc()).limit(limit).all()

    def record_run(self, run: PublishRun) -> PublishRun:
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run
