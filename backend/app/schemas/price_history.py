"""Price history schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PriceHistoryBase(BaseModel):
    """Base price history schema."""

    retailer: str
    price: float
    currency: str = "USD"


class PriceHistoryCreate(PriceHistoryBase):
    """Schema for creating a new price history entry."""

    product_id: int


class PriceHistoryResponse(PriceHistoryBase):
    """Schema for price history response data."""

    id: int
    product_id: int
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceHistoryList(BaseModel):
    """Schema for paginated price history response."""

    items: List[PriceHistoryResponse]
    total: int
    page: int
    limit: int


class PriceHistoryStats(BaseModel):
    """Schema for price history statistics."""

    product_id: int
    retailer: Optional[str] = None
    min_price: float
    max_price: float
    avg_price: float
    current_price: Optional[float] = None
    price_change_pct: Optional[float] = None
    start_date: datetime
    end_date: datetime


class PriceHistoryChartData(BaseModel):
    """Schema for price history chart data points."""

    date: datetime
    price: float
    retailer: str


class PriceHistoryChartResponse(BaseModel):
    """Schema for price history chart response."""

    product_id: int
    product_name: str
    data: List[PriceHistoryChartData]
    stats: PriceHistoryStats
