"""Pydantic schemas for request/response validation."""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    Token,
    TokenData,
    LoginRequest,
)
from app.schemas.product import (
    ProductBase,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductWithPrices,
    ProductSearchQuery,
    PriceBase,
    PriceCreate,
    PriceResponse,
)
from app.schemas.wishlist import (
    WishlistItemBase,
    WishlistItemCreate,
    WishlistItemUpdate,
    WishlistItemResponse,
    WishlistItemWithProduct,
)

__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "Token",
    "TokenData",
    "LoginRequest",
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductWithPrices",
    "ProductSearchQuery",
    "PriceBase",
    "PriceCreate",
    "PriceResponse",
    "WishlistItemBase",
    "WishlistItemCreate",
    "WishlistItemUpdate",
    "WishlistItemResponse",
    "WishlistItemWithProduct",
]
