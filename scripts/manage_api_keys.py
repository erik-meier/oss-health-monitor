"""Script to create and manage API keys."""

import secrets
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, "/home/erik/personal/oss-health-monitor")

from app.database import SessionLocal
from app.models.auth import APIKey
from app.middleware.auth import hash_api_key


def create_api_key(name: str, expires_days: int = None):
    """
    Create a new API key.
    
    Args:
        name: Human-readable name for the key
        expires_days: Optional expiration in days
    """
    # Generate random API key
    api_key = secrets.token_urlsafe(32)
    
    # Calculate expiration date
    expires_at = None
    if expires_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
    
    # Create database record
    db = SessionLocal()
    try:
        db_key = APIKey(
            key_hash=hash_api_key(api_key),
            name=name,
            enabled=True,
            expires_at=expires_at,
        )
        db.add(db_key)
        db.commit()
        db.refresh(db_key)
        
        print("=" * 60)
        print("API Key Created Successfully!")
        print("=" * 60)
        print(f"Name: {name}")
        print(f"API Key: {api_key}")
        print(f"Key ID: {db_key.id}")
        print(f"Created: {db_key.created_at}")
        if expires_at:
            print(f"Expires: {expires_at}")
        print("=" * 60)
        print("\n⚠️  IMPORTANT: Save this API key securely!")
        print("This is the only time it will be displayed.\n")
        print("Use it in API requests:")
        print(f'Authorization: Bearer {api_key}')
        print("=" * 60)
        
    finally:
        db.close()


def list_api_keys():
    """List all API keys (without showing the actual keys)."""
    db = SessionLocal()
    try:
        keys = db.query(APIKey).all()
        
        print("\n" + "=" * 80)
        print("API Keys")
        print("=" * 80)
        print(f"{'ID':<5} {'Name':<20} {'Enabled':<10} {'Created':<20} {'Expires':<20}")
        print("-" * 80)
        
        for key in keys:
            expires = key.expires_at.strftime("%Y-%m-%d") if key.expires_at else "Never"
            created = key.created_at.strftime("%Y-%m-%d %H:%M")
            enabled = "Yes" if key.enabled else "No"
            
            print(f"{key.id:<5} {key.name:<20} {enabled:<10} {created:<20} {expires:<20}")
        
        print("=" * 80 + "\n")
        
    finally:
        db.close()


def disable_api_key(key_id: int):
    """Disable an API key."""
    db = SessionLocal()
    try:
        key = db.query(APIKey).filter(APIKey.id == key_id).first()
        
        if not key:
            print(f"Error: API key with ID {key_id} not found")
            return
        
        key.enabled = False
        db.commit()
        
        print(f"API key '{key.name}' (ID: {key_id}) has been disabled")
        
    finally:
        db.close()


def enable_api_key(key_id: int):
    """Enable an API key."""
    db = SessionLocal()
    try:
        key = db.query(APIKey).filter(APIKey.id == key_id).first()
        
        if not key:
            print(f"Error: API key with ID {key_id} not found")
            return
        
        key.enabled = True
        db.commit()
        
        print(f"API key '{key.name}' (ID: {key_id}) has been enabled")
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage API keys")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new API key")
    create_parser.add_argument("name", help="Name for the API key")
    create_parser.add_argument("--expires", type=int, help="Expiration in days")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all API keys")
    
    # Disable command
    disable_parser = subparsers.add_parser("disable", help="Disable an API key")
    disable_parser.add_argument("id", type=int, help="API key ID")
    
    # Enable command
    enable_parser = subparsers.add_parser("enable", help="Enable an API key")
    enable_parser.add_argument("id", type=int, help="API key ID")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_api_key(args.name, args.expires)
    elif args.command == "list":
        list_api_keys()
    elif args.command == "disable":
        disable_api_key(args.id)
    elif args.command == "enable":
        enable_api_key(args.id)
    else:
        parser.print_help()
