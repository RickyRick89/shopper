"""Wishlist routes."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.database import get_db
from app.models.price_history import PriceHistory
from app.models.product import Price, Product
from app.models.user import User
from app.models.wishlist import WishlistItem
from app.schemas.price_history import (
    PriceHistoryChartData,
    PriceHistoryChartResponse,
    PriceHistoryResponse,
    PriceHistoryStats,
)
from app.schemas.wishlist import (
    WishlistItemCreate,
    WishlistItemResponse,
    WishlistItemUpdate,
    WishlistItemWithProduct,
)

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.get("", response_model=List[WishlistItemWithProduct])
def get_wishlist(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get current user's wishlist."""
    wishlist_items = (
        db.query(WishlistItem).filter(WishlistItem.user_id == current_user.id).all()
    )
    return wishlist_items


@router.post("", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_wishlist(
    item_data: WishlistItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add a product to the wishlist."""
    # Check if product exists
    product = db.query(Product).filter(Product.id == item_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Check if already in wishlist
    existing = (
        db.query(WishlistItem)
        .filter(
            WishlistItem.user_id == current_user.id,
            WishlistItem.product_id == item_data.product_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product already in wishlist",
        )

    wishlist_item = WishlistItem(
        user_id=current_user.id,
        product_id=item_data.product_id,
        target_price=item_data.target_price,
    )
    db.add(wishlist_item)
    db.commit()
    db.refresh(wishlist_item)

    return wishlist_item


@router.put("/{item_id}", response_model=WishlistItemResponse)
def update_wishlist_item(
    item_id: int,
    item_update: WishlistItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a wishlist item (e.g., target price)."""
    item = (
        db.query(WishlistItem)
        .filter(WishlistItem.id == item_id, WishlistItem.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found",
        )

    if item_update.target_price is not None:
        item.target_price = item_update.target_price

    db.commit()
    db.refresh(item)

    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_wishlist(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Remove a product from the wishlist."""
    item = (
        db.query(WishlistItem)
        .filter(WishlistItem.id == item_id, WishlistItem.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found",
        )

    db.delete(item)
    db.commit()


@router.get(
    "/{item_id}/price-history", response_model=PriceHistoryChartResponse
)
def get_wishlist_item_price_history(
    item_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    retailer: Optional[str] = Query(None, description="Filter by retailer"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get price history for a wishlist item's product.

    Returns historical price data and statistics for charting.
    """
    # Get wishlist item
    item = (
        db.query(WishlistItem)
        .filter(WishlistItem.id == item_id, WishlistItem.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found",
        )

    # Get product
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    # Query price history
    query = db.query(PriceHistory).filter(
        PriceHistory.product_id == item.product_id,
        PriceHistory.recorded_at >= start_date,
    )

    if retailer:
        query = query.filter(PriceHistory.retailer == retailer)

    history = query.order_by(PriceHistory.recorded_at.asc()).all()

    # Build chart data
    chart_data = [
        PriceHistoryChartData(
            date=h.recorded_at,
            price=h.price,
            retailer=h.retailer,
        )
        for h in history
    ]

    # Calculate statistics
    if history:
        prices = [h.price for h in history]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        current_price = prices[-1] if prices else None

        # Calculate price change percentage
        if len(prices) >= 2:
            oldest_price = prices[0]
            if oldest_price > 0:
                price_change_pct = ((prices[-1] - oldest_price) / oldest_price) * 100
            else:
                price_change_pct = 0.0
        else:
            price_change_pct = 0.0

        stats = PriceHistoryStats(
            product_id=item.product_id,
            retailer=retailer,
            min_price=min_price,
            max_price=max_price,
            avg_price=round(avg_price, 2),
            current_price=current_price,
            price_change_pct=round(price_change_pct, 2),
            start_date=start_date,
            end_date=end_date,
        )
    else:
        # Return empty stats if no history
        stats = PriceHistoryStats(
            product_id=item.product_id,
            retailer=retailer,
            min_price=0.0,
            max_price=0.0,
            avg_price=0.0,
            current_price=None,
            price_change_pct=None,
            start_date=start_date,
            end_date=end_date,
        )

    return PriceHistoryChartResponse(
        product_id=item.product_id,
        product_name=product.name,
        data=chart_data,
        stats=stats,
    )


@router.get("/products/{product_id}/price-history", response_model=List[PriceHistoryResponse])
def get_product_price_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    retailer: Optional[str] = Query(None, description="Filter by retailer"),
    db: Session = Depends(get_db),
):
    """Get price history for a specific product.

    This endpoint is public and doesn't require authentication.
    """
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    # Query price history
    query = db.query(PriceHistory).filter(
        PriceHistory.product_id == product_id,
        PriceHistory.recorded_at >= start_date,
    )

    if retailer:
        query = query.filter(PriceHistory.retailer == retailer)

    history = query.order_by(PriceHistory.recorded_at.desc()).all()

    return history
