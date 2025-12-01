"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app

# Use SQLite in-memory database for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_db():
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for a test user."""
    # Register a test user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    }
    client.post("/api/v1/auth/register", json=user_data)

    # Login and get token
    login_data = {"username": "test@example.com", "password": "testpassword123"}
    response = client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}
