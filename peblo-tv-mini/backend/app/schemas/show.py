from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
from backend.app.core.config import settings
from backend.app.schemas.artwork import ArtworkInfo
from backend.app.schemas.episode import EpisodeResponse

class SeasonBase(BaseModel):
    season_number: int = 1
    title: Optional[str] = None

class SeasonResponse(SeasonBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    show_id: int
    episodes: List[EpisodeResponse] = []
    created_at: datetime

class ShowBase(BaseModel):
    title: str
    slug: str
    section: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    synopsis: Optional[str] = None
    status: str = Field(default="draft")

    @field_validator("section")
    @classmethod
    def validate_section(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "" and v not in settings.ALLOWED_SECTIONS:
            raise ValueError(f"Section '{v}' is invalid. Allowed: {settings.ALLOWED_SECTIONS}")
        return v if v != "" else None

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: List[str]) -> List[str]:
        for cat in v:
            if cat not in settings.ALLOWED_CATEGORIES:
                raise ValueError(f"Category '{cat}' is invalid. Allowed: {settings.ALLOWED_CATEGORIES}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ["draft", "published"]:
            raise ValueError("Status must be 'draft' or 'published'")
        return v

class ShowCreate(ShowBase):
    pass

class ShowUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    section: Optional[str] = None
    categories: Optional[List[str]] = None
    synopsis: Optional[str] = None
    status: Optional[str] = None

class ShowDetailResponse(ShowBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
    seasons: List[SeasonResponse] = []
    artwork: Dict[str, Optional[ArtworkInfo]] = {}

class ShowListResponse(ShowBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
    episode_count: int = 0
    languages: List[str] = []
    artwork: Dict[str, Optional[ArtworkInfo]] = {}
