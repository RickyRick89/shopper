"""Product routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.product import Price, Product
from app.schemas.product import (
    PriceCreate,
    PriceResponse,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    ProductWithPrices,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=List[ProductResponse])
def list_products(
    query: Optional[str] = Query(None, description="Search query for product name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List and search products."""
    products_query = db.query(Product)

    # Apply filters
    if query:
        search_pattern = f"%{query}%"
        products_query = products_query.filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern),
            )
        )

    if category:
        products_query = products_query.filter(Product.category == category)

    if brand:
        products_query = products_query.filter(Product.brand == brand)

    # Pagination
    offset = (page - 1) * limit
    products = products_query.offset(offset).limit(limit).all()

    return products


@router.get("/{product_id}", response_model=ProductWithPrices)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a product by ID with its current prices."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product."""
    product = Product(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, product_update: ProductUpdate, db: Session = Depends(get_db)
):
    """Update a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    db.delete(product)
    db.commit()


@router.post(
    "/{product_id}/prices", response_model=PriceResponse, status_code=status.HTTP_201_CREATED
)
def add_price(product_id: int, price_data: PriceCreate, db: Session = Depends(get_db)):
    """Add a price entry for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    price = Price(
        product_id=product_id,
        retailer=price_data.retailer,
        price=price_data.price,
        currency=price_data.currency,
        url=price_data.url,
        in_stock=1 if price_data.in_stock else 0,
    )
    db.add(price)
    db.commit()
    db.refresh(price)
    return price


@router.get("/{product_id}/prices", response_model=List[PriceResponse])
def get_product_prices(product_id: int, db: Session = Depends(get_db)):
    """Get all prices for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product.prices
