"""Tests for application configuration."""

from app.config import Settings, get_settings


def test_default_settings():
    """Test default settings."""
    settings = Settings()
    assert settings.app_name == "OSS Health Monitor"
    assert settings.app_version == "0.1.0"
    assert settings.debug is False
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000


def test_get_settings_cached():
    """Test that settings are cached."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2
