"""Price history routes for retrieving and analyzing price trends."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.database import get_db
from app.models.price_history import PriceHistory
from app.models.product import Price, Product
from app.models.user import User
from app.schemas.price_history import (
    PriceHistoryChartData,
    PriceHistoryChartResponse,
    PriceHistoryResponse,
    PriceHistoryStats,
)

router = APIRouter(prefix="/price-history", tags=["price-history"])


@router.get(
    "/product/{product_id}",
    response_model=List[PriceHistoryResponse],
)
def get_product_price_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days of history to retrieve"),
    retailer: Optional[str] = Query(None, description="Filter by specific retailer"),
    db: Session = Depends(get_db),
):
    """Get price history for a specific product.
    
    Args:
        product_id: ID of the product
        days: Number of days of history to retrieve (default: 30)
        retailer: Optional retailer filter
    
    Returns:
        List of price history entries
    """
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    query = db.query(PriceHistory).filter(
        and_(
            PriceHistory.product_id == product_id,
            PriceHistory.recorded_at >= cutoff_date,
        )
    )

    if retailer:
        query = query.filter(PriceHistory.retailer == retailer)

    history = query.order_by(desc(PriceHistory.recorded_at)).all()

    return history


@router.get(
    "/product/{product_id}/chart",
    response_model=PriceHistoryChartResponse,
)
def get_price_history_chart_data(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    db: Session = Depends(get_db),
):
    """Get price history data formatted for charts.
    
    Args:
        product_id: ID of the product
        days: Number of days of history
    
    Returns:
        Chart data with timestamps and prices grouped by retailer
    """
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Get all price history for the product
    history = (
        db.query(PriceHistory)
        .filter(
            and_(
                PriceHistory.product_id == product_id,
                PriceHistory.recorded_at >= cutoff_date,
            )
        )
        .order_by(PriceHistory.recorded_at)
        .all()
    )

    # Group by retailer and create chart data
    retailers_data = {}
    for entry in history:
        if entry.retailer not in retailers_data:
            retailers_data[entry.retailer] = []

        retailers_data[entry.retailer].append(
            PriceHistoryChartData(
                timestamp=entry.recorded_at,
                price=entry.price,
            )
        )

    return PriceHistoryChartResponse(
        product_id=product_id,
        product_name=product.name,
        data_by_retailer=retailers_data,
    )


@router.get(
    "/product/{product_id}/stats",
    response_model=PriceHistoryStats,
)
def get_price_history_stats(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    db: Session = Depends(get_db),
):
    """Get price statistics for a product over a period.
    
    Args:
        product_id: ID of the product
        days: Number of days to analyze
    
    Returns:
        Price statistics including min, max, average, and trends
    """
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Get statistics
    stats = db.query(
        func.min(PriceHistory.price).label("min_price"),
        func.max(PriceHistory.price).label("max_price"),
        func.avg(PriceHistory.price).label("avg_price"),
        func.count(PriceHistory.id).label("total_records"),
    ).filter(
        and_(
            PriceHistory.product_id == product_id,
            PriceHistory.recorded_at >= cutoff_date,
        )
    ).first()

    if not stats or stats.total_records == 0:
        return PriceHistoryStats(
            product_id=product_id,
            min_price=None,
            max_price=None,
            avg_price=None,
            price_change=None,
            trend="stable",
            total_records=0,
        )

    # Get first and last prices to calculate trend
    first_entry = (
        db.query(PriceHistory)
        .filter(
            and_(
                PriceHistory.product_id == product_id,
                PriceHistory.recorded_at >= cutoff_date,
            )
        )
        .order_by(PriceHistory.recorded_at.asc())
        .first()
    )

    last_entry = (
        db.query(PriceHistory)
        .filter(
            and_(
                PriceHistory.product_id == product_id,
                PriceHistory.recorded_at >= cutoff_date,
            )
        )
        .order_by(PriceHistory.recorded_at.desc())
        .first()
    )

    price_change = None
    trend = "stable"
    if first_entry and last_entry:
        price_change = last_entry.price - first_entry.price
        if price_change > 0:
            trend = "increasing"
        elif price_change < 0:
            trend = "decreasing"

    return PriceHistoryStats(
        product_id=product_id,
        min_price=float(stats.min_price) if stats.min_price else None,
        max_price=float(stats.max_price) if stats.max_price else None,
        avg_price=float(stats.avg_price) if stats.avg_price else None,
        price_change=price_change,
        trend=trend,
        total_records=stats.total_records,
    )


@router.get(
    "/wishlist/{wishlist_item_id}",
    response_model=List[PriceHistoryResponse],
)
def get_wishlist_item_price_history(
    wishlist_item_id: int,
    current_user: User = Depends(get_current_active_user),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get price history for a wishlist item.
    
    Args:
        wishlist_item_id: ID of the wishlist item
        current_user: Current authenticated user
        days: Number of days of history
    
    Returns:
        Price history for the product in the wishlist
    """
    from app.models.wishlist import WishlistItem

    # Verify wishlist item exists and belongs to user
    wishlist_item = (
        db.query(WishlistItem)
        .filter(
            and_(
                WishlistItem.id == wishlist_item_id,
                WishlistItem.user_id == current_user.id,
            )
        )
        .first()
    )

    if not wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found",
        )

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    history = (
        db.query(PriceHistory)
        .filter(
            and_(
                PriceHistory.product_id == wishlist_item.product_id,
                PriceHistory.recorded_at >= cutoff_date,
            )
        )
        .order_by(desc(PriceHistory.recorded_at))
        .all()
    )

    return history
