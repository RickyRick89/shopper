"""Search routes for finding products and deals."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.product import Price, Product
from app.schemas.product import ProductResponse, ProductWithPrices

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/products", response_model=List[ProductResponse])
def search_products(
    q: Optional[str] = Query(None, description="Search query for product name or description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    retailer: Optional[str] = Query(None, description="Filter by retailer"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Search and filter products with various criteria."""
    products_query = db.query(Product)

    # Text search on name and description
    if q:
        search_pattern = f"%{q}%"
        products_query = products_query.filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern),
                Product.brand.ilike(search_pattern),
            )
        )

    # Filter by category
    if category:
        products_query = products_query.filter(Product.category.ilike(f"%{category}%"))

    # Filter by brand
    if brand:
        products_query = products_query.filter(Product.brand.ilike(f"%{brand}%"))

    # Filter by price range and retailer (requires joining with prices table)
    if min_price is not None or max_price is not None or retailer or in_stock is not None:
        products_query = products_query.join(Price)

        if min_price is not None:
            products_query = products_query.filter(Price.price >= min_price)

        if max_price is not None:
            products_query = products_query.filter(Price.price <= max_price)

        if retailer:
            products_query = products_query.filter(Price.retailer.ilike(f"%{retailer}%"))

        if in_stock is not None:
            products_query = products_query.filter(Price.in_stock == in_stock)

        # Remove duplicates from join
        products_query = products_query.distinct()

    # Pagination
    offset = (page - 1) * limit
    products = products_query.offset(offset).limit(limit).all()

    return products


@router.get("/deals", response_model=List[ProductWithPrices])
def search_deals(
    category: Optional[str] = Query(None, description="Filter by category"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Find products with the best deals (lowest prices, in stock)."""
    products_query = db.query(Product).join(Price).filter(Price.in_stock == True)

    if category:
        products_query = products_query.filter(Product.category.ilike(f"%{category}%"))

    if max_price is not None:
        products_query = products_query.filter(Price.price <= max_price)

    # Order by lowest price
    products_query = products_query.order_by(Price.price.asc()).distinct()

    # Pagination
    offset = (page - 1) * limit
    products = products_query.offset(offset).limit(limit).all()

    return products


@router.get("/suggestions", response_model=List[str])
def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Partial search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum suggestions"),
    db: Session = Depends(get_db),
):
    """Get search suggestions based on product names."""
    search_pattern = f"%{q}%"

    # Get matching product names
    products = (
        db.query(Product.name)
        .filter(Product.name.ilike(search_pattern))
        .distinct()
        .limit(limit)
        .all()
    )

    return [product.name for product in products]
