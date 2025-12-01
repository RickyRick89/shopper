"""Tests for search endpoints."""


def test_search_products_by_query(client):
    """Test searching products by text query."""
    # Create products
    client.post(
        "/api/v1/products",
        json={"name": "Apple iPhone 15", "brand": "Apple", "category": "Electronics"},
    )
    client.post(
        "/api/v1/products",
        json={"name": "Samsung Galaxy S24", "brand": "Samsung", "category": "Electronics"},
    )
    client.post(
        "/api/v1/products",
        json={"name": "Apple MacBook Pro", "brand": "Apple", "category": "Computers"},
    )

    # Search for Apple
    response = client.get("/api/v1/search/products?q=Apple")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all("Apple" in p["name"] or p["brand"] == "Apple" for p in data)


def test_search_products_by_category(client):
    """Test filtering products by category."""
    # Create products
    client.post(
        "/api/v1/products",
        json={"name": "Laptop", "category": "Electronics"},
    )
    client.post(
        "/api/v1/products",
        json={"name": "T-Shirt", "category": "Clothing"},
    )

    # Filter by category
    response = client.get("/api/v1/search/products?category=Electronics")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "Electronics"


def test_search_products_by_brand(client):
    """Test filtering products by brand."""
    # Create products
    client.post(
        "/api/v1/products",
        json={"name": "iPhone", "brand": "Apple"},
    )
    client.post(
        "/api/v1/products",
        json={"name": "Galaxy", "brand": "Samsung"},
    )

    # Filter by brand
    response = client.get("/api/v1/search/products?brand=Apple")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["brand"] == "Apple"


def test_search_products_by_price_range(client):
    """Test filtering products by price range."""
    # Create products with prices
    product1_resp = client.post(
        "/api/v1/products", json={"name": "Cheap Product"}
    )
    product1_id = product1_resp.json()["id"]
    client.post(
        f"/api/v1/products/{product1_id}/prices",
        json={"product_id": product1_id, "retailer": "Amazon", "price": 25.0},
    )

    product2_resp = client.post(
        "/api/v1/products", json={"name": "Expensive Product"}
    )
    product2_id = product2_resp.json()["id"]
    client.post(
        f"/api/v1/products/{product2_id}/prices",
        json={"product_id": product2_id, "retailer": "Amazon", "price": 150.0},
    )

    # Search by min price
    response = client.get("/api/v1/search/products?min_price=100")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Expensive Product"

    # Search by max price
    response = client.get("/api/v1/search/products?max_price=50")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Cheap Product"


def test_search_products_by_retailer(client):
    """Test filtering products by retailer."""
    # Create products with prices at different retailers
    product1_resp = client.post(
        "/api/v1/products", json={"name": "Amazon Product"}
    )
    product1_id = product1_resp.json()["id"]
    client.post(
        f"/api/v1/products/{product1_id}/prices",
        json={"product_id": product1_id, "retailer": "Amazon", "price": 50.0},
    )

    product2_resp = client.post(
        "/api/v1/products", json={"name": "Walmart Product"}
    )
    product2_id = product2_resp.json()["id"]
    client.post(
        f"/api/v1/products/{product2_id}/prices",
        json={"product_id": product2_id, "retailer": "Walmart", "price": 45.0},
    )

    # Search by retailer
    response = client.get("/api/v1/search/products?retailer=Amazon")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Amazon Product"


def test_search_products_in_stock(client):
    """Test filtering products by stock availability."""
    # Create product in stock
    product1_resp = client.post(
        "/api/v1/products", json={"name": "In Stock Product"}
    )
    product1_id = product1_resp.json()["id"]
    client.post(
        f"/api/v1/products/{product1_id}/prices",
        json={"product_id": product1_id, "retailer": "Amazon", "price": 50.0, "in_stock": True},
    )

    # Create product out of stock
    product2_resp = client.post(
        "/api/v1/products", json={"name": "Out of Stock Product"}
    )
    product2_id = product2_resp.json()["id"]
    client.post(
        f"/api/v1/products/{product2_id}/prices",
        json={"product_id": product2_id, "retailer": "Amazon", "price": 45.0, "in_stock": False},
    )

    # Search for in stock only
    response = client.get("/api/v1/search/products?in_stock=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "In Stock Product"


def test_search_deals(client):
    """Test getting deals (lowest priced, in-stock products)."""
    # Create products with prices
    product1_resp = client.post(
        "/api/v1/products", json={"name": "Best Deal", "category": "Electronics"}
    )
    product1_id = product1_resp.json()["id"]
    client.post(
        f"/api/v1/products/{product1_id}/prices",
        json={"product_id": product1_id, "retailer": "Amazon", "price": 10.0, "in_stock": True},
    )

    product2_resp = client.post(
        "/api/v1/products", json={"name": "Pricey Item", "category": "Electronics"}
    )
    product2_id = product2_resp.json()["id"]
    client.post(
        f"/api/v1/products/{product2_id}/prices",
        json={"product_id": product2_id, "retailer": "Amazon", "price": 100.0, "in_stock": True},
    )

    # Get deals
    response = client.get("/api/v1/search/deals")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # First item should be the cheapest
    assert data[0]["name"] == "Best Deal"


def test_search_suggestions(client):
    """Test getting search suggestions."""
    # Create products
    client.post("/api/v1/products", json={"name": "Apple iPhone 15"})
    client.post("/api/v1/products", json={"name": "Apple MacBook Pro"})
    client.post("/api/v1/products", json={"name": "Samsung Galaxy"})

    # Get suggestions
    response = client.get("/api/v1/search/suggestions?q=Apple")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all("Apple" in name for name in data)


def test_search_pagination(client):
    """Test search pagination."""
    # Create multiple products
    for i in range(15):
        client.post(
            "/api/v1/products", json={"name": f"Product {i}", "category": "Test"}
        )

    # Get first page
    response = client.get("/api/v1/search/products?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10

    # Get second page
    response = client.get("/api/v1/search/products?page=2&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5


def test_search_empty_results(client):
    """Test search with no matching results."""
    # Create a product
    client.post("/api/v1/products", json={"name": "Test Product"})

    # Search for non-existent product
    response = client.get("/api/v1/search/products?q=NonExistent12345")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
