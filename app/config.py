"""Configuration settings for the application."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application settings
    app_name: str = "OSS Health Monitor"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Database settings
    database_url: str = "postgresql://postgres:postgres@localhost:5432/oss_health_monitor"
    database_echo: bool = False

    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # GitHub settings
    github_token: str = ""  # GitHub personal access token for API access

    # Scanner settings
    osv_scanner_path: str = "osv-scanner"  # Path to osv-scanner binary

    # Cache settings
    scan_cache_ttl_hours: int = 12  # Cache scan results for 12 hours
    scan_cache_max_size: int = 1000  # Maximum number of cached scan results


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
