"""User schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """Base user schema with common attributes."""

    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str


class UserUpdate(BaseModel):
    """Schema for updating user data."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response data."""

    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for token payload data."""

    email: Optional[str] = None
    user_id: Optional[int] = None


class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str
