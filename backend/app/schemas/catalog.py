from pydantic import BaseModel, ConfigDict
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

class CatalogueEpisodeVariant(BaseModel):
    language: str
    episode_id: str
    episode_title: str
    duration_seconds: Optional[int] = None

class CatalogueEpisode(BaseModel):
    content_group: str
    episode_number: int
    title: str
    duration_seconds: int
    languages: List[str]
    artwork: Dict[str, str] = {}
    variants: List[CatalogueEpisodeVariant] = []

class CatalogueSeason(BaseModel):
    season_number: int
    title: str
    episodes: List[CatalogueEpisode] = []

class CatalogueShow(BaseModel):
    id: int
    title: str
    slug: str
    section: str
    categories: List[str]
    synopsis: str
    artwork: Dict[str, str] = {}
    available_languages: List[str] = []
    total_episodes: int = 0
    seasons: List[CatalogueSeason] = []
    trailers: List[CatalogueEpisode] = []

class CatalogueSection(BaseModel):
    section: str
    title: str
    shows: List[CatalogueShow] = []

class Catalogue(BaseModel):
    version: int
    published_at: str
    total_shows: int
    total_episodes: int
    featured: Optional[CatalogueShow] = None
    sections: List[CatalogueSection] = []

class PublishResponse(BaseModel):
    success: bool
    version: int
    published_at: str
    shows_published: int
    episodes_published: int
    message: str
    catalogue_url: str
    publish_run_id: int

class PublishRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    version: int
    catalogue_version: Optional[int] = None
    triggered_by: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    show_count: int
    episode_count: int
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    metadata_json: Dict[str, Any] = {}
    created_at: datetime
