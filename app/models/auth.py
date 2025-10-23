"""Database models for authentication."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String

from app.database import Base


class APIKey(Base):
    """API keys for server-to-server authentication."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    key_hash = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)  # Human-readable name for the key
    scopes = Column(JSON, nullable=True)  # List of allowed scopes
    rate_limit = Column(Integer, nullable=True)  # Requests per hour
    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
