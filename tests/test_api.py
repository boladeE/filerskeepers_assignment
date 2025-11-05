"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "docs" in response.json()


def test_docs_endpoint():
    """Test that Swagger docs are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_endpoint():
    """Test that OpenAPI schema is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()


def test_books_endpoint_requires_auth():
    """Test that books endpoint requires authentication."""
    response = client.get("/books")
    assert response.status_code == 401
    assert "API key required" in response.json()["detail"]


def test_books_endpoint_invalid_api_key():
    """Test that books endpoint rejects invalid API key."""
    response = client.get("/books", headers={"X-API-Key": "invalid-key"})
    assert response.status_code == 401


def test_changes_endpoint_requires_auth():
    """Test that changes endpoint requires authentication."""
    response = client.get("/changes")
    assert response.status_code == 401
    assert "API key required" in response.json()["detail"]


def test_book_detail_endpoint_requires_auth():
    """Test that book detail endpoint requires authentication."""
    response = client.get("/books/507f1f77bcf86cd799439011")
    assert response.status_code == 401


def test_rate_limit_headers():
    """Test that rate limit doesn't apply to health check."""
    # Health check should not be rate limited
    for _ in range(5):
        response = client.get("/health")
        assert response.status_code == 200

