"""Search routes for finding products and deals."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.product import Price, Product
from app.schemas.product import ProductCreate, ProductResponse, ProductWithPrices
from app.services import search as search_service
from app.services.product import add_product_price, create_product

router = APIRouter(prefix="/search", tags=["search"])


# Lightweight demo data used when a search returns no rows so the UI shows example results.
DEMO_RESULTS = {
    "saxophone": [
        {
            "product": ProductCreate(
                name="Yamaha YAS-280 Alto Saxophone",
                brand="Yamaha",
                category="Instruments",
                description="Student alto sax with case and mouthpiece.",
            ),
            "prices": [
                {"retailer": "Sweetwater", "price": 1299.99, "url": "https://example.com/yas-280-sw"},
                {"retailer": "Guitar Center", "price": 1199.99, "url": "https://example.com/yas-280-gc"},
            ],
        }
    ],
    "guitar": [
        {
            "product": ProductCreate(
                name="Fender Player Stratocaster",
                brand="Fender",
                category="Electric Guitars",
                description="Aldrich body, maple neck, classic single-coil tone.",
            ),
            "prices": [
                {"retailer": "Sweetwater", "price": 799.99, "url": "https://example.com/strat-sw"},
                {"retailer": "Guitar Center", "price": 749.99, "url": "https://example.com/strat-gc"},
            ],
        }
    ],
    "laptop": [
        {
            "product": ProductCreate(
                name="Dell XPS 13",
                brand="Dell",
                category="Computers",
                description="13-inch ultrabook with Intel Evo platform.",
            ),
            "prices": [
                {"retailer": "Amazon", "price": 1199.00, "url": "https://example.com/xps13-amz"},
                {"retailer": "Best Buy", "price": 1149.00, "url": "https://example.com/xps13-bb"},
            ],
        }
    ],
    "shoes": [
        {
            "product": ProductCreate(
                name="Nike Air Zoom Pegasus",
                brand="Nike",
                category="Footwear",
                description="Daily training running shoes with responsive cushioning.",
            ),
            "prices": [
                {"retailer": "Nike", "price": 129.99, "url": "https://example.com/pegasus"},
                {"retailer": "Foot Locker", "price": 119.99, "url": "https://example.com/pegasus-fl"},
            ],
        }
    ],
}


def _maybe_seed_demo_results(db: Session, query_text: str) -> None:
    """When a search yields no rows, insert a small demo set for the query keyword."""

    normalized = (query_text or "").lower()
    for keyword, entries in DEMO_RESULTS.items():
        if keyword in normalized:
            for entry in entries:
                # Skip if product already exists
                exists = db.query(Product).filter(Product.name == entry["product"].name).first()
                if exists:
                    continue

                product = create_product(db, entry["product"])
                for price in entry.get("prices", []):
                    add_product_price(
                        db,
                        product_id=product.id,
                        retailer=price["retailer"],
                        price=price["price"],
                        url=price.get("url"),
                        in_stock=True,
                    )
            break


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

    # If no results, seed a small demo set for this query and retry once
    if not products and q:
        _maybe_seed_demo_results(db, q)
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
    products_query = db.query(Product).join(Price).filter(Price.in_stock.is_(True))

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
    return search_service.get_search_suggestions(db, q, limit)


@router.get("/location", response_model=List[ProductResponse])
def search_products_by_location(
    zip_code: Optional[str] = Query(None, description="US zip code for location"),
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="Latitude"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="Longitude"),
    radius: float = Query(25.0, ge=1, le=500, description="Search radius in miles"),
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Search products with location-based filtering."""
    return search_service.search_products_by_location(
        db=db,
        zip_code=zip_code,
        latitude=latitude,
        longitude=longitude,
        radius_miles=radius,
        query=q,
        category=category,
        page=page,
        limit=limit,
    )


@router.get("/coordinates")
def get_coordinates_from_zip(
    zip_code: str = Query(..., min_length=5, max_length=5, description="US 5-digit zip code"),
):
    """Convert a zip code to latitude/longitude coordinates."""
    coords = search_service.zip_to_coordinates(zip_code)
    if coords:
        return {"zip_code": zip_code, "latitude": coords[0], "longitude": coords[1]}
    return {"zip_code": zip_code, "latitude": None, "longitude": None, "message": "Zip code not found"}
