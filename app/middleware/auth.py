"""Authentication middleware for API key validation."""

import hashlib
from datetime import datetime

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import APIKey

security = HTTPBearer()


def hash_api_key(key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(key.encode()).hexdigest()


async def get_current_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
) -> APIKey:
    """
    Validate API key from Authorization header.

    Args:
        credentials: HTTP Bearer token credentials
        db: Database session

    Returns:
        APIKey model if valid

    Raises:
        HTTPException: 401 if invalid or expired
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
        )

    key_hash = hash_api_key(credentials.credentials)

    api_key = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if not api_key.enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has been disabled",
        )

    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    # Update last used timestamp
    api_key.last_used_at = datetime.utcnow()
    db.commit()

    return api_key


class AuthMiddleware:
    """Middleware for API key authentication (if needed for global auth)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # For now, we'll use dependency injection for auth
        # This can be expanded if global middleware is needed
        await self.app(scope, receive, send)
