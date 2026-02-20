"""
Tests for /auth/register, /auth/login, and /auth/me endpoints.

Coverage
────────
Register  (5 tests)
  ✓ success → 201 with correct body shape
  ✗ duplicate email → 409
  ✗ duplicate username → 409
  ✗ password too short → 422
  ✗ invalid email format → 422

Login     (3 tests)
  ✓ success → 200 with JWT token
  ✗ wrong password → 401
  ✗ unregistered email → 401

Me        (3 tests)
  ✓ valid token → 200 with user data matching registered user
  ✗ no Authorization header → 403
  ✗ tampered/invalid token → 401
"""

import pytest

from tests.conftest import VALID_USER


# ═══════════════════════════════════════════════════════════════════════════════
# POST /auth/register
# ═══════════════════════════════════════════════════════════════════════════════


class TestRegister:

    def test_register_success(self, client):
        """A valid payload must return 201 with the created user."""
        response = client.post("/auth/register", json=VALID_USER)

        assert response.status_code == 201
        body = response.json()
        assert body["message"] == "Account created successfully"

        user = body["user"]
        assert user["email"] == VALID_USER["email"]
        assert user["username"] == VALID_USER["username"]
        assert "id" in user
        assert "created_at" in user
        # Password must never appear in the response
        assert "password" not in user
        assert "hashed_password" not in user

    def test_register_duplicate_email(self, client):
        """Registering the same email twice must return 409."""
        client.post("/auth/register", json=VALID_USER)

        duplicate = {**VALID_USER, "username": "different_user"}
        response = client.post("/auth/register", json=duplicate)

        assert response.status_code == 409
        assert "email" in response.json()["detail"].lower()

    def test_register_duplicate_username(self, client):
        """Registering the same username twice must return 409."""
        client.post("/auth/register", json=VALID_USER)

        duplicate = {**VALID_USER, "email": "other@example.com"}
        response = client.post("/auth/register", json=duplicate)

        assert response.status_code == 409
        assert "username" in response.json()["detail"].lower()

    def test_register_password_too_short(self, client):
        """A password shorter than 8 characters must be rejected with 422."""
        payload = {**VALID_USER, "password": "short"}
        response = client.post("/auth/register", json=payload)

        assert response.status_code == 422

    def test_register_invalid_email(self, client):
        """A malformed email address must be rejected with 422."""
        payload = {**VALID_USER, "email": "not-an-email"}
        response = client.post("/auth/register", json=payload)

        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# POST /auth/login
# ═══════════════════════════════════════════════════════════════════════════════


class TestLogin:

    def test_login_success(self, registered_user):
        """Valid credentials must return 200 and a bearer JWT."""
        client, user = registered_user
        response = client.post(
            "/auth/login",
            json={"email": user["email"], "password": user["password"]},
        )

        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        # JWT has 3 dot-separated segments
        assert len(body["access_token"].split(".")) == 3

    def test_login_wrong_password(self, registered_user):
        """Wrong password must return 401, not 403 or 404."""
        client, user = registered_user
        response = client.post(
            "/auth/login",
            json={"email": user["email"], "password": "WrongPassword1"},
        )

        assert response.status_code == 401
        # Detail must not hint which field was wrong (prevents enumeration)
        detail = response.json()["detail"].lower()
        assert "incorrect" in detail

    def test_login_unknown_email(self, client):
        """An email that was never registered must return 401."""
        response = client.post(
            "/auth/login",
            json={"email": "ghost@example.com", "password": "SomePassword1"},
        )

        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# GET /auth/me
# ═══════════════════════════════════════════════════════════════════════════════


class TestMe:

    def test_me_success(self, auth_token):
        """A valid token must return 200 with the authenticated user's data."""
        client, token = auth_token
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == VALID_USER["email"]
        assert body["username"] == VALID_USER["username"]
        assert "id" in body
        assert "created_at" in body

    def test_me_no_token(self, client):
        """Calling /auth/me without an Authorization header must return 403."""
        response = client.get("/auth/me")

        # HTTPBearer returns 403 when the header is entirely absent
        assert response.status_code == 403

    def test_me_invalid_token(self, client):
        """A tampered/invalid JWT must be rejected with 401."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
        )

        assert response.status_code == 401
