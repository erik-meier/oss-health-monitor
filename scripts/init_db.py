#!/usr/bin/env python3
"""
DEPRECATED: Initialize database schema by creating all tables.

This script is deprecated. The application now automatically initializes
the database on startup. Use this script only if you have disabled
automatic initialization with AUTO_INIT_DB=false.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import models to register them with Base (they need to be imported)
from app.database import Base, engine  # noqa: E402
from app.models import APIKey, RepositoryConfig, RepositoryScan, ScanMetrics, ScanVulnerability  # noqa: E402,F401


def init_db():
    """Create all database tables."""
    print("Creating database tables...")
    
    # All models are imported above to ensure they're registered with Base
    # This ensures SQLAlchemy knows about all tables when creating schema
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database tables created successfully!")
    print("\nCreated tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")


if __name__ == "__main__":
    init_db()