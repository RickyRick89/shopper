"""Product database model."""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class Product(Base):
    """Product model for storing product information."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    brand = Column(String, nullable=True)
    category = Column(String, index=True, nullable=True)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    prices = relationship("Price", back_populates="product")
    wishlist_items = relationship("WishlistItem", back_populates="product")


class Price(Base):
    """Price model for tracking product prices at different retailers."""

    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    retailer = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    url = Column(String, nullable=True)
    in_stock = Column(Integer, default=1)  # 1 = in stock, 0 = out of stock
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    product = relationship("Product", back_populates="prices")
