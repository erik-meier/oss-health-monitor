"""Health check routes."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "oss-health-monitor"}


@router.get("/health/db")
async def database_health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Health check endpoint that verifies database connectivity."""
    try:
        # Execute a simple query to verify database connection
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        return {
            "status": "healthy",
            "service": "oss-health-monitor",
            "database": "connected",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "oss-health-monitor",
            "database": "disconnected",
            "error": str(e),
        }
