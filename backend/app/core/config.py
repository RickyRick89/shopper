"""Application configuration settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = "Shopper API"
    app_version: str = "0.1.0"
    debug: bool = False

    # API
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "sqlite:///./shopper.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
