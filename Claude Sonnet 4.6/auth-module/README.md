# Auth Module — FastAPI + SQLite

A minimal, production-ready authentication service built with **FastAPI**, **SQLite**, **SQLAlchemy ORM**, **bcrypt**, and **JWT (HS256)**.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Setup & Run](#setup--run)
3. [API Reference](#api-reference)
4. [curl Examples](#curl-examples)
5. [Running Tests](#running-tests)
6. [Security Notes](#security-notes)
7. [Known Bugs & Security Issues](#known-bugs--security-issues)

---

## Project Structure

```
auth-module/
├── app/
│   ├── __init__.py         # Package marker
│   ├── main.py             # FastAPI app entry point, lifespan DB init
│   ├── database.py         # SQLAlchemy engine, SessionLocal, DeclarativeBase
│   ├── models.py           # ORM model: User
│   ├── schemas.py          # Pydantic v2 request / response schemas + validators
│   ├── auth.py             # bcrypt helpers, JWT create/decode, get_current_user dep
│   └── routes/
│       ├── __init__.py
│       └── auth.py         # POST /auth/register  POST /auth/login  GET /auth/me
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # In-memory SQLite fixture, get_db override, shared helpers
│   └── test_auth.py        # 11 tests across TestRegister / TestLogin / TestMe
├── requirements.txt
└── README.md
```

---

## Setup & Run

### Prerequisites

- Python 3.11+
- pip

> **Windows note:** Python installed via the Microsoft Store may not be on your `PATH` by default.
> Fix it for the current terminal session with:
> ```powershell
> $env:PATH += ";$env:LOCALAPPDATA\Microsoft\WindowsApps"
> ```

---

### Step 1 — Create and activate a virtual environment

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

> If you get an *"execution policy"* error on Windows, run once:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

---

### Step 3 — (Optional) Set a custom secret key

Create a `.env` file in the `auth-module/` directory:

```env
SECRET_KEY=your-super-long-random-string-minimum-32-chars
```

> The app falls back to a hardcoded default when `SECRET_KEY` is absent.
> **Never use the default key in production.**

---

### Step 4 — Start the development server

```bash
# Run from inside auth-module/
uvicorn app.main:app --reload
```

The SQLite database file (`auth.db`) is created automatically on first startup.

| URL | Description |
|-----|-------------|
| http://127.0.0.1:8000/docs | Swagger UI (interactive) |
| http://127.0.0.1:8000/redoc | ReDoc docs |
| http://127.0.0.1:8000/health | Health check |

---

## API Reference

### Endpoint Overview

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| `POST` | `/auth/register` | — | Create a new user account |
| `POST` | `/auth/login` | — | Exchange credentials for a JWT |
| `GET` | `/auth/me` | Bearer | Get the authenticated user's profile |
| `GET` | `/health` | — | Service health check |

---

### `POST /auth/register`

Register a new user account.

**Request body**

| Field | Type | Rules |
|-------|------|-------|
| `email` | string | Valid e-mail format, unique |
| `username` | string | 3–30 chars, `[a-zA-Z0-9_]` only, unique |
| `password` | string | Minimum 8 characters |

```json
{
  "email": "alice@example.com",
  "username": "alice",
  "password": "s3cur3P@ss"
}
```

**Responses**

| Status | When |
|--------|------|
| `201 Created` | Account created successfully |
| `409 Conflict` | Email or username already taken |
| `422 Unprocessable Entity` | Validation failed (bad email, weak password, etc.) |

**201 body**

```json
{
  "message": "Account created successfully",
  "user": {
    "id": 1,
    "email": "alice@example.com",
    "username": "alice",
    "created_at": "2026-02-20T10:00:00Z"
  }
}
```

---

### `POST /auth/login`

Authenticate with email + password and receive a JWT valid for **15 minutes**.

**Request body**

| Field | Type | Description |
|-------|------|-------------|
| `email` | string | Registered email address |
| `password` | string | Account password |

```json
{
  "email": "alice@example.com",
  "password": "s3cur3P@ss"
}
```

**Responses**

| Status | When |
|--------|------|
| `200 OK` | Credentials valid — token returned |
| `401 Unauthorized` | Email not found or wrong password |
| `422 Unprocessable Entity` | Malformed request body |

**200 body**

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

---

### `GET /auth/me`

Return the profile of the currently authenticated user.

**Headers**

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer <access_token>` |

**Responses**

| Status | When |
|--------|------|
| `200 OK` | Token valid — user returned |
| `401 Unauthorized` | Token expired, tampered, or payload invalid |
| `403 Forbidden` | `Authorization` header missing entirely |

**200 body**

```json
{
  "id": 1,
  "email": "alice@example.com",
  "username": "alice",
  "created_at": "2026-02-20T10:00:00Z"
}
```

---

## curl Examples

> Replace `<token>` with the `access_token` value returned by `/auth/login`.

### Register

```bash
# macOS / Linux
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","username":"alice","password":"s3cur3P@ss"}'
```

```powershell
# Windows PowerShell
curl -X POST http://127.0.0.1:8000/auth/register `
  -H "Content-Type: application/json" `
  -d '{"email":"alice@example.com","username":"alice","password":"s3cur3P@ss"}'
```

---

### Login

```bash
# macOS / Linux
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"s3cur3P@ss"}'
```

```powershell
# Windows PowerShell
curl -X POST http://127.0.0.1:8000/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email":"alice@example.com","password":"s3cur3P@ss"}'
```

---

### Get current user

```bash
# macOS / Linux
curl http://127.0.0.1:8000/auth/me \
  -H "Authorization: Bearer <token>"
```

```powershell
# Windows PowerShell
curl http://127.0.0.1:8000/auth/me `
  -H "Authorization: Bearer <token>"
```

---

## Running Tests

All tests use an **in-memory SQLite database** — no file is created on disk and each test is fully isolated.

### Run all tests

```bash
pytest -v
```

### Run a single class or test

```bash
# One class
pytest -v tests/test_auth.py::TestRegister

# One specific test
pytest -v tests/test_auth.py::TestLogin::test_login_wrong_password
```

### Run with coverage

```bash
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

### Test matrix

| # | Class | Test | Expected outcome |
|---|-------|------|-----------------|
| 1 | `TestRegister` | `test_register_success` | `201` — correct body, no password in response |
| 2 | `TestRegister` | `test_register_duplicate_email` | `409` |
| 3 | `TestRegister` | `test_register_duplicate_username` | `409` |
| 4 | `TestRegister` | `test_register_password_too_short` | `422` |
| 5 | `TestRegister` | `test_register_invalid_email` | `422` |
| 6 | `TestLogin` | `test_login_success` | `200` — valid 3-segment JWT |
| 7 | `TestLogin` | `test_login_wrong_password` | `401` |
| 8 | `TestLogin` | `test_login_unknown_email` | `401` |
| 9 | `TestMe` | `test_me_success` | `200` — email/username match registered user |
| 10 | `TestMe` | `test_me_no_token` | `403` |
| 11 | `TestMe` | `test_me_invalid_token` | `401` |

---

## Security Notes

### Password policy

- Minimum **8 characters** enforced by a Pydantic `field_validator`.
- Stored as a **bcrypt hash** with a per-user random salt (cost factor 12 by default).
- The plain-text password is **never logged, stored, or returned** in any response.
- Production recommendation: add complexity rules (uppercase + digit + special char) inside the existing `password_strength` validator in `schemas.py`.

### JWT storage (client-side)

Tokens returned by `/auth/login` must be stored securely on the client:

| Storage | Risk | Recommendation |
|---------|------|----------------|
| `localStorage` | Vulnerable to XSS | Avoid for sensitive apps |
| `sessionStorage` | Cleared on tab close, still XSS-accessible | Acceptable for short sessions |
| `HttpOnly` cookie | Not accessible via JS — XSS-safe | **Preferred** (needs CSRF protection) |
| In-memory (JS variable) | Lost on refresh | Good for SPAs with refresh-token flow |

### Rate limiting

This module has **no built-in rate limiting**. In production, protect `/auth/login` and `/auth/register` against brute-force attacks using one of:

- **[slowapi](https://github.com/laurents/slowapi)** — drop-in FastAPI rate limiter:
  ```bash
  pip install slowapi
  ```
  ```python
  from slowapi import Limiter
  from slowapi.util import get_remote_address
  limiter = Limiter(key_func=get_remote_address)

  @router.post("/login")
  @limiter.limit("5/minute")
  def login(request: Request, ...):
      ...
  ```
- A reverse-proxy rule (nginx `limit_req`, AWS WAF, Cloudflare).

---

## Known Bugs & Security Issues

> Each item includes its **severity** and a **verification step** you can run against the running server.

---

### 1. Hardcoded fallback `SECRET_KEY`

**Severity:** Critical

`app/auth.py` falls back to a literal string when `SECRET_KEY` is absent from the environment. Any attacker who reads the source can forge valid JWTs indefinitely.

**Verify:**
```bash
# Start server without .env, then paste the token at https://jwt.io and set the
# secret to: "change-me-in-production-use-a-long-random-string"
# The signature will verify successfully — proving the key is known.
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"s3cur3P@ss"}'
```

**Fix:** Raise a `RuntimeError` at startup if `SECRET_KEY` is absent or shorter than 32 characters.

---

### 2. No rate limiting on `/auth/login`

**Severity:** High

Unlimited login attempts allow brute-force or credential-stuffing attacks with no consequence.

**Verify:**
```bash
# All 100 requests return 401 — none are blocked or slowed
for i in $(seq 1 100); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"alice@example.com\",\"password\":\"Wrong$i\"}"
done
```

**Fix:** Add `slowapi` with `@limiter.limit("5/minute")` on the login and register routes.

---

### 3. No token revocation / blacklisting

**Severity:** High

A JWT remains valid for its full 15-minute window after issuance. There is no logout endpoint and no way to invalidate a stolen token before it expires.

**Verify:**
```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"s3cur3P@ss"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Token still works even after a conceptual "logout"
curl -s http://127.0.0.1:8000/auth/me -H "Authorization: Bearer $TOKEN"
```

**Fix:** Add a `jti` (JWT ID) claim and check it against a Redis revocation set on every request, or implement a short-lived token + refresh-token pattern.

---

### 4. Passwords lack complexity rules

**Severity:** Medium

The validator only enforces minimum length. Trivially guessable passwords like `"password"` or `"12345678"` are accepted.

**Verify:**
```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"bob@example.com","username":"bob","password":"password"}'
# Returns 201 — weak password accepted
```

**Fix:** Extend `password_strength` in `schemas.py` to require at least one uppercase letter, one digit, and one special character, or use the `zxcvbn` library for entropy-based scoring.

---

### 5. SQLite is unsuitable for concurrent production use

**Severity:** Medium

SQLite serialises all writes with a file lock. Under concurrent load this causes timeouts. It also stores all data in a single, unprotected file on disk.

**Verify:**
```bash
# Send 50 concurrent register requests — observe lock errors or timeouts
ab -n 200 -c 50 -T application/json \
   -p register.json http://127.0.0.1:8000/auth/register
```

**Fix:** Replace `sqlite:///./auth.db` in `database.py` with a PostgreSQL or MySQL connection string for production.

---

### 6. No HTTPS enforcement

**Severity:** Medium

Passwords and bearer tokens are transmitted in plain text when the server is run without TLS. Any on-path observer can capture them.

**Verify:**
```bash
# Capture traffic on the loopback interface while making a login request
tcpdump -i lo -A 'tcp port 8000' &
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"s3cur3P@ss"}'
# The password appears in plain text in the tcpdump output
```

**Fix:** Deploy behind a TLS-terminating reverse proxy (nginx, Caddy) or pass `--ssl-keyfile` and `--ssl-certfile` to `uvicorn`.

---

### 7. `created_at` column can be `None` in edge cases

**Severity:** Low

`created_at` uses only `server_default=func.now()`, which is evaluated by SQLite. If the ORM returns the row before the DB default is reflected (possible with some async drivers or test double scenarios), the field is `None` and Pydantic raises a serialisation error.

**Verify:**
```bash
sqlite3 auth.db "SELECT id, email, created_at FROM users;"
# If the created_at column is empty/NULL the server default was not applied
```

**Fix:** Add `default=datetime.now(timezone.utc)` at the Python/ORM layer alongside `server_default`, so the value is always set regardless of DB behaviour.

---

### 8. Internal error details exposed in debug mode

**Severity:** Low

Running with `--reload` (development mode) can cause Starlette to include internal tracebacks — file paths, library versions, and stack frames — in 500-level error responses visible to clients.

**Verify:**
```bash
# Send a deliberately malformed body to trigger an unhandled exception path
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{invalid json here}'
# Inspect whether the 422 detail contains internal framework context
```

**Fix:** Run `uvicorn app.main:app` (no `--reload`) in production and register a global exception handler:
```python
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```
