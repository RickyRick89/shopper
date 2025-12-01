"""Wishlist database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.database import Base


class WishlistItem(Base):
    """Wishlist item model for user's saved products."""

    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    target_price = Column(Float, nullable=True)  # User's target price for alerts
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="wishlists")
    product = relationship("Product", back_populates="wishlist_items")
