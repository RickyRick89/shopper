"""Wishlist schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.product import ProductResponse


class WishlistItemBase(BaseModel):
    """Base wishlist item schema."""

    product_id: int
    target_price: Optional[float] = None


class WishlistItemCreate(WishlistItemBase):
    """Schema for creating a new wishlist item."""

    pass


class WishlistItemUpdate(BaseModel):
    """Schema for updating wishlist item data."""

    target_price: Optional[float] = None


class WishlistItemResponse(WishlistItemBase):
    """Schema for wishlist item response data."""

    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WishlistItemWithProduct(WishlistItemResponse):
    """Schema for wishlist item with product details."""

    product: ProductResponse
