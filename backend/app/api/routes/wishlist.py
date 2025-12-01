"""Wishlist routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.database import get_db
from app.models.product import Product
from app.models.user import User
from app.models.wishlist import WishlistItem
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
