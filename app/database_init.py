"""Database initialization utilities."""

import logging
from sqlalchemy import inspect

from app.database import Base, engine
from app.models import APIKey, RepositoryConfig, RepositoryScan, ScanMetrics, ScanVulnerability  # noqa: F401

logger = logging.getLogger(__name__)


def init_database() -> None:
    """Initialize database by creating all tables if they don't exist."""
    try:
        # Check if tables already exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if existing_tables:
            logger.info(f"Database already initialized with tables: {existing_tables}")
            return
        
        logger.info("Initializing database tables...")
        
        # All models are imported above to ensure they're registered with Base
        # This ensures SQLAlchemy knows about all tables when creating schema
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        inspector = inspect(engine)
        created_tables = inspector.get_table_names()
        
        logger.info("✅ Database tables created successfully!")
        for table_name in created_tables:
            logger.info(f"  - {table_name}")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise


def check_database_health() -> bool:
    """Check if database is accessible and has required tables."""
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        
        # Required tables for the application to function
        required_tables = {
            "api_keys",
            "repository_scans",
            "scan_vulnerabilities",
            "scan_metrics",
            "repository_configs"
        }

        missing_tables = required_tables - existing_tables

        if missing_tables:
            logger.warning(f"Missing required tables: {missing_tables}")
            return False

        logger.info("Database health check passed")
        return True

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False