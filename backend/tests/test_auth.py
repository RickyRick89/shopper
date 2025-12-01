"""Tests for authentication endpoints."""


def test_register_user(client):
    """Test user registration."""
    user_data = {
        "email": "newuser@example.com",
        "password": "password123",
        "full_name": "New User",
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client):
    """Test registration with duplicate email."""
    user_data = {
        "email": "duplicate@example.com",
        "password": "password123",
    }
    client.post("/api/v1/auth/register", json=user_data)

    # Try to register again with same email
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client):
    """Test successful login."""
    # Register user first
    user_data = {
        "email": "login@example.com",
        "password": "password123",
    }
    client.post("/api/v1/auth/register", json=user_data)

    # Login
    login_data = {"username": "login@example.com", "password": "password123"}
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    """Test login with wrong password."""
    # Register user first
    user_data = {
        "email": "wrong@example.com",
        "password": "password123",
    }
    client.post("/api/v1/auth/register", json=user_data)

    # Login with wrong password
    login_data = {"username": "wrong@example.com", "password": "wrongpassword"}
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    """Test login with nonexistent user."""
    login_data = {"username": "nonexistent@example.com", "password": "password123"}
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
