from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class ArtworkInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    artwork_type: str  # "poster", "banner", "thumbnail"
    url: str
    file_path: Optional[str] = None
    width: int
    height: int
    file_size_bytes: int
    mime_type: str

class ArtworkValidationResult(BaseModel):
    valid: bool
    artwork_type: str
    width: int
    height: int
    aspect_ratio: float
    file_size_bytes: int
    errors: List[str] = []
    warnings: List[str] = []
    url: Optional[str] = None
