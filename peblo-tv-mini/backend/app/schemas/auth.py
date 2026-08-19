from pydantic import BaseModel, ConfigDict
from typing import Dict, Any
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class UserBase(BaseModel):
    username: str
    email: str
    role: str = "editor"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
    created_at: datetime

class LoginRequest(BaseModel):
    username: str
    password: str
