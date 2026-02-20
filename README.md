# Comparative Evaluation
## GenAI Tools: Claude Sonnet 4.6 vs Gemini 2.0 Flash

**Task:** Build a Python FastAPI authentication module with SQLite, bcrypt, JWT (HS256), input validation, and tests.  
**Date:** February 20, 2026

---

## 1. Output Quality

### 1.1 Project Structure

| Aspect | Claude Sonnet 4.6 | Gemini 2.0 Flash |
|--------|-------------------|-----------------|
| Folder layout | Dedicated `routes/`, `tests/` packages with `__init__.py` | All logic flat inside `app/`, single `tests/` file |
| Separation of concerns | Routes isolated in `app/routes/auth.py`; auth utilities in `app/auth.py` | All route handlers defined directly in `main.py` alongside business logic |
| Test organisation | `conftest.py` + `test_auth.py` with class-based test groups | Single `test_bug.py` — procedural script, no test classes |

Claude produced a layered, navigable layout. Gemini produced a flat, monolithic arrangement suitable only for a prototype.

---

### 1.2 SQLAlchemy ORM

| Aspect | Claude Sonnet 4.6 | Gemini 2.0 Flash |
|--------|-------------------|-----------------|
| Base class | `DeclarativeBase` (SQLAlchemy 2.0, current) | `declarative_base()` from `sqlalchemy.ext.declarative` (deprecated since SQLAlchemy 1.4, removed path in 2.0) |
| Session lifecycle | `get_db()` dependency injected per route; tables created via `asynccontextmanager` lifespan | `get_db()` present but tables created at module import time (`models.Base.metadata.create_all(bind=engine)` at top of `main.py`) |
| `created_at` field | `DateTime(timezone=True)` with `server_default=func.now()` | Not present |

Claude used the current SQLAlchemy 2.0 API. Gemini used a deprecated import that raises a deprecation warning in any project using SQLAlchemy ≥ 2.0.

---

### 1.3 Password Hashing

| Aspect | Claude Sonnet 4.6 | Gemini 2.0 Flash |
|--------|-------------------|-----------------|
| Library | `bcrypt` (direct, as specified in requirements) | `passlib` with `CryptContext(schemes=["pbkdf2_sha256"])` |
| Algorithm | **bcrypt** — as required | **PBKDF2-SHA256** — does **not** meet the stated requirement |
| Salt handling | `bcrypt.gensalt()` per call — explicit | Managed internally by passlib |

Gemini failed to satisfy the explicit bcrypt requirement, substituting a different algorithm without acknowledging the deviation.

---

### 1.4 JWT Implementation

| Aspect | Claude Sonnet 4.6 | Gemini 2.0 Flash |
|--------|-------------------|-----------------|
| `sub` claim value | User **ID** (integer, opaque) | **Username** (string, exposes internal data) |
| Token decode location | Isolated `decode_access_token()` in `auth.py` | Inline inside `get_current_user()` in `main.py` |
| Secret key source | `os.getenv("SECRET_KEY", fallback)` + `.env` file via `python-dotenv` | Hardcoded literal: `SECRET_KEY = "SUPER_SECRET_KEY"` — no env var |
| Timestamp API | `datetime.now(timezone.utc)` (correct, Python 3.12+ safe) | `datetime.utcnow()` (deprecated since Python 3.12) |

Gemini hardcoded a trivially guessable secret key directly in source. This is a critical security defect, not just a code smell.

---

### 1.5 Pydantic Schemas

| Aspect | Claude Sonnet 4.6 | Gemini 2.0 Flash |
|--------|-------------------|-----------------|
| Pydantic API version | v2 — `field_validator`, `model_config = {"from_attributes": True}`, `model_validate()` | Mixed — `class Config: from_attributes = True` (v1 style, works in v2 but deprecated) |
| Input validation | `username` length (3–30), alphanumeric regex, password min-length all enforced via `field_validator` | No password strength validation; no username format rules |
| Response shape | Separate `RegisterResponse` (wraps user + message) and `UserResponse` | `User` schema doubles as both create input base and response |

Claude applied meaningful, documented constraints. Gemini applied no constraints beyond type checking.

---

### 1.6 HTTP Status Codes

