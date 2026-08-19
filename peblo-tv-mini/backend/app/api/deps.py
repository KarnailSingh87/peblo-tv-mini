from typing import Optional, List
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.security import decode_access_token
from backend.app.db.session import get_db
from backend.app.models.entities import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_name: Optional[str] = Header(None, alias="X-User-Name"),
    db: Session = Depends(get_db)
) -> User:
    """
    Extracts the authenticated user from JWT token or fallback dev role header.
    Raises 401 Unauthorized if invalid or not provided.
    """
    if token:
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        username: str = payload["sub"]
        user = db.query(User).filter(User.username == username).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account does not exist or is inactive.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return user

    # Development header simulation
    if x_user_role:
        role = x_user_role.lower()
        if role in ["admin", "editor"]:
            username = x_user_name or f"{role}_user"
            user = db.query(User).filter(User.username == username).first()
            if not user:
                user = db.query(User).filter(User.role == role).first()
            if user and user.is_active:
                return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Please provide a valid Bearer token.",
        headers={"WWW-Authenticate": "Bearer"}
    )

def require_role(roles: List[str]):
    """
    Dependency factory enforcing strict role-based access control.
    Returns 403 Forbidden if user's role is not authorized.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires role in {roles}, got '{current_user.role}'."
            )
        return current_user
    return role_checker

require_editor_or_admin = require_role(["editor", "admin"])
require_admin = require_role(["admin"])
