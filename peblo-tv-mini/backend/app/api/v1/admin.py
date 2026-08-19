from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import User, PublishRun
from backend.app.schemas.validation import ValidationReportResponse
from backend.app.schemas.catalog import PublishRunResponse
from backend.app.services.validation_service import ValidationService
from backend.app.services.publisher import CataloguePublisher, PublishingError
from backend.app.api.deps import require_admin, require_editor_or_admin

router = APIRouter(prefix="/admin", tags=["Admin Operations"])

@router.get("/validation-report", response_model=ValidationReportResponse)
def get_validation_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor_or_admin)
):
    """
    Accessible to Editors and Admins.
    Returns comprehensive catalog audit report with all blocking errors and warnings.
    """
    return ValidationService.audit_catalog(db)

@router.post("/catalog/publish", status_code=status.HTTP_200_OK)
def publish_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Restricted strictly to Admin role.
    Runs pre-flight validation audit, performs zero-downtime atomic catalogue replacement,
    and logs a PublishRun audit record in PostgreSQL.
    """
    try:
        run, catalog_data = CataloguePublisher.publish(db, current_user)
        return {
            "status": "success",
            "message": "Catalogue successfully compiled and published atomically.",
            "publish_run": {
                "id": str(run.id),
                "triggered_by": run.triggered_by,
                "started_at": run.started_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "status": run.status,
                "catalogue_version": run.catalogue_version,
                "show_count": run.show_count,
                "episode_count": run.episode_count,
                "file_path": run.file_path,
                "file_size_bytes": run.file_size_bytes
            }
        }
    except PublishingError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Catalogue publication rejected due to validation blockers.",
                "message": str(e),
                "blockers": e.blockers
            }
        )

@router.get("/catalog/publish-runs", response_model=List[PublishRunResponse])
def get_publish_runs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Restricted strictly to Admin role.
    Returns publish history ordered from newest to oldest.
    """
    runs = db.query(PublishRun).order_by(PublishRun.created_at.desc(), PublishRun.version.desc()).all()
    return runs
