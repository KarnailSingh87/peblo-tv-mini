import json
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.entities import PublishRun, User
from backend.app.services.catalog_generator import CatalogueGenerator, CatalogueGenerationError
from backend.app.services.validation_service import ValidationService
from backend.app.storage import get_storage

class PublishingError(Exception):
    def __init__(self, message: str, blockers: list = None):
        super().__init__(message)
        self.blockers = blockers or []

class CataloguePublisher:
    """
    Orchestrates atomic publication of the streaming catalogue.
    
    Guarantees:
    - Pre-flight validation audit (blocks if any critical errors exist)
    - Zero-downtime atomic rename (readers never see partial writes)
    - Resilient rollback (failed publish leaves existing catalogue 100% intact)
    - Full PostgreSQL audit trail via PublishRun records
    """

    @classmethod
    def get_next_version(cls, db: Session) -> int:
        last_run = (
            db.query(PublishRun)
            .filter(PublishRun.status == "success")
            .order_by(PublishRun.version.desc())
            .first()
        )
        return (last_run.version + 1) if last_run else 1

    @classmethod
    def publish(cls, db: Session, user: User) -> Tuple[PublishRun, Dict[str, Any]]:
        started_at = datetime.utcnow()
        next_version = cls.get_next_version(db)

        # 1. Create in-progress publish run record
        run = PublishRun(
            triggered_by=user.username,
            started_at=started_at,
            status="failed",  # Default to failed until completed
            version=next_version
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # 2. Run validation audit
        report = ValidationService.audit_catalog(db)
        if not report.can_publish:
            blocker_msgs = [f"[{i.code}] {i.problem}" for i in report.all_issues if i.severity == "blocking"]
            run.completed_at = datetime.utcnow()
            run.status = "failed"
            run.error_message = f"Validation failed with {len(blocker_msgs)} blockers: {'; '.join(blocker_msgs[:3])}"
            db.commit()
            raise PublishingError(
                f"Catalogue publication rejected: {len(blocker_msgs)} blocking data validation errors found.",
                blockers=blocker_msgs
            )

        # 3. Generate pure catalogue JSON
        try:
            catalogue_obj = CatalogueGenerator.generate_catalogue(db, version=next_version, check_validation=False)
            catalog_dict = catalogue_obj.model_dump()
            catalog_json_bytes = json.dumps(catalog_dict, indent=2, ensure_ascii=False).encode("utf-8")
        except Exception as e:
            run.completed_at = datetime.utcnow()
            run.status = "failed"
            run.error_message = f"Catalogue compilation error: {str(e)}"
            db.commit()
            raise PublishingError(f"Catalogue generation failed: {str(e)}")

        # 4. Write to atomic temporary file on storage disk
        storage_dir = os.path.abspath(settings.LOCAL_STORAGE_DIR)
        os.makedirs(storage_dir, exist_ok=True)

        tmp_filename = f"catalogue_v{next_version}_{uuid.uuid4().hex[:8]}.tmp.json"
        tmp_filepath = os.path.join(storage_dir, tmp_filename)

        live_filename = "catalogue.json"
        live_filepath = os.path.join(storage_dir, live_filename)

        archive_filename = f"catalogue_v{next_version}.json"
        archive_filepath = os.path.join(storage_dir, archive_filename)

        try:
            # Step 4a: Write complete payload to temporary file
            with open(tmp_filepath, "wb") as f:
                f.write(catalog_json_bytes)
                f.flush()
                os.fsync(f.fileno())  # Ensure all bytes are committed to physical disk

            # Step 4b: Save versioned archive copy
            with open(archive_filepath, "wb") as f:
                f.write(catalog_json_bytes)
                f.flush()
                os.fsync(f.fileno())

            # Step 5: ATOMIC RENAME (os.replace is atomic on POSIX/Windows)
            # Atomically swaps tmp_filepath -> live_filepath. Readers never see a partial file.
            os.replace(tmp_filepath, live_filepath)

        except Exception as e:
            # Clean up temp file on failure
            if os.path.exists(tmp_filepath):
                try:
                    os.remove(tmp_filepath)
                except Exception:
                    pass
            run.completed_at = datetime.utcnow()
            run.status = "failed"
            run.error_message = f"Disk I/O error during atomic write: {str(e)}"
            db.commit()
            raise PublishingError(f"Failed to persist catalogue to storage: {str(e)}")

        # 6. Update PublishRun success record
        completed_at = datetime.utcnow()
        run.completed_at = completed_at
        run.status = "success"
        run.show_count = catalogue_obj.total_shows
        run.episode_count = catalogue_obj.total_episodes
        run.file_path = "catalogue.json"
        run.file_size_bytes = len(catalog_json_bytes)
        run.error_message = None
        db.commit()
        db.refresh(run)

        return run, catalog_dict
