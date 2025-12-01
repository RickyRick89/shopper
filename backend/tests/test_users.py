"""Tests for user endpoints."""


def test_get_current_user(client, auth_headers):
    """Test getting current user info."""
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"


def test_get_current_user_unauthorized(client):
    """Test getting current user without auth."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_update_current_user(client, auth_headers):
    """Test updating current user info."""
    update_data = {"full_name": "Updated Name"}
    response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"
