"""Retailer schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RetailerBase(BaseModel):
    """Base retailer schema."""

    name: str
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None


class RetailerCreate(RetailerBase):
    """Schema for creating a new retailer."""

    pass


class RetailerUpdate(BaseModel):
    """Schema for updating retailer data."""

    name: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RetailerResponse(RetailerBase):
    """Schema for retailer response data."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
