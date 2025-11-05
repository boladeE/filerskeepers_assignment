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


def test_books_endpoint_requires_auth():
    """Test that books endpoint requires authentication."""
    response = client.get("/books")
    assert response.status_code == 401


def test_changes_endpoint_requires_auth():
    """Test that changes endpoint requires authentication."""
    response = client.get("/changes")
    assert response.status_code == 401

