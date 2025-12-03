"""Tests for price history endpoints."""

from datetime import datetime, timedelta, timezone


def test_get_product_price_history_empty(client):
    """Test getting price history for a product with no history."""
    # Create a product
    product_response = client.post(
        "/api/v1/products", json={"name": "Price History Test Product"}
    )
    product_id = product_response.json()["id"]

    response = client.get(f"/api/v1/wishlist/products/{product_id}/price-history")
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_get_product_price_history_nonexistent(client):
    """Test getting price history for a nonexistent product."""
    response = client.get("/api/v1/wishlist/products/99999/price-history")
    assert response.status_code == 404


def test_get_wishlist_item_price_history_unauthorized(client):
    """Test getting wishlist item price history without auth."""
    response = client.get("/api/v1/wishlist/1/price-history")
    assert response.status_code == 401


def test_get_wishlist_item_price_history_not_found(client, auth_headers):
    """Test getting price history for a nonexistent wishlist item."""
    response = client.get(
        "/api/v1/wishlist/99999/price-history", headers=auth_headers
    )
    assert response.status_code == 404


def test_get_wishlist_item_price_history_empty(client, auth_headers, test_db):
    """Test getting price history for a wishlist item with no history."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db.database import Base

    # Create a product
    product_response = client.post(
        "/api/v1/products", json={"name": "Wishlist Price History Product"}
    )
    product_id = product_response.json()["id"]

    # Add to wishlist
    wishlist_response = client.post(
        "/api/v1/wishlist",
        json={"product_id": product_id, "target_price": 100.0},
        headers=auth_headers,
    )
    item_id = wishlist_response.json()["id"]

    # Get price history
    response = client.get(
        f"/api/v1/wishlist/{item_id}/price-history", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == product_id
    assert data["product_name"] == "Wishlist Price History Product"
    assert data["data"] == []
    assert data["stats"]["min_price"] == 0.0
    assert data["stats"]["max_price"] == 0.0


def test_get_product_price_history_with_days_filter(client):
    """Test getting price history with days filter."""
    # Create a product
    product_response = client.post(
        "/api/v1/products", json={"name": "Days Filter Product"}
    )
    product_id = product_response.json()["id"]

    response = client.get(
        f"/api/v1/wishlist/products/{product_id}/price-history?days=7"
    )
    assert response.status_code == 200


def test_get_product_price_history_with_retailer_filter(client):
    """Test getting price history with retailer filter."""
    # Create a product
    product_response = client.post(
        "/api/v1/products", json={"name": "Retailer Filter Product"}
    )
    product_id = product_response.json()["id"]

    response = client.get(
        f"/api/v1/wishlist/products/{product_id}/price-history?retailer=Amazon"
    )
    assert response.status_code == 200
