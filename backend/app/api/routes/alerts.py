"""Price alerts routes for managing user price alerts."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.models.wishlist import WishlistItem
from app.schemas.wishlist import (
    WishlistItemResponse,
    WishlistItemUpdate,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=List[WishlistItemResponse])
def get_price_alerts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all active price alerts for the current user.
    
    Returns only wishlist items that have a target price set.
    
    Returns:
        List of wishlist items with active price alerts
    """
    alerts = (
        db.query(WishlistItem)
        .filter(
            and_(
                WishlistItem.user_id == current_user.id,
                WishlistItem.target_price.isnot(None),
            )
        )
        .all()
    )
    return alerts


@router.post("/{wishlist_item_id}/set", response_model=WishlistItemResponse)
def set_price_alert(
    wishlist_item_id: int,
    target_price: float = Query(..., gt=0, description="Target price for the alert"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Set or update a price alert for a wishlist item.
    
    Args:
        wishlist_item_id: ID of the wishlist item
        target_price: Target price below which to trigger alert
        current_user: Current authenticated user
    
    Returns:
        Updated wishlist item with new alert
    """
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

    # Update target price
    wishlist_item.target_price = target_price
    db.commit()
    db.refresh(wishlist_item)

    return wishlist_item


@router.delete("/{wishlist_item_id}/remove")
def remove_price_alert(
    wishlist_item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Remove a price alert from a wishlist item.
    
    Args:
        wishlist_item_id: ID of the wishlist item
        current_user: Current authenticated user
    
    Returns:
        Success message
    """
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

    # Remove alert
    wishlist_item.target_price = None
    db.commit()

    return {"message": "Price alert removed successfully"}


@router.get("/{wishlist_item_id}/status", response_model=dict)
def get_alert_status(
    wishlist_item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the current status of a price alert.
    
    Args:
        wishlist_item_id: ID of the wishlist item
        current_user: Current authenticated user
    
    Returns:
        Alert status including target price and current lowest price
    """
    from app.models.product import Price

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

    if wishlist_item.target_price is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No price alert set for this item",
        )

    # Get lowest current price
    lowest_price_record = (
        db.query(Price)
        .filter(Price.product_id == wishlist_item.product_id)
        .order_by(Price.price.asc())
        .first()
    )

    lowest_price = lowest_price_record.price if lowest_price_record else None

    # Determine if alert is triggered
    alert_triggered = (
        lowest_price is not None and lowest_price <= wishlist_item.target_price
    )

    return {
        "wishlist_item_id": wishlist_item_id,
        "target_price": wishlist_item.target_price,
        "current_lowest_price": lowest_price,
        "alert_triggered": alert_triggered,
        "savings": (
            wishlist_item.target_price - lowest_price
            if lowest_price is not None
            else None
        ),
    }
