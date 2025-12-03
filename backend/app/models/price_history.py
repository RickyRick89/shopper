"""Price history database model for tracking price changes over time."""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class PriceHistory(Base):
    """Price history model for storing historical price data."""

    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    retailer = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    recorded_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    # Relationships
    product = relationship("Product", back_populates="price_history")
