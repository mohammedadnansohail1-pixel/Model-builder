"""Integration tests for project endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.organization import Organization
from app.models.project import Project


def test_create_project(
    client: TestClient,
    test_user: User,
    test_organization: Organization,
    auth_headers: dict
):
    """Test creating a project."""
    response = client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={
            "name": "My Project",
            "organization_id": str(test_organization.id),
            "description": "Test project",
            "tags": ["ml", "nlp"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Project"
    assert data["organization_id"] == str(test_organization.id)
    assert data["tags"] == ["ml", "nlp"]


def test_list_projects(
    client: TestClient,
    test_user: User,
    test_project: Project,
    auth_headers: dict
):
    """Test listing projects."""
    response = client.get("/api/v1/projects", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_list_projects_by_organization(
    client: TestClient,
    test_user: User,
    test_organization: Organization,
    test_project: Project,
    auth_headers: dict
):
    """Test listing projects filtered by organization."""
    response = client.get(
        f"/api/v1/projects?organization_id={test_organization.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert all(p["organization_id"] == str(test_organization.id) for p in data)


def test_get_project(
    client: TestClient,
    test_user: User,
    test_project: Project,
    auth_headers: dict
):
    """Test getting a single project."""
    response = client.get(
        f"/api/v1/projects/{test_project.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_project.id)
    assert data["name"] == test_project.name


def test_update_project(
    client: TestClient,
    test_user: User,
    test_project: Project,
    auth_headers: dict
):
    """Test updating a project."""
    response = client.put(
        f"/api/v1/projects/{test_project.id}",
        headers=auth_headers,
        json={
            "name": "Updated Project",
            "description": "Updated description",
            "tags": ["updated", "test"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Project"
    assert data["description"] == "Updated description"
    assert data["tags"] == ["updated", "test"]


def test_delete_project(
    client: TestClient,
    test_user: User,
    test_project: Project,
    auth_headers: dict
):
    """Test deleting a project."""
    response = client.delete(
        f"/api/v1/projects/{test_project.id}",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(
        f"/api/v1/projects/{test_project.id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404
