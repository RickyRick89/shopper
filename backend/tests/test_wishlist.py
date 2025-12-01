"""Tests for wishlist endpoints."""


def test_add_to_wishlist(client, auth_headers):
    """Test adding a product to wishlist."""
    # Create a product first
    product_response = client.post(
        "/api/v1/products", json={"name": "Wishlist Product"}
    )
    product_id = product_response.json()["id"]

    # Add to wishlist
    wishlist_data = {"product_id": product_id, "target_price": 50.0}
    response = client.post(
        "/api/v1/wishlist", json=wishlist_data, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == product_id
    assert data["target_price"] == 50.0


def test_get_wishlist(client, auth_headers):
    """Test getting user's wishlist."""
    # Create products and add to wishlist
    for i in range(2):
        product_response = client.post(
            "/api/v1/products", json={"name": f"Wishlist Product {i}"}
        )
        product_id = product_response.json()["id"]
        client.post(
            "/api/v1/wishlist",
            json={"product_id": product_id},
            headers=auth_headers,
        )

    response = client.get("/api/v1/wishlist", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_update_wishlist_item(client, auth_headers):
    """Test updating a wishlist item."""
    # Create a product and add to wishlist
    product_response = client.post(
        "/api/v1/products", json={"name": "Update Wishlist Product"}
    )
    product_id = product_response.json()["id"]

    wishlist_response = client.post(
        "/api/v1/wishlist",
        json={"product_id": product_id, "target_price": 100.0},
        headers=auth_headers,
    )
    item_id = wishlist_response.json()["id"]

    # Update the target price
    response = client.put(
        f"/api/v1/wishlist/{item_id}",
        json={"target_price": 75.0},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["target_price"] == 75.0


def test_remove_from_wishlist(client, auth_headers):
    """Test removing a product from wishlist."""
    # Create a product and add to wishlist
    product_response = client.post(
        "/api/v1/products", json={"name": "Delete Wishlist Product"}
    )
    product_id = product_response.json()["id"]

    wishlist_response = client.post(
        "/api/v1/wishlist",
        json={"product_id": product_id},
        headers=auth_headers,
    )
    item_id = wishlist_response.json()["id"]

    # Remove from wishlist
    response = client.delete(f"/api/v1/wishlist/{item_id}", headers=auth_headers)
    assert response.status_code == 204


def test_wishlist_unauthorized(client):
    """Test wishlist endpoints without auth."""
    response = client.get("/api/v1/wishlist")
    assert response.status_code == 401


def test_add_nonexistent_product_to_wishlist(client, auth_headers):
    """Test adding a nonexistent product to wishlist."""
    response = client.post(
        "/api/v1/wishlist",
        json={"product_id": 99999},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_add_duplicate_to_wishlist(client, auth_headers):
    """Test adding the same product to wishlist twice."""
    # Create a product
    product_response = client.post(
        "/api/v1/products", json={"name": "Duplicate Wishlist Product"}
    )
    product_id = product_response.json()["id"]

    # Add to wishlist twice
    client.post(
        "/api/v1/wishlist", json={"product_id": product_id}, headers=auth_headers
    )
    response = client.post(
        "/api/v1/wishlist", json={"product_id": product_id}, headers=auth_headers
    )
    assert response.status_code == 400
    assert "already in wishlist" in response.json()["detail"]
