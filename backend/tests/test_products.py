"""Tests for product endpoints."""


def test_create_product(client):
    """Test creating a product."""
    product_data = {
        "name": "Test Product",
        "description": "A test product description",
        "brand": "Test Brand",
        "category": "Electronics",
    }
    response = client.post("/api/v1/products", json=product_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["brand"] == "Test Brand"
    assert "id" in data


def test_list_products(client):
    """Test listing products."""
    # Create some products first
    for i in range(3):
        client.post(
            "/api/v1/products", json={"name": f"Product {i}", "category": "Test"}
        )

    response = client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_search_products(client):
    """Test searching products."""
    # Create products
    client.post("/api/v1/products", json={"name": "Apple iPhone", "brand": "Apple"})
    client.post(
        "/api/v1/products", json={"name": "Samsung Galaxy", "brand": "Samsung"}
    )

    # Search for Apple
    response = client.get("/api/v1/products?query=apple")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "Apple" in data[0]["name"]


def test_get_product(client):
    """Test getting a single product."""
    # Create a product
    create_response = client.post(
        "/api/v1/products",
        json={"name": "Specific Product", "description": "Details here"},
    )
    product_id = create_response.json()["id"]

    response = client.get(f"/api/v1/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Specific Product"


def test_get_nonexistent_product(client):
    """Test getting a product that doesn't exist."""
    response = client.get("/api/v1/products/99999")
    assert response.status_code == 404


def test_update_product(client):
    """Test updating a product."""
    # Create a product
    create_response = client.post(
        "/api/v1/products", json={"name": "Original Name"}
    )
    product_id = create_response.json()["id"]

    # Update it
    response = client.put(
        f"/api/v1/products/{product_id}", json={"name": "Updated Name"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


def test_delete_product(client):
    """Test deleting a product."""
    # Create a product
    create_response = client.post(
        "/api/v1/products", json={"name": "To Delete"}
    )
    product_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/api/v1/products/{product_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 404


def test_add_price_to_product(client):
    """Test adding a price to a product."""
    # Create a product
    create_response = client.post(
        "/api/v1/products", json={"name": "Product with Price"}
    )
    product_id = create_response.json()["id"]

    # Add a price
    price_data = {
        "product_id": product_id,
        "retailer": "Amazon",
        "price": 99.99,
        "currency": "USD",
        "url": "https://amazon.com/product",
        "in_stock": True,
    }
    response = client.post(f"/api/v1/products/{product_id}/prices", json=price_data)
    assert response.status_code == 201
    data = response.json()
    assert data["retailer"] == "Amazon"
    assert data["price"] == 99.99


def test_get_product_prices(client):
    """Test getting prices for a product."""
    # Create a product
    create_response = client.post(
        "/api/v1/products", json={"name": "Multi-Price Product"}
    )
    product_id = create_response.json()["id"]

    # Add multiple prices
    retailers = ["Amazon", "Walmart", "Target"]
    for i, retailer in enumerate(retailers):
        client.post(
            f"/api/v1/products/{product_id}/prices",
            json={"product_id": product_id, "retailer": retailer, "price": 50.0 + i},
        )

    response = client.get(f"/api/v1/products/{product_id}/prices")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
