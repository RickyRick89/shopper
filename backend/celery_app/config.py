"""Celery configuration settings."""

from typing import List

from pydantic_settings import BaseSettings
from functools import lru_cache


class CelerySettings(BaseSettings):
    """Celery configuration with environment variable support."""

    # Broker settings (Redis)
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/0"

    # Task settings
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: List[str] = ["json"]
    timezone: str = "UTC"
    enable_utc: bool = True

    # Task execution settings
    task_acks_late: bool = True
    task_reject_on_worker_lost: bool = True
    worker_prefetch_multiplier: int = 1

    # Schedule settings (in seconds)
    price_scrape_interval: int = 3600  # 1 hour
    alert_check_interval: int = 300  # 5 minutes
    price_history_cleanup_interval: int = 86400  # 24 hours

    # Price history settings
    price_history_retention_days: int = 365  # Keep 1 year of history

    class Config:
        env_prefix = "CELERY_"
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_celery_settings() -> CelerySettings:
    """Get cached Celery settings instance."""
    return CelerySettings()
