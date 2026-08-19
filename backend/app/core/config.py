import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Dict, Any

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "Peblo TV Mini API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://peblo_user:peblo_password@localhost:5432/peblo_tv_db")

    # Storage
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  # "local" | "r2" | "s3"
    LOCAL_STORAGE_DIR: str = os.getenv("LOCAL_STORAGE_DIR", "./storage")

    # Cloudflare R2 / S3 Storage Credentials
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "")
    S3_ACCESS_KEY_ID: str = os.getenv("S3_ACCESS_KEY_ID", "")
    S3_SECRET_ACCESS_KEY: str = os.getenv("S3_SECRET_ACCESS_KEY", "")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "peblo-tv-catalog")
    S3_REGION_NAME: str = os.getenv("S3_REGION_NAME", "auto")
    S3_PUBLIC_BASE_URL: str = os.getenv("S3_PUBLIC_BASE_URL", "")

    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "temporary-dev-secret-key-change-in-production-min32chars")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "*"
    ]

    # Reference Data Rules
    ALLOWED_SECTIONS: List[str] = ["featured", "series", "minisodes", "songs"]
    ALLOWED_CATEGORIES: List[str] = [
        "adventure", "folk", "friendship", "india", "language",
        "learning", "maths", "music", "nature", "reading",
        "science", "singalong", "stories", "travel", "values"
    ]
    ALLOWED_LANGUAGES: List[str] = ["en", "hi"]

    # Artwork Constraints
    MAX_IMAGE_SIZE_BYTES: int = 200 * 1024  # 200 KB
    ARTWORK_SPECS: Dict[str, Any] = {
        "poster": {"aspect": "2:3", "target_px": (600, 900), "max_kb": 200},
        "banner": {"aspect": "16:9", "target_px": (1280, 720), "max_kb": 200},
        "thumbnail": {"aspect": "16:9", "target_px": (640, 360), "max_kb": 200}
    }

settings = Settings()
