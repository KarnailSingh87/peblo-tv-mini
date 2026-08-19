import os
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.db.session import engine, Base, get_db
from backend.app.api.v1.router import api_router
from backend.app.storage import get_storage

local_storage_path = os.path.abspath(settings.LOCAL_STORAGE_DIR)
os.makedirs(local_storage_path, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database schema on startup
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Peblo TV Mini — Backend Platform API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get(f"{settings.API_V1_STR}/storage/{{file_path:path}}", tags=["Storage"])
def serve_storage_file(file_path: str):
    storage = get_storage()
    clean_path = file_path.lstrip("/")
    full_local = os.path.abspath(os.path.join(local_storage_path, clean_path))

    if not full_local.startswith(local_storage_path) or not os.path.exists(full_local):
        raise HTTPException(status_code=404, detail="File not found")

    content_type = "application/octet-stream"
    if clean_path.endswith(".json"):
        content_type = "application/json"
    elif clean_path.endswith((".jpg", ".jpeg")):
        content_type = "image/jpeg"
    elif clean_path.endswith(".png"):
        content_type = "image/png"
    elif clean_path.endswith(".webp"):
        content_type = "image/webp"

    return FileResponse(full_local, media_type=content_type)

app.include_router(api_router, prefix=settings.API_V1_STR)

def _perform_health_check(db: Session) -> dict:
    db_healthy = False
    db_error = None
    try:
        db.execute(text("SELECT 1"))
        db_healthy = True
    except Exception as e:
        db_healthy = False
        db_error = str(e)

    storage_healthy = False
    try:
        storage = get_storage()
        storage_healthy = os.path.exists(local_storage_path) if settings.STORAGE_TYPE == "local" else True
    except Exception:
        storage_healthy = False

    is_overall_healthy = db_healthy and storage_healthy

    payload = {
        "status": "healthy" if is_overall_healthy else "unhealthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "database": {
            "status": "connected" if db_healthy else "disconnected",
            "error": db_error if not db_healthy else None
        },
        "storage": {
            "status": "accessible" if storage_healthy else "inaccessible",
            "type": settings.STORAGE_TYPE
        }
    }
    return payload, is_overall_healthy

@app.get("/health", tags=["Health"])
def root_health_check(response: Response, db: Session = Depends(get_db)):
    """Root health check endpoint for load balancers and orchestrator probes."""
    payload, is_healthy = _perform_health_check(db)
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload

@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
def api_v1_health_check(response: Response, db: Session = Depends(get_db)):
    """Versioned health check endpoint under /api/v1/health."""
    payload, is_healthy = _perform_health_check(db)
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload
