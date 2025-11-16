"""Integration tests for organization endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.organization import Organization


def test_create_organization(client: TestClient, test_user: User, auth_headers: dict):
    """Test creating an organization."""
    response = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "name": "My Organization",
            "slug": "my-org",
            "description": "Test organization",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Organization"
    assert data["slug"] == "my-org"
    assert data["owner_id"] == str(test_user.id)


def test_create_organization_duplicate_slug(
    client: TestClient,
    test_user: User,
    test_organization: Organization,
    auth_headers: dict
):
    """Test creating organization with duplicate slug."""
    response = client.post(
        "/api/v1/organizations",
        headers=auth_headers,
        json={
            "name": "Another Organization",
            "slug": test_organization.slug,
        },
    )

    assert response.status_code == 400
    assert "slug already exists" in response.json()["detail"]


def test_list_organizations(
    client: TestClient,
    test_user: User,
    test_organization: Organization,
    auth_headers: dict
):
    """Test listing organizations."""
    response = client.get("/api/v1/organizations", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == str(test_organization.id)


def test_get_organization(
    client: TestClient,
    test_user: User,
    test_organization: Organization,
    auth_headers: dict
):
    """Test getting a single organization."""
    response = client.get(
        f"/api/v1/organizations/{test_organization.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_organization.id)
    assert data["name"] == test_organization.name


def test_update_organization(
    client: TestClient,
    test_user: User,
    test_organization: Organization,
    auth_headers: dict
):
    """Test updating organization."""
    response = client.put(
        f"/api/v1/organizations/{test_organization.id}",
        headers=auth_headers,
        json={
            "name": "Updated Organization Name",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Organization Name"
    assert data["description"] == "Updated description"


def test_delete_organization(
    client: TestClient,
    test_user: User,
    test_organization: Organization,
    auth_headers: dict
):
    """Test deleting organization."""
    response = client.delete(
        f"/api/v1/organizations/{test_organization.id}",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(
        f"/api/v1/organizations/{test_organization.id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404
