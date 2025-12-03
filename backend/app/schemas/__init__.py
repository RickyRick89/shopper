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
from app.schemas.retailer import (
    RetailerBase,
    RetailerCreate,
    RetailerUpdate,
    RetailerResponse,
)
from app.schemas.wishlist import (
    WishlistItemBase,
    WishlistItemCreate,
    WishlistItemUpdate,
    WishlistItemResponse,
    WishlistItemWithProduct,
)
from app.schemas.price_history import (
    PriceHistoryBase,
    PriceHistoryCreate,
    PriceHistoryResponse,
    PriceHistoryList,
    PriceHistoryStats,
    PriceHistoryChartData,
    PriceHistoryChartResponse,
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
    "RetailerBase",
    "RetailerCreate",
    "RetailerUpdate",
    "RetailerResponse",
    "WishlistItemBase",
    "WishlistItemCreate",
    "WishlistItemUpdate",
    "WishlistItemResponse",
    "WishlistItemWithProduct",
    "PriceHistoryBase",
    "PriceHistoryCreate",
    "PriceHistoryResponse",
    "PriceHistoryList",
    "PriceHistoryStats",
    "PriceHistoryChartData",
    "PriceHistoryChartResponse",
]
