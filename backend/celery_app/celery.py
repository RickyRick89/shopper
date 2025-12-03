"""Celery application instance and configuration."""

from celery import Celery
from celery.schedules import crontab

from celery_app.config import get_celery_settings

settings = get_celery_settings()

# Create Celery application
celery_app = Celery(
    "shopper",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=["celery_app.tasks"],
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.task_serializer,
    result_serializer=settings.result_serializer,
    accept_content=settings.accept_content,
    timezone=settings.timezone,
    enable_utc=settings.enable_utc,
    task_acks_late=settings.task_acks_late,
    task_reject_on_worker_lost=settings.task_reject_on_worker_lost,
    worker_prefetch_multiplier=settings.worker_prefetch_multiplier,
)

# Configure periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    "scrape-prices-hourly": {
        "task": "celery_app.tasks.scrape_all_prices",
        "schedule": settings.price_scrape_interval,
        "options": {"queue": "scraping"},
    },
    "check-price-alerts": {
        "task": "celery_app.tasks.check_price_alerts",
        "schedule": settings.alert_check_interval,
        "options": {"queue": "alerts"},
    },
    "cleanup-price-history-daily": {
        "task": "celery_app.tasks.cleanup_old_price_history",
        "schedule": crontab(hour=2, minute=0),  # Run at 2 AM UTC
        "options": {"queue": "maintenance"},
    },
}

# Define task queues
celery_app.conf.task_queues = {
    "default": {},
    "scraping": {},
    "alerts": {},
    "maintenance": {},
}

celery_app.conf.task_default_queue = "default"
