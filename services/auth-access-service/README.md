# TCS Intelligent Microservice Factory — Auth & Access Control Service

Dedicated microservice for enterprise authentication, strictly 2-role RBAC (`ADMIN` and `DEVELOPER`), and client account isolation.

- **Port**: `8001`
- **Swagger Documentation**: `http://localhost:8001/docs`
- **Constitution Version**: `1.2.0`

## Features

1. **Authentication & JWT Issuance**: Fast and secure token issuance using PyJWT (HS256) and bcrypt with 12 salt rounds.
2. **Zero Preloaded Data**: Zero credentials or seed accounts hardcoded. Clean startup via idempotent `POST /api/v1/auth/setup-admin`.
3. **Strict 2-Role RBAC**: Exactly two roles supported (`ADMIN` and `DEVELOPER`). Admin self-deactivation protection.
4. **Client Isolation**: Developers only have access to their assigned client accounts (e.g. `bcp`, `retail-corp`).
5. **Inter-Service Verification**: Fast token and permission verification via `POST /api/v1/auth/verify` (< 20ms).

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `PORT` | HTTP listen port | `8001` |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./auth_factory_local.db` |
| `JWT_SECRET_KEY` | Cryptographic secret for signing tokens | (Configurable dev secret) |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes | `480` (8 hours) |

## Quickstart

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --port 8001 --reload
```

## Running Tests

```bash
pytest -v
```

