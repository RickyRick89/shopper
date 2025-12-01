"""Tests for product service functions."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.services import product as product_service
from app.schemas.product import ProductCreate, ProductUpdate

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


def test_product_service_create(db_session):
    """Test creating a product via service."""
    product_data = ProductCreate(
        name="Service Test Product",
        description="Created via service",
        brand="TestBrand",
        category="TestCategory",
    )
    product = product_service.create_product(db_session, product_data)

    assert product.id is not None
    assert product.name == "Service Test Product"
    assert product.brand == "TestBrand"


def test_product_service_get(db_session):
    """Test getting a product via service."""
    # Create a product first
    product_data = ProductCreate(name="Get Test Product")
    created = product_service.create_product(db_session, product_data)

    # Get the product
    product = product_service.get_product(db_session, created.id)

    assert product is not None
    assert product.name == "Get Test Product"


def test_product_service_get_nonexistent(db_session):
    """Test getting a nonexistent product via service."""
    product = product_service.get_product(db_session, 99999)
    assert product is None


def test_product_service_update(db_session):
    """Test updating a product via service."""
    # Create a product first
    product_data = ProductCreate(name="Original Name")
    created = product_service.create_product(db_session, product_data)

    # Update the product
    update_data = ProductUpdate(name="Updated Name", brand="NewBrand")
    updated = product_service.update_product(db_session, created.id, update_data)

    assert updated is not None
    assert updated.name == "Updated Name"
    assert updated.brand == "NewBrand"


def test_product_service_delete(db_session):
    """Test deleting a product via service."""
    # Create a product first
    product_data = ProductCreate(name="To Delete")
    created = product_service.create_product(db_session, product_data)

    # Delete the product
    result = product_service.delete_product(db_session, created.id)
    assert result is True

    # Verify it's gone
    product = product_service.get_product(db_session, created.id)
    assert product is None


def test_product_service_get_products(db_session):
    """Test getting products list via service."""
    # Create some products
    for i in range(5):
        product_service.create_product(
            db_session, ProductCreate(name=f"Product {i}", category="TestCat")
        )

    # Get products
    products = product_service.get_products(db_session, skip=0, limit=10)
    assert len(products) >= 5


def test_product_service_get_products_with_query(db_session):
    """Test getting products with text filter via service."""
    # Create products
    product_service.create_product(db_session, ProductCreate(name="Apple iPhone"))
    product_service.create_product(db_session, ProductCreate(name="Samsung Galaxy"))

    # Search
    products = product_service.get_products(db_session, query="Apple")
    assert len(products) == 1
    assert "Apple" in products[0].name


def test_product_service_count(db_session):
    """Test counting products via service."""
    # Create some products
    for i in range(3):
        product_service.create_product(
            db_session, ProductCreate(name=f"Count Test {i}")
        )

    # Count products
    count = product_service.count_products(db_session)
    assert count >= 3


def test_product_service_add_price(db_session):
    """Test adding a price to a product via service."""
    # Create a product
    product = product_service.create_product(db_session, ProductCreate(name="Price Test"))

    # Add a price
    price = product_service.add_product_price(
        db_session, product.id, retailer="Amazon", price=99.99
    )

    assert price is not None
    assert price.retailer == "Amazon"
    assert price.price == 99.99


def test_product_service_get_lowest_price(db_session):
    """Test getting lowest price for a product via service."""
    # Create a product
    product = product_service.create_product(db_session, ProductCreate(name="Multi Price"))

    # Add multiple prices
    product_service.add_product_price(db_session, product.id, "Amazon", 100.0, in_stock=True)
    product_service.add_product_price(db_session, product.id, "Walmart", 85.0, in_stock=True)
    product_service.add_product_price(db_session, product.id, "Target", 90.0, in_stock=True)

    # Get lowest price
    lowest = product_service.get_lowest_price(db_session, product.id)

    assert lowest is not None
    assert lowest.price == 85.0
    assert lowest.retailer == "Walmart"


def test_product_service_get_products_by_category(db_session):
    """Test getting products by category via service."""
    # Create products in different categories
    product_service.create_product(
        db_session, ProductCreate(name="Electronics 1", category="Electronics")
    )
    product_service.create_product(
        db_session, ProductCreate(name="Clothing 1", category="Clothing")
    )

    # Get by category
    electronics = product_service.get_products_by_category(db_session, "Electronics")

    assert len(electronics) >= 1
    assert all(p.category == "Electronics" for p in electronics)


def test_product_service_get_products_by_brand(db_session):
    """Test getting products by brand via service."""
    # Create products with different brands
    product_service.create_product(
        db_session, ProductCreate(name="iPhone", brand="Apple")
    )
    product_service.create_product(
        db_session, ProductCreate(name="Galaxy", brand="Samsung")
    )

    # Get by brand
    apple_products = product_service.get_products_by_brand(db_session, "Apple")

    assert len(apple_products) >= 1
    assert all("Apple" in p.brand for p in apple_products)
