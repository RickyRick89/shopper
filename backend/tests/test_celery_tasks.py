"""Tests for Celery tasks."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


class TestCeleryConfig:
    """Tests for Celery configuration."""

    def test_default_settings(self):
        """Test default Celery settings."""
        from celery_app.config import CelerySettings

        settings = CelerySettings()
        assert settings.broker_url == "redis://localhost:6379/0"
        assert settings.result_backend == "redis://localhost:6379/0"
        assert settings.task_serializer == "json"
        assert settings.timezone == "UTC"
        assert settings.price_scrape_interval == 3600
        assert settings.alert_check_interval == 300
        assert settings.price_history_retention_days == 365

    def test_custom_settings(self):
        """Test custom Celery settings."""
        from celery_app.config import CelerySettings

        settings = CelerySettings(
            broker_url="redis://custom:6379/1",
            price_scrape_interval=7200,
        )
        assert settings.broker_url == "redis://custom:6379/1"
        assert settings.price_scrape_interval == 7200


class TestCeleryApp:
    """Tests for Celery app configuration."""

    def test_celery_app_created(self):
        """Test Celery app is properly created."""
        from celery_app.celery import celery_app

        assert celery_app is not None
        assert celery_app.main == "shopper"

    def test_celery_beat_schedule_configured(self):
        """Test Celery beat schedule is configured."""
        from celery_app.celery import celery_app

        schedule = celery_app.conf.beat_schedule
        assert "scrape-prices-hourly" in schedule
        assert "check-price-alerts" in schedule
        assert "cleanup-price-history-daily" in schedule

    def test_celery_queues_configured(self):
        """Test Celery queues are configured."""
        from celery_app.celery import celery_app

        queues = celery_app.conf.task_queues
        assert "default" in queues
        assert "scraping" in queues
        assert "alerts" in queues
        assert "maintenance" in queues


class TestCeleryTasks:
    """Tests for Celery task functions."""

    @patch("celery_app.tasks.SessionLocal")
    def test_store_price_history(self, mock_session):
        """Test storing price history entry."""
        from celery_app.tasks import store_price_history

        # Create mock session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock the commit to set id on the history entry
        def set_id(entry=None):
            if hasattr(mock_db, '_added_entry'):
                mock_db._added_entry.id = 1

        mock_db.commit.side_effect = set_id

        def track_add(entry):
            mock_db._added_entry = entry
            entry.id = 1

        mock_db.add.side_effect = track_add

        result = store_price_history(
            product_id=1, retailer="Amazon", price=99.99, currency="USD"
        )

        assert result["status"] == "success"
        assert result["product_id"] == 1
        assert result["retailer"] == "Amazon"
        assert result["price"] == 99.99
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch("celery_app.tasks.SessionLocal")
    def test_scrape_product_prices_not_found(self, mock_session):
        """Test scraping prices for nonexistent product."""
        from celery_app.tasks import scrape_product_prices

        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = scrape_product_prices(product_id=99999)

        assert result["status"] == "error"
        assert result["message"] == "Product not found"

    @patch("celery_app.tasks.SessionLocal")
    def test_check_price_alerts_no_items(self, mock_session):
        """Test checking alerts when no wishlist items exist."""
        from celery_app.tasks import check_price_alerts

        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = check_price_alerts()

        assert result["status"] == "success"
        assert result["items_checked"] == 0
        assert result["alerts_triggered"] == 0

    @patch("celery_app.tasks.SessionLocal")
    def test_cleanup_old_price_history(self, mock_session):
        """Test cleaning up old price history."""
        from celery_app.tasks import cleanup_old_price_history

        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.delete.return_value = 10

        result = cleanup_old_price_history()

        assert result["status"] == "success"
        assert result["deleted_count"] == 10
        mock_db.commit.assert_called_once()

    @patch("celery_app.tasks.SessionLocal")
    def test_get_price_history_stats_no_data(self, mock_session):
        """Test getting price history stats with no data."""
        from celery_app.tasks import get_price_history_stats

        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Create a mock that returns itself for chained calls
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query  # filter returns self
        mock_query.order_by.return_value = mock_query  # order_by returns self
        mock_query.all.return_value = []  # final result is empty

        result = get_price_history_stats(product_id=1, days=30)

        assert result["status"] == "success"
        assert result["data"] is None

    @patch("celery_app.tasks.SessionLocal")
    def test_get_price_history_stats_with_data(self, mock_session):
        """Test getting price history stats with data."""
        from celery_app.tasks import get_price_history_stats

        # Create mock history entries
        mock_entry1 = MagicMock()
        mock_entry1.price = 100.0
        mock_entry2 = MagicMock()
        mock_entry2.price = 120.0
        mock_entry3 = MagicMock()
        mock_entry3.price = 90.0

        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Create a mock that returns itself for chained calls
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query  # filter returns self
        mock_query.order_by.return_value = mock_query  # order_by returns self
        mock_query.all.return_value = [mock_entry1, mock_entry2, mock_entry3]

        result = get_price_history_stats(product_id=1, days=30)

        assert result["status"] == "success"
        assert result["data"]["min_price"] == 90.0
        assert result["data"]["max_price"] == 120.0
        assert result["data"]["avg_price"] == 103.33
        assert result["data"]["data_points"] == 3
