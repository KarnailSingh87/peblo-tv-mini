import uuid
from typing import Optional, List, Generic, TypeVar
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from backend.app.core.config import settings

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

# --- Episode Schemas ---
class EpisodeBase(BaseModel):
    episode_number: int = Field(ge=0, default=1, description="Order within season (>=0, 0 reserved for trailers)")
    episode_title: str = Field(min_length=1, max_length=255)
    duration_seconds: Optional[int] = Field(None, ge=1, description="Runtime in seconds (>0)")
    language: str = Field(default="en", description="Allowed language code ('en' or 'hi')")
    content_group: str = Field(min_length=1, max_length=100, description="Canonical grouping key for language variants")
    status: str = Field(default="draft", description="'draft' or 'published'")
    artwork_available: List[str] = Field(default_factory=list, description="List of available artwork types")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in settings.ALLOWED_LANGUAGES:
            raise ValueError(f"Language '{v}' is not supported. Allowed languages are: {', '.join(settings.ALLOWED_LANGUAGES)}.")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ["draft", "published"]:
            raise ValueError("Status must be either 'draft' or 'published'.")
        return v

class EpisodeCreate(EpisodeBase):
    custom_id: Optional[str] = Field(None, max_length=50, description="Optional custom ID like 'ep_0001'")

class EpisodeUpdate(BaseModel):
    episode_number: Optional[int] = Field(None, ge=0)
    episode_title: Optional[str] = Field(None, min_length=1, max_length=255)
    duration_seconds: Optional[int] = Field(None, ge=1)
    language: Optional[str] = None
    content_group: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = None
    artwork_available: Optional[List[str]] = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in settings.ALLOWED_LANGUAGES:
            raise ValueError(f"Language '{v}' is not supported. Allowed languages are: {', '.join(settings.ALLOWED_LANGUAGES)}.")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ["draft", "published"]:
            raise ValueError("Status must be either 'draft' or 'published'.")
        return v

class EpisodeResponse(EpisodeBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    custom_id: Optional[str] = None
    show_id: uuid.UUID
    season_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

# --- Season Schemas ---
class SeasonBase(BaseModel):
    season_number: int = Field(ge=0, default=1, description="0 for Trailers, 1..N for numbered seasons")
    title: Optional[str] = Field(None, max_length=255)

class SeasonCreate(SeasonBase):
    pass

class SeasonResponse(SeasonBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    show_id: uuid.UUID
    episodes: List[EpisodeResponse] = []
    created_at: datetime
    updated_at: datetime

# --- Show Schemas ---
class ShowBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    section: Optional[str] = Field(None, description="Homepage section ('featured', 'series', 'minisodes', 'songs')")
    categories: List[str] = Field(default_factory=list)
    synopsis: Optional[str] = None
    status: str = Field(default="draft", description="'draft' or 'published'")

    @field_validator("section")
    @classmethod
    def validate_section(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "" and v not in settings.ALLOWED_SECTIONS:
            raise ValueError(f"Section '{v}' is invalid. Allowed sections are: {', '.join(settings.ALLOWED_SECTIONS)}.")
        return v if v != "" else None

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: List[str]) -> List[str]:
        for cat in v:
            if cat not in settings.ALLOWED_CATEGORIES:
                raise ValueError(f"Category '{cat}' is not permitted. Allowed categories are: {', '.join(settings.ALLOWED_CATEGORIES)}.")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ["draft", "published"]:
            raise ValueError("Status must be either 'draft' or 'published'.")
        return v

class ShowCreate(ShowBase):
    pass

class ShowUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    section: Optional[str] = None
    categories: Optional[List[str]] = None
    synopsis: Optional[str] = None
    status: Optional[str] = None

    @field_validator("section")
    @classmethod
    def validate_section(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "" and v not in settings.ALLOWED_SECTIONS:
            raise ValueError(f"Section '{v}' is invalid. Allowed sections are: {', '.join(settings.ALLOWED_SECTIONS)}.")
        return v if v != "" else None

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            for cat in v:
                if cat not in settings.ALLOWED_CATEGORIES:
                    raise ValueError(f"Category '{cat}' is not permitted. Allowed categories are: {', '.join(settings.ALLOWED_CATEGORIES)}.")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ["draft", "published"]:
            raise ValueError("Status must be either 'draft' or 'published'.")
        return v

class ShowDetailResponse(ShowBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    seasons: List[SeasonResponse] = []

class ShowListResponse(ShowBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    episode_count: int = 0
    languages: List[str] = []
    created_at: datetime
    updated_at: datetime
