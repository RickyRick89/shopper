"""Tests for search service functions."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.services import search as search_service
from app.services import product as product_service
from app.schemas.product import ProductCreate

# Use the same test database as conftest
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session(test_db):
    """Create a database session for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_haversine_distance():
    """Test haversine distance calculation."""
    # Distance between NYC and LA (approximately 2451 miles)
    nyc_lat, nyc_lon = 40.7128, -74.0060
    la_lat, la_lon = 34.0522, -118.2437

    distance = search_service.haversine_distance(nyc_lat, nyc_lon, la_lat, la_lon)

    # Should be approximately 2451 miles (with some tolerance)
    assert 2400 < distance < 2500


def test_haversine_distance_same_point():
    """Test haversine distance for same point is zero."""
    lat, lon = 40.7128, -74.0060

    distance = search_service.haversine_distance(lat, lon, lat, lon)

    assert distance == 0


def test_zip_to_coordinates_valid():
    """Test converting valid zip code to coordinates."""
    coords = search_service.zip_to_coordinates("10001")

    assert coords is not None
    lat, lon = coords
    # NYC coordinates
    assert 40.7 < lat < 40.8
    assert -74.0 < lon < -73.9


def test_zip_to_coordinates_unknown():
    """Test converting unknown zip code returns None."""
    coords = search_service.zip_to_coordinates("00000")

    assert coords is None


def test_zip_to_coordinates_normalization():
    """Test zip code normalization."""
    # With extra spaces
    coords = search_service.zip_to_coordinates("  10001  ")

    assert coords is not None


def test_coordinates_to_bounding_box():
    """Test calculating bounding box around a point."""
    lat, lon = 40.7484, -73.9967  # NYC
    radius = 25  # 25 miles

    min_lat, max_lat, min_lon, max_lon = search_service.coordinates_to_bounding_box(
        lat, lon, radius
    )

    # Bounding box should contain the center point
    assert min_lat < lat < max_lat
    assert min_lon < lon < max_lon

    # Box should extend in all directions
    assert max_lat - min_lat > 0
    assert max_lon - min_lon > 0


def test_search_products_by_text_basic(db_session):
    """Test basic text search via service."""
    # Create products
    product_service.create_product(
        db_session, ProductCreate(name="Apple iPhone 15", brand="Apple")
    )
    product_service.create_product(
        db_session, ProductCreate(name="Samsung Galaxy", brand="Samsung")
    )

    # Search
    products = search_service.search_products_by_text(db_session, query="Apple")

    assert len(products) == 1
    assert "Apple" in products[0].name or products[0].brand == "Apple"


def test_search_products_by_text_category(db_session):
    """Test text search with category filter via service."""
    # Create products
    product_service.create_product(
        db_session, ProductCreate(name="Laptop", category="Electronics")
    )
    product_service.create_product(
        db_session, ProductCreate(name="T-Shirt", category="Clothing")
    )

    # Search by category
    products = search_service.search_products_by_text(db_session, category="Electronics")

    assert len(products) >= 1
    assert all("Electronics" in p.category for p in products)


def test_search_products_by_location_with_zip(db_session):
    """Test location-based search with zip code via service."""
    # Create a product
    product_service.create_product(
        db_session, ProductCreate(name="NYC Product", category="Electronics")
    )

    # Search by location
    products = search_service.search_products_by_location(
        db_session, zip_code="10001", radius_miles=25
    )

    assert isinstance(products, list)


def test_search_products_by_location_with_coords(db_session):
    """Test location-based search with coordinates via service."""
    # Create a product
    product_service.create_product(
        db_session, ProductCreate(name="Coord Product", category="Test")
    )

    # Search by coordinates
    products = search_service.search_products_by_location(
        db_session, latitude=40.7128, longitude=-74.0060, radius_miles=50
    )

    assert isinstance(products, list)


def test_get_search_suggestions(db_session):
    """Test getting search suggestions via service."""
    # Create products
    product_service.create_product(db_session, ProductCreate(name="Apple iPhone 15"))
    product_service.create_product(db_session, ProductCreate(name="Apple MacBook Pro"))
    product_service.create_product(db_session, ProductCreate(name="Samsung Galaxy"))

    # Get suggestions
    suggestions = search_service.get_search_suggestions(db_session, "Apple")

    assert len(suggestions) == 2
    assert all("Apple" in s for s in suggestions)


def test_get_deals(db_session):
    """Test getting deals via service."""
    # Create product with price
    product = product_service.create_product(
        db_session, ProductCreate(name="Deal Product", category="Test")
    )
    product_service.add_product_price(
        db_session, product.id, "Amazon", 25.0, in_stock=True
    )

    # Get deals
    deals = search_service.get_deals(db_session)

    assert len(deals) >= 1


def test_get_deals_with_category(db_session):
    """Test getting deals with category filter via service."""
    # Create products with prices
    product1 = product_service.create_product(
        db_session, ProductCreate(name="Electronics Deal", category="Electronics")
    )
    product_service.add_product_price(db_session, product1.id, "Amazon", 30.0, in_stock=True)

    product2 = product_service.create_product(
        db_session, ProductCreate(name="Clothing Deal", category="Clothing")
    )
    product_service.add_product_price(db_session, product2.id, "Walmart", 20.0, in_stock=True)

    # Get electronics deals
    deals = search_service.get_deals(db_session, category="Electronics")

    assert len(deals) >= 1
    assert all("Electronics" in d.category for d in deals)


def test_search_pagination(db_session):
    """Test search pagination via service."""
    # Create 15 products
    for i in range(15):
        product_service.create_product(
            db_session, ProductCreate(name=f"Pagination Product {i}")
        )

    # Get first page
    page1 = search_service.search_products_by_text(db_session, page=1, limit=10)
    assert len(page1) == 10

    # Get second page
    page2 = search_service.search_products_by_text(db_session, page=2, limit=10)
    assert len(page2) == 5
