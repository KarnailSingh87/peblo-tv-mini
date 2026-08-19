from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.catalog import CatalogueShow

class SearchResultItem(BaseModel):
    id: int
    title: str
    slug: str
    section: str
    categories: List[str] = []
    synopsis: str = ""
    artwork: Dict[str, str] = {}
    available_languages: List[str] = []
    total_episodes: int
    matched_episodes: List[str] = Field(
        default_factory=list,
        description="Titles of specific episodes matching the search query"
    )

class SearchResponse(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    section: Optional[str] = None
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[SearchResultItem] = []
