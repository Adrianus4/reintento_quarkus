# Phase 0 Research: Spec 001 — auth-access-service

## 1. Technical Decisions & Trade-Offs

### 1.1 Language & Framework
- **Decision**: Python 3.11+ with **FastAPI** (`0.111+`) and **Uvicorn** running on port `8001`.
- **Rationale**: FastAPI provides native OpenAPI/Swagger documentation generation at `/docs`, automatic Pydantic v2 validation, high throughput, and seamless integration with the distributed microservices ecosystem of the TCS Factory.
- **Alternatives Considered**:
  - *Quarkus with Java*: While generated microservices are Java/Quarkus, the factory control plane microservices (LangGraph AI orchestrators, governance, verifier wrappers) leverage the Python AI ecosystem natively. Having FastAPI for `auth-access-service` allows sharing Pydantic schemas, JWT decoding utilities, and authentication middleware directly with `client-governance-service` and `ai-orchestrator-service`.

### 1.2 Cryptographic Security & Password Hashing
- **Decision**: Use `bcrypt` (or `argon2-cffi` via `passlib[bcrypt]`) with salt rounds = 12.
- **Rationale**: Bcrypt is battle-tested, resistant to GPU attacks, deterministic, and natively supported across all deployment platforms (Windows, Linux, Azure Container Apps) without complex compilation dependencies.
- **Storage**: Passwords are never stored in plain text. Stored as `hashed_password` string ($2b$12$...).

### 1.3 JWT Architecture & Inter-Service Token Verification
- **Decision**: `PyJWT` (or `python-jose`) using algorithm `HS256` for the MVP, parameterized via `JWT_SECRET_KEY` and `JWT_ALGORITHM`.
- **Payload Schema**:
  ```json
  {
    "sub": "user-uuid",
    "email": "collaborator@tcs.com",
    "role": "DEVELOPER",
    "exp": 1729500000,
    "iat": 1729464000
  }
  ```
- **Inter-service Verification (`POST /api/v1/auth/verify`)**:
  - The endpoint decodes the token, checks the signature and expiration, retrieves the user's current status (`is_active`) and assigned client codes, and returns:
    ```json
    {
      "valid": true,
      "user_id": "user-uuid",
      "email": "collaborator@tcs.com",
      "role": "DEVELOPER",
      "assigned_clients": ["bcp", "retail-core"],
      "reason": null
    }
    ```
  - If invalid, expired, or deactivated, returns `{ "valid": false, "reason": "TOKEN_EXPIRED" | "USER_INACTIVE" | "INVALID_SIGNATURE" }` with HTTP 200 (so consuming microservices can cleanly handle business logic).

### 1.4 Persistence & Database
- **Decision**: **SQLAlchemy 2.0** ORM.
- **Driver**: SQLite (`auth_factory_local.db`) for zero-dependency local development, with dynamic switch to PostgreSQL via `DATABASE_URL` environment variable.
- **Session Pattern**: Dependency injection `get_db` yielding session with transaction rollback on error.
- **Schema Management**: Auto-migration / DDL initialization on startup via `Base.metadata.create_all(bind=engine)`.

### 1.5 Access Control (RBAC): Strictly 2 Corporate Roles
- **Roles**:
  1. `ADMIN`: Can manage users, assign clients, view audit logs, access all endpoints.
  2. `DEVELOPER`: Can authenticate, view own profile (`/api/v1/auth/me`), view own assigned clients (`/api/v1/auth/me/clients`), and change own password. Forbidden from user management (`/api/v1/users`).
- **Zero Preloaded Data & Clean Bootstrap**:
  - Database starts completely empty (Zero preloaded fake data).
  - Dedicated endpoint `POST /api/v1/auth/setup-admin` allows creating the initial Administrator. Once at least one user exists in the database, this endpoint permanently disables itself and responds `409 Conflict: Setup already completed`.

---

## 2. Directory Layout Decision

The service will reside in `services/auth-access-service/`:

```text
services/auth-access-service/
├── app/
│   ├── api/
│   │   ├── deps.py             # Auth dependencies, get_current_user, require_role(ADMIN)
│   │   └── v1/
│   │       ├── api.py          # APIRouter aggregator
│   │       ├── auth.py         # /login, /setup-admin, /verify, /me
│   │       └── users.py        # /users (CRUD, assign clients)
│   ├── core/
│   │   ├── config.py           # Pydantic BaseSettings (PORT=8001, SECRET_KEY, DB_URL)
│   │   ├── security.py         # verify_password, get_password_hash, create_access_token
│   │   └── database.py         # SQLAlchemy engine, sessionmaker, Base
│   ├── models/
│   │   ├── user.py             # User and UserRole enum
│   │   ├── assignment.py       # UserClientAssignment
│   │   └── audit.py            # AuditLoginLog
│   ├── schemas/
│   │   ├── auth.py             # LoginRequest, TokenResponse, TokenVerifyResponse
│   │   └── user.py             # UserCreate, UserUpdate, UserResponse, ClientAssignRequest
│   └── main.py                 # FastAPI application definition, CORS, exception handlers
├── tests/
│   ├── conftest.py             # Pytest fixtures (test DB in memory, test client)
│   ├── test_auth.py            # Login, setup-admin, token verification tests
│   ├── test_users.py           # User management & RBAC tests (ADMIN vs DEVELOPER)
│   └── test_client_access.py   # Client isolation and assignment tests
├── requirements.txt            # Explicit frozen dependencies
├── Dockerfile                  # Containerization for Azure Container Apps
└── README.md                   # Operational guide & API documentation
```

---

## 3. Performance & Security Best Practices
1. **Timing Attack Mitigation**: Credential checks use constant-time string comparisons.
2. **Audit Logging**: All login attempts (success and failure) record client IP, attempted email, and timestamp without logging plain passwords.
3. **Admin Self-Deactivation Guard**: Logic prevents an Admin from deleting or deactivating themselves if they are the sole active Admin.

