"""Pytest configuration and test client fixtures for FedBank MLOps."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure backend and workspace are on path
project_root = Path(__file__).resolve().parents[1]
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

from app.main import app
from app.database.init_db import init_db
from app.database import SessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database is initialized and seeded before test suite runs."""
    init_db()
    yield


@pytest.fixture
def client():
    """TestClient instance."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Yield DB session and rollback/close after each test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def admin_token(client):
    """Retrieve access token for default SUPER_ADMIN user."""
    res = client.post("/api/v1/auth/login", json={"email": "admin@fedbank.com", "password": "Admin@123"})
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    return res.json()["access_token"]


@pytest.fixture
def auth_headers(admin_token):
    """Headers with Bearer access token."""
    return {"Authorization": f"Bearer {admin_token}"}
