"""Search service for location-based filtering and product search."""

import math
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.product import Price, Product


# US Zip code to coordinates mapping (sample data)
# In production, this would use a geocoding API or database
ZIP_CODE_COORDS: Dict[str, Tuple[float, float]] = {
    "10001": (40.7484, -73.9967),  # New York, NY
    "90210": (34.0901, -118.4065),  # Beverly Hills, CA
    "60601": (41.8819, -87.6278),  # Chicago, IL
    "77001": (29.7604, -95.3698),  # Houston, TX
    "85001": (33.4484, -112.0740),  # Phoenix, AZ
    "19101": (39.9526, -75.1652),  # Philadelphia, PA
    "78201": (29.4241, -98.4936),  # San Antonio, TX
    "92101": (32.7157, -117.1611),  # San Diego, CA
    "75201": (32.7767, -96.7970),  # Dallas, TX
    "95101": (37.3382, -121.8863),  # San Jose, CA
    "32801": (28.5383, -81.3792),  # Orlando, FL
    "33101": (25.7617, -80.1918),  # Miami, FL
    "98101": (47.6062, -122.3321),  # Seattle, WA
    "80201": (39.7392, -104.9903),  # Denver, CO
    "02101": (42.3601, -71.0589),  # Boston, MA
}


def haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate the great-circle distance between two points on Earth.

    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees

    Returns:
        Distance in miles
    """
    # Earth's radius in miles
    earth_radius = 3959

    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    # Haversine formula
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c


def zip_to_coordinates(zip_code: str) -> Optional[Tuple[float, float]]:
    """
    Convert a zip code to latitude/longitude coordinates.

    Args:
        zip_code: US 5-digit zip code

    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    # Normalize zip code (remove any extra characters)
    normalized_zip = zip_code.strip()[:5]
    return ZIP_CODE_COORDS.get(normalized_zip)


def coordinates_to_bounding_box(
    lat: float, lon: float, radius_miles: float
) -> Tuple[float, float, float, float]:
    """
    Calculate a bounding box around a point with given radius.

    Args:
        lat: Center latitude in degrees
        lon: Center longitude in degrees
        radius_miles: Radius in miles

    Returns:
        Tuple of (min_lat, max_lat, min_lon, max_lon)
    """
    # Approximate degrees per mile (varies by latitude)
    lat_degrees_per_mile = 1 / 69.0
    lon_degrees_per_mile = 1 / (69.0 * math.cos(math.radians(lat)))

    lat_delta = radius_miles * lat_degrees_per_mile
    lon_delta = radius_miles * lon_degrees_per_mile

    return (
        lat - lat_delta,  # min_lat
        lat + lat_delta,  # max_lat
        lon - lon_delta,  # min_lon
        lon + lon_delta,  # max_lon
    )


def search_products_by_text(
    db: Session,
    query: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    retailer: Optional[str] = None,
    in_stock: Optional[bool] = None,
    page: int = 1,
    limit: int = 20,
) -> List[Product]:
    """
    Search products with various filters.

    Args:
        db: Database session
        query: Text search query for name/description/brand
        category: Filter by category
        brand: Filter by brand
        min_price: Minimum price filter
        max_price: Maximum price filter
        retailer: Filter by retailer name
        in_stock: Filter by stock availability
        page: Page number (1-indexed)
        limit: Results per page

    Returns:
        List of matching products
    """
    products_query = db.query(Product)

    # Text search on name, description, and brand
    if query:
        search_pattern = f"%{query}%"
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


def search_products_by_location(
    db: Session,
    zip_code: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_miles: float = 25.0,
    query: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> List[Product]:
    """
    Search products with location-based filtering.

    Note: This is a simplified implementation. In production, you would:
    1. Have retailers with location data (lat/lon)
    2. Filter retailers within the radius
    3. Return products available at those retailers

    Args:
        db: Database session
        zip_code: US zip code for location center
        latitude: Latitude for location center (used if zip_code not provided)
        longitude: Longitude for location center (used if zip_code not provided)
        radius_miles: Search radius in miles
        query: Text search query
        category: Filter by category
        page: Page number
        limit: Results per page

    Returns:
        List of matching products
    """
    # Get coordinates from zip code or use provided lat/lon
    coords = None
    if zip_code:
        coords = zip_to_coordinates(zip_code)
    elif latitude is not None and longitude is not None:
        coords = (latitude, longitude)

    # For now, we do text/category filtering
    # Location filtering would require retailer location data
    products_query = db.query(Product)

    if query:
        search_pattern = f"%{query}%"
        products_query = products_query.filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern),
                Product.brand.ilike(search_pattern),
            )
        )

    if category:
        products_query = products_query.filter(Product.category.ilike(f"%{category}%"))

    # Pagination
    offset = (page - 1) * limit
    products = products_query.offset(offset).limit(limit).all()

    return products


def get_search_suggestions(
    db: Session, query: str, limit: int = 10
) -> List[str]:
    """
    Get search suggestions based on product names.

    Args:
        db: Database session
        query: Partial search query
        limit: Maximum number of suggestions

    Returns:
        List of product name suggestions
    """
    search_pattern = f"%{query}%"

    products = (
        db.query(Product.name)
        .filter(Product.name.ilike(search_pattern))
        .distinct()
        .limit(limit)
        .all()
    )

    return [product.name for product in products]


def get_deals(
    db: Session,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    page: int = 1,
    limit: int = 20,
) -> List[Product]:
    """
    Find products with the best deals (lowest prices, in stock).

    Args:
        db: Database session
        category: Filter by category
        max_price: Maximum price filter
        page: Page number
        limit: Results per page

    Returns:
        List of products ordered by lowest price
    """
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
