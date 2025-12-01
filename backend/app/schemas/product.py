"""Product schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PriceBase(BaseModel):
    """Base price schema."""

    retailer: str
    price: float
    currency: str = "USD"
    url: Optional[str] = None
    in_stock: bool = True


class PriceCreate(PriceBase):
    """Schema for creating a new price entry."""

    product_id: int


class PriceResponse(PriceBase):
    """Schema for price response data."""

    id: int
    product_id: int
    scraped_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    """Base product schema."""

    name: str
    description: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema for creating a new product."""

    pass


class ProductUpdate(BaseModel):
    """Schema for updating product data."""

    name: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None


class ProductResponse(ProductBase):
    """Schema for product response data."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductWithPrices(ProductResponse):
    """Schema for product with price data."""

    prices: List[PriceResponse] = []


class ProductSearchQuery(BaseModel):
    """Schema for product search parameters."""

    query: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    brand: Optional[str] = None
    retailer: Optional[str] = None
    page: int = 1
    limit: int = 20
