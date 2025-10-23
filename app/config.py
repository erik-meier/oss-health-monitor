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


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
