"""Health check routes."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.database_init import check_database_health

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy"}


@router.get("/health/db")
async def database_health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Health check endpoint that verifies database connectivity and schema."""
    try:
        # Execute a simple query to verify database connection
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        
        # Check if all required tables exist
        is_healthy = check_database_health()
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "database": "connected",
            "schema": "complete" if is_healthy else "incomplete",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }
