"""
Shared pytest fixtures.

Strategy
────────
Each test function gets its own *fresh* in-memory SQLite database created by
overriding the FastAPI `get_db` dependency.  This guarantees full isolation
without requiring a real file on disk.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# In-memory URL — StaticPool ensures every connection sees the same DB
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture()
def client():
    """
    Yield a TestClient backed by a fresh in-memory SQLite DB.
    Tables are created before the test and dropped afterwards.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Teardown
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


# ── Reusable helpers ──────────────────────────────────────────────────────────

VALID_USER = {
    "email": "alice@example.com",
    "username": "alice",
    "password": "s3cur3P@ss",
}


@pytest.fixture()
def registered_user(client):
    """Register a user and return (client, user_payload)."""
    response = client.post("/auth/register", json=VALID_USER)
    assert response.status_code == 201
    return client, VALID_USER


@pytest.fixture()
def auth_token(registered_user):
    """Return a valid JWT for the pre-registered user."""
    client, user = registered_user
    response = client.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert response.status_code == 200
    return client, response.json()["access_token"]
