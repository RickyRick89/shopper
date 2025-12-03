"""Celery tasks for price scraping, history storage, and alert checking."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from celery import shared_task
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.price_history import PriceHistory
from app.models.product import Price, Product
from app.models.wishlist import WishlistItem
from celery_app.config import get_celery_settings

logger = logging.getLogger(__name__)

# Initialize database connection for Celery tasks
app_settings = get_settings()
celery_settings = get_celery_settings()

engine = create_engine(
    app_settings.database_url,
    connect_args={"check_same_thread": False}
    if app_settings.database_url.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session for Celery tasks."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scrape_product_prices(self, product_id: int) -> dict:
    """Scrape prices for a specific product from all retailers.

    Args:
        product_id: ID of the product to scrape prices for

    Returns:
        Dictionary with scraping results
    """
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            logger.warning(f"Product {product_id} not found")
            return {"status": "error", "message": "Product not found"}

        # Get current prices and store in history
        current_prices = db.query(Price).filter(Price.product_id == product_id).all()

        prices_stored = 0
        for price in current_prices:
            # Store price in history
            history_entry = PriceHistory(
                product_id=product_id,
                retailer=price.retailer,
                price=price.price,
                currency=price.currency,
            )
            db.add(history_entry)
            prices_stored += 1

        db.commit()

        logger.info(f"Stored {prices_stored} price entries for product {product_id}")
        return {
            "status": "success",
            "product_id": product_id,
            "prices_stored": prices_stored,
        }

    except Exception as exc:
        logger.error(f"Error scraping prices for product {product_id}: {exc}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def scrape_all_prices(self) -> dict:
    """Scrape prices for all products in the database.

    Returns:
        Dictionary with overall scraping results
    """
    db = SessionLocal()
    try:
        # Get all products that have prices
        products_with_prices = (
            db.query(Product.id)
            .join(Price)
            .distinct()
            .all()
        )

        product_ids = [p.id for p in products_with_prices]
        logger.info(f"Starting price scrape for {len(product_ids)} products")

        # Queue individual scrape tasks for each product
        for product_id in product_ids:
            scrape_product_prices.delay(product_id)

        return {
            "status": "success",
            "products_queued": len(product_ids),
        }

    except Exception as exc:
        logger.error(f"Error in scrape_all_prices: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def store_price_history(
    self, product_id: int, retailer: str, price: float, currency: str = "USD"
) -> dict:
    """Store a price history entry for a product.

    Args:
        product_id: ID of the product
        retailer: Name of the retailer
        price: Current price
        currency: Currency code (default: USD)

    Returns:
        Dictionary with storage result
    """
    db = SessionLocal()
    try:
        history_entry = PriceHistory(
            product_id=product_id,
            retailer=retailer,
            price=price,
            currency=currency,
        )
        db.add(history_entry)
        db.commit()

        logger.info(
            f"Stored price history: product={product_id}, "
            f"retailer={retailer}, price={price}"
        )

        return {
            "status": "success",
            "id": history_entry.id,
            "product_id": product_id,
            "retailer": retailer,
            "price": price,
        }

    except Exception as exc:
        logger.error(f"Error storing price history: {exc}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_price_alerts(self) -> dict:
    """Check all wishlist items for price alerts.

    Compares current prices against target prices and logs alerts.

    Returns:
        Dictionary with alert check results
    """
    db = SessionLocal()
    try:
        # Get all wishlist items with target prices
        wishlist_items = (
            db.query(WishlistItem)
            .filter(WishlistItem.target_price.isnot(None))
            .all()
        )

        alerts_triggered = 0
        items_checked = 0

        for item in wishlist_items:
            items_checked += 1

            # Get the lowest current price for this product
            lowest_price = (
                db.query(func.min(Price.price))
                .filter(Price.product_id == item.product_id)
                .scalar()
            )

            if lowest_price is not None and lowest_price <= item.target_price:
                alerts_triggered += 1
                logger.info(
                    f"Price alert triggered: user={item.user_id}, "
                    f"product={item.product_id}, "
                    f"target={item.target_price}, current={lowest_price}"
                )
                # In a real implementation, this would trigger a notification
                # (email, push notification, etc.)

        logger.info(
            f"Price alert check complete: {items_checked} items checked, "
            f"{alerts_triggered} alerts triggered"
        )

        return {
            "status": "success",
            "items_checked": items_checked,
            "alerts_triggered": alerts_triggered,
        }

    except Exception as exc:
        logger.error(f"Error checking price alerts: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def check_single_product_alert(self, product_id: int) -> dict:
    """Check price alerts for a specific product.

    Args:
        product_id: ID of the product to check alerts for

    Returns:
        Dictionary with alert check results
    """
    db = SessionLocal()
    try:
        # Get wishlist items for this product with target prices
        wishlist_items = (
            db.query(WishlistItem)
            .filter(
                WishlistItem.product_id == product_id,
                WishlistItem.target_price.isnot(None),
            )
            .all()
        )

        if not wishlist_items:
            return {"status": "success", "alerts_triggered": 0}

        # Get the lowest current price
        lowest_price = (
            db.query(func.min(Price.price))
            .filter(Price.product_id == product_id)
            .scalar()
        )

        alerts_triggered = 0
        for item in wishlist_items:
            if lowest_price is not None and lowest_price <= item.target_price:
                alerts_triggered += 1
                logger.info(
                    f"Price alert: user={item.user_id}, product={product_id}, "
                    f"target={item.target_price}, current={lowest_price}"
                )

        return {
            "status": "success",
            "product_id": product_id,
            "alerts_triggered": alerts_triggered,
        }

    except Exception as exc:
        logger.error(f"Error checking alerts for product {product_id}: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task(bind=True, max_retries=1)
def cleanup_old_price_history(self) -> dict:
    """Clean up old price history entries beyond retention period.

    Returns:
        Dictionary with cleanup results
    """
    db = SessionLocal()
    try:
        retention_days = celery_settings.price_history_retention_days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

        # Delete old entries
        deleted_count = (
            db.query(PriceHistory)
            .filter(PriceHistory.recorded_at < cutoff_date)
            .delete()
        )
        db.commit()

        logger.info(
            f"Price history cleanup: deleted {deleted_count} entries "
            f"older than {retention_days} days"
        )

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "retention_days": retention_days,
        }

    except Exception as exc:
        logger.error(f"Error cleaning up price history: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


@shared_task
def get_price_history_stats(
    product_id: int, retailer: Optional[str] = None, days: int = 30
) -> dict:
    """Get price history statistics for a product.

    Args:
        product_id: ID of the product
        retailer: Optional retailer filter
        days: Number of days to include in stats

    Returns:
        Dictionary with price statistics
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        query = db.query(PriceHistory).filter(
            PriceHistory.product_id == product_id,
            PriceHistory.recorded_at >= cutoff_date,
        )

        if retailer:
            query = query.filter(PriceHistory.retailer == retailer)

        history = query.order_by(PriceHistory.recorded_at.desc()).all()

        if not history:
            return {"status": "success", "data": None}

        prices = [h.price for h in history]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        current_price = prices[0] if prices else None

        # Calculate price change percentage
        if len(prices) >= 2:
            oldest_price = prices[-1]
            if oldest_price > 0:
                price_change_pct = ((current_price - oldest_price) / oldest_price) * 100
            else:
                price_change_pct = 0
        else:
            price_change_pct = 0

        return {
            "status": "success",
            "data": {
                "product_id": product_id,
                "retailer": retailer,
                "min_price": min_price,
                "max_price": max_price,
                "avg_price": round(avg_price, 2),
                "current_price": current_price,
                "price_change_pct": round(price_change_pct, 2),
                "data_points": len(prices),
                "days": days,
            },
        }

    except Exception as exc:
        logger.error(f"Error getting price history stats: {exc}")
        return {"status": "error", "message": str(exc)}
    finally:
        db.close()
