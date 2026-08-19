from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from backend.app.core.config import settings

class EpisodeBase(BaseModel):
    episode_number: int = Field(ge=1, default=1)
    episode_title: str
    duration_seconds: Optional[int] = None
    language: str = Field(default="en")
    content_group: str
    status: str = Field(default="draft")
    artwork_available: List[str] = Field(default_factory=list)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in settings.ALLOWED_LANGUAGES:
            raise ValueError(f"Language '{v}' is invalid. Allowed: {settings.ALLOWED_LANGUAGES}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ["draft", "published"]:
            raise ValueError("Status must be 'draft' or 'published'")
        return v

class EpisodeCreate(EpisodeBase):
    show_id: int
    season_number: int = 1
    custom_id: Optional[str] = None

class EpisodeUpdate(BaseModel):
    episode_number: Optional[int] = None
    episode_title: Optional[str] = None
    duration_seconds: Optional[int] = None
    language: Optional[str] = None
    content_group: Optional[str] = None
    status: Optional[str] = None
    artwork_available: Optional[List[str]] = None
    season_number: Optional[int] = None

class EpisodeResponse(EpisodeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    custom_id: Optional[str] = None
    show_id: int
    season_id: int
    season_number: int
    show_title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