| Endpoint | Claude Sonnet 4.6 | Gemini 2.0 Flash | Correct code |
|----------|-------------------|-----------------|:------------:|
| Register success | `201 Created` | `201 Created` | ✓ |
| Duplicate email/username | `409 Conflict` | `400 Bad Request` | 409 |
| Invalid input | `422 Unprocessable Entity` (Pydantic) | `422` (Pydantic only) | 422 |
| Wrong credentials | `401 Unauthorized` | `401 Unauthorized` | ✓ |
| Missing token | `403 Forbidden` | `403 Forbidden` | ✓ |

Gemini used `400` for duplicate registration instead of the semantically correct `409 Conflict`.

---

### 1.7 Security Practices

| Practice | Claude Sonnet 4.6 | Gemini 2.0 Flash |
|----------|-------------------|-----------------|
| User enumeration prevention | Single `"Incorrect email or password"` message for both bad email and bad password | Separate message `"Incorrect username or password"` — acceptable but exposes the login field is username |
| Secret key in source | Never — env var only | **Yes — hardcoded** `"SUPER_SECRET_KEY"` |
| Login body type | JSON (`LoginRequest` schema) | `OAuth2PasswordRequestForm` → form-encoded (different wire format than the task description implied) |
| `python-dotenv` | Included | Not included |

---

### 1.8 Test Quality

| Aspect | Claude Sonnet 4.6 | Gemini 2.0 Flash |
|--------|-------------------|-----------------|
| Framework | `pytest` with `httpx` | Script-based (`python test_bug.py`) |
| Isolation | Each test gets a **fresh in-memory SQLite DB** via `StaticPool` + `dependency_overrides` | Single shared `TestClient` — state bleeds between runs |
| Number of tests | 11 (5 register, 3 login, 3 me) | 1 (single procedural flow) |
| Failure cases covered | Duplicate email, duplicate username, short password, bad email format, wrong password, unknown email, no token, invalid token | None — only the happy path is verified |
| Assertion style | `assert response.status_code == X` + field checks | `print()` statements; no assertions, exit code always 0 |
| Coverage | Register, Login, Me — happy and failure paths | Login + Me — happy path only |

Gemini's test cannot fail. Every run exits 0 regardless of what the server returns, because there are no `assert` statements.

---

## 2. Prompt Sensitivity

### 2.1 Adherence to Explicit Requirements

| Requirement stated in prompt | Claude Sonnet 4.6 | Gemini 2.0 Flash |
|------------------------------|:-----------------:|:----------------:|
| `POST /auth/register` | ✓ | ✓ |
| `POST /auth/login` | ✓ | ✓ |
| `GET /auth/me` | ✓ | ✓ |
| Store users in SQLite | ✓ | ✓ |
| **Hash passwords with bcrypt** | ✓ | ✗ (uses PBKDF2) |
| JWT HS256 with 15-min expiry | ✓ | ✓ |
| Input validation | ✓ | Partial (type only) |
| Correct HTTP status codes | ✓ | Partial (400 vs 409) |
| Project folder structure | ✓ | Minimal |
| Full code for each file | ✓ | ✓ |
| `requirements.txt` | ✓ (pinned versions) | ✓ (unpinned) |
| Steps to run locally | ✓ (detailed) | ✓  (minimal) |

Claude satisfied 12/12 requirements. Gemini satisfied 9/12 — it silently substituted a different password algorithm, omitted meaningful validation, and used approximate status codes.

### 2.2 Response to Follow-up Prompts

Claude responded incrementally across multiple prompts, preserving all prior work while adding:
- Modern ORM refactor when asked
- Full pytest suite with isolated fixtures when asked
- Controlled bug introduction and step-by-step debugging walkthrough when asked
- Comprehensive README rewrite with security analysis when asked

Gemini was not iteratively prompted in this session — only a single generation was captured. This limits direct comparison of multi-turn behaviour, but the single-pass output already shows lower baseline completeness.

---

## 3. Technical Limitations

### Claude Sonnet 4.6

| Limitation | Detail |
|------------|--------|
| Default secret key fallback | Ships with a hardcoded fallback value (acknowledged in README and security notes, but present) |
| No rate limiting | Acknowledged and documented as a known issue, but not implemented |
| SQLite for production | Correctly noted as unsuitable; not remediated |
| No token revocation | Acknowledged; refresh-token flow not implemented |
| Password policy | Minimum length only; no complexity enforcement |

