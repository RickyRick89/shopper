"""Tests for location-based search and search service functions."""


def test_search_by_location_with_zip(client):
    """Test searching products by zip code location."""
    # Create a product
    client.post(
        "/api/v1/products",
        json={"name": "Local Product", "category": "Electronics"},
    )

    # Search by location with zip code
    response = client.get("/api/v1/search/location?zip_code=10001")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_search_by_location_with_coordinates(client):
    """Test searching products by latitude/longitude."""
    # Create a product
    client.post(
        "/api/v1/products",
        json={"name": "Nearby Product", "category": "Clothing"},
    )

    # Search by coordinates
    response = client.get("/api/v1/search/location?latitude=40.7128&longitude=-74.0060&radius=50")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_search_by_location_with_category_filter(client):
    """Test location search with category filter."""
    # Create products in different categories
    client.post(
        "/api/v1/products",
        json={"name": "Electronic Item", "category": "Electronics"},
    )
    client.post(
        "/api/v1/products",
        json={"name": "Clothing Item", "category": "Clothing"},
    )

    # Search by location with category filter
    response = client.get("/api/v1/search/location?zip_code=10001&category=Electronics")
    assert response.status_code == 200
    data = response.json()
    assert all(p["category"] == "Electronics" for p in data)


def test_search_by_location_with_query(client):
    """Test location search with text query."""
    # Create products
    client.post(
        "/api/v1/products",
        json={"name": "Apple iPhone 15", "brand": "Apple"},
    )
    client.post(
        "/api/v1/products",
        json={"name": "Samsung Galaxy", "brand": "Samsung"},
    )

    # Search by location with query
    response = client.get("/api/v1/search/location?zip_code=10001&q=Apple")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "Apple" in data[0]["name"] or data[0]["brand"] == "Apple"


def test_get_coordinates_from_zip_valid(client):
    """Test getting coordinates from a valid zip code."""
    response = client.get("/api/v1/search/coordinates?zip_code=10001")
    assert response.status_code == 200
    data = response.json()
    assert data["zip_code"] == "10001"
    assert data["latitude"] is not None
    assert data["longitude"] is not None
    # Verify approximate coordinates for NYC
    assert 40.7 < data["latitude"] < 40.8
    assert -74.0 < data["longitude"] < -73.9


def test_get_coordinates_from_zip_unknown(client):
    """Test getting coordinates from an unknown zip code."""
    response = client.get("/api/v1/search/coordinates?zip_code=00000")
    assert response.status_code == 200
    data = response.json()
    assert data["zip_code"] == "00000"
    assert data["latitude"] is None
    assert data["longitude"] is None
    assert "message" in data


def test_location_search_pagination(client):
    """Test location search with pagination."""
    # Create multiple products
    for i in range(15):
        client.post(
            "/api/v1/products",
            json={"name": f"Product {i}", "category": "Test"},
        )

    # Get first page
    response = client.get("/api/v1/search/location?zip_code=10001&page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10

    # Get second page
    response = client.get("/api/v1/search/location?zip_code=10001&page=2&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5


def test_location_search_radius_validation(client):
    """Test that radius parameter is properly validated."""
    # Radius too small
    response = client.get("/api/v1/search/location?zip_code=10001&radius=0.5")
    assert response.status_code == 422  # Validation error

    # Radius too large
    response = client.get("/api/v1/search/location?zip_code=10001&radius=600")
    assert response.status_code == 422  # Validation error

    # Valid radius
    response = client.get("/api/v1/search/location?zip_code=10001&radius=100")
    assert response.status_code == 200
