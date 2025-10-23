"""Database models for repository configuration."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint

from app.database import Base


class RepositoryConfig(Base):
    """Configuration for repositories to be scanned on a schedule."""

    __tablename__ = "repository_configs"

    id = Column(Integer, primary_key=True)
    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)
    default_ref = Column(String, default="main")
    enabled = Column(Boolean, default=True)
    scan_schedule = Column(String, default="0 2 * * *")  # Daily at 2 AM UTC
    scanner_preference = Column(String, default="both")  # osv, github, both

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("owner", "name", name="uq_repo_owner_name"),)