All limitations were explicitly identified, documented, and given concrete fix recommendations.

### Gemini 2.0 Flash

| Limitation | Detail |
|------------|--------|
| Wrong hashing algorithm | `pbkdf2_sha256` used instead of `bcrypt` — silent deviation from a stated requirement |
| Hardcoded secret key | `"SUPER_SECRET_KEY"` committed to source; no env-var override |
| Deprecated `datetime.utcnow()` | Raises `DeprecationWarning` in Python 3.12 and will break in a future version |
| Deprecated `declarative_base` import | `sqlalchemy.ext.declarative` removed path in SQLAlchemy 2.x+ |
| No real tests | `test_bug.py` uses print-driven assertions — always exits 0 |
| Unpinned dependencies | `requirements.txt` has no version pins; reproducible builds not guaranteed |
| OAuth2 form login | `/auth/login` requires `application/x-www-form-urlencoded`, not `application/json` — inconsistent with the other JSON endpoints |
| No `.env` support | Secret key cannot be overridden without editing source code |

Most Gemini limitations are **silent** — no documentation, no warning, no suggestion to fix.

---

## 4. Performance Metrics

> Note: these are code-quality and generation-quality metrics, not runtime benchmarks. Runtime performance of both FastAPI apps is effectively identical for a SQLite-backed auth service at low load.

### 4.1 Code Volume and Completeness

| Metric | Claude Sonnet 4.6 | Gemini 2.0 Flash |
|--------|:-----------------:|:----------------:|
| Source files generated | 9 | 7 |
| Lines of application code (approx.) | ~230 | ~130 |
| Lines of test code | ~160 (conftest + test file) | ~55 (single script) |
| README length | ~300 lines (setup, API reference, curl, security, bugs) | ~35 lines |
| requirements.txt pinned | Yes | No |

### 4.2 Correctness on First Pass

| Check | Claude Sonnet 4.6 | Gemini 2.0 Flash |
|-------|:-----------------:|:----------------:|
| Server starts without modification | ✓ | ✓ |
| All explicit requirements met | ✓ | ✗ (bcrypt, validation, status codes) |
| Tests runnable with `pytest -v` | ✓ (11 passed) | N/A — not a pytest suite |
| Tests provide real pass/fail signal | ✓ | ✗ (always exits 0) |
| No deprecated API usage | ✓ | ✗ (`datetime.utcnow`, `declarative_base`) |
| No hardcoded secrets | ✓ | ✗ |

### 4.3 Documentation Quality

| Aspect | Claude Sonnet 4.6 | Gemini 2.0 Flash |
|--------|:-----------------:|:----------------:|
| Setup instructions | Step-by-step with Windows-specific notes | 3-line pip + uvicorn |
| API reference table | Full table + per-endpoint request/response schemas | Feature list only |
| curl examples | Both bash and PowerShell variants | None |
| Security notes | Dedicated section (password policy, JWT storage, rate limiting) | None |
| Known issues | 8 documented bugs with severity + verification commands | None |

---

## 5. Summary

| Criterion | Claude Sonnet 4.6 | Gemini 2.0 Flash |
|-----------|:-----------------:|:----------------:|
| **Output Quality** | Production-grade structure, modern APIs, no silent deviations | Functional prototype, silent requirement deviations, deprecated APIs |
| **Prompt Sensitivity** | Accurately followed all 12 requirements; iterated faithfully on follow-ups | Missed 3 explicit requirements silently; no iteration tested |
| **Technical Limitations** | Present but all documented with fixes | Present and undocumented; some are security-critical |
| **Performance (correctness, completeness)** | 11/11 tests pass; full API reference; security analysis included | 0 real assertions; minimal docs; hardcoded secret |

### Overall Assessment

**Claude Sonnet 4.6** produced a solution that is deployable as-is (with the acknowledged caveats around rate limiting and secret key), follows current library best-practices, and documents its own shortcomings clearly.

**Gemini 2.0 Flash** produced a working proof-of-concept that correctly assembles the required endpoints, but deviates from the stated bcrypt requirement, hardcodes a secret key, uses deprecated library APIs, and provides no real test coverage. It is suitable as a starting scaffold requiring significant revision before production use.

For tasks demanding strict requirement adherence, security awareness, and production-readiness, **Claude Sonnet 4.6 performed materially better on this workload**.
