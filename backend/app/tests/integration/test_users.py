"""Integration tests for user endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


def test_get_current_user(client: TestClient, test_user: User, auth_headers: dict):
    """Test getting current user info."""
    response = client.get("/api/v1/users/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["username"] == test_user.username
    assert data["id"] == str(test_user.id)


def test_get_current_user_unauthorized(client: TestClient):
    """Test getting current user without auth."""
    response = client.get("/api/v1/users/me")

    assert response.status_code == 403  # No authorization header


def test_update_current_user(client: TestClient, test_user: User, auth_headers: dict):
    """Test updating current user."""
    response = client.put(
        "/api/v1/users/me",
        headers=auth_headers,
        json={
            "full_name": "Updated Name",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["email"] == test_user.email  # Email unchanged


def test_change_password(client: TestClient, test_user: User, auth_headers: dict):
    """Test changing password."""
    response = client.post(
        "/api/v1/users/me/change-password",
        headers=auth_headers,
        json={
            "current_password": "TestPassword123",
            "new_password": "NewPassword456",
        },
    )

    assert response.status_code == 200
    assert "Password updated successfully" in response.json()["message"]

    # Try logging in with new password
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "NewPassword456",
        },
    )
    assert login_response.status_code == 200


def test_change_password_wrong_current(client: TestClient, test_user: User, auth_headers: dict):
    """Test changing password with wrong current password."""
    response = client.post(
        "/api/v1/users/me/change-password",
        headers=auth_headers,
        json={
            "current_password": "WrongPassword",
            "new_password": "NewPassword456",
        },
    )

    assert response.status_code == 400
    assert "Incorrect password" in response.json()["detail"]


def test_regenerate_api_key(client: TestClient, test_user: User, auth_headers: dict):
    """Test regenerating API key."""
    old_api_key = test_user.api_key

    response = client.post(
        "/api/v1/users/me/regenerate-api-key",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "api_key" in data
    assert data["api_key"] != old_api_key
    assert data["api_key"].startswith("ut_")


def test_get_api_key(client: TestClient, test_user: User, auth_headers: dict):
    """Test getting API key."""
    response = client.get(
        "/api/v1/users/me/api-key",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["api_key"] == test_user.api_key
