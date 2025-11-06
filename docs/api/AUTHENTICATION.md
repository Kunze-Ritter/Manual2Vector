# Authentication & Authorization Guide

The KRAI Processing Pipeline exposes a production-ready authentication stack built on FastAPI. This guide explains how to configure environment variables, understand roles & permissions, work with the authentication API, and integrate permission checks into your own endpoints.

---

## Table of Contents

1. [Overview](#overview)
2. [Environment Setup](#environment-setup)
3. [Roles & Permissions](#roles--permissions)
4. [Token Flow](#token-flow)
5. [API Endpoints](#api-endpoints)
6. [Middleware & Dependencies](#middleware--dependencies)
7. [Token Blacklisting & Logout](#token-blacklisting--logout)
8. [RBAC in Practice](#rbac-in-practice)
9. [Security Best Practices](#security-best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Reference Links](#reference-links)

---

## Overview

The authentication system provides:

- **JWT authentication** with RS256 signing and refresh tokens
- **Role-based access control (RBAC)** with granular permissions
- **Token blacklisting** for logout and breach response
- **Rate limiting & account lockout** to deter brute-force attacks
- **Admin bootstrap** via environment variables and startup checks

Key components:

- `backend/api/routes/auth.py`: FastAPI router with auth endpoints
- `backend/services/auth_service.py`: Business logic for users, tokens, permissions
- `backend/api/middleware/auth_middleware.py`: Permission guards and middleware
- `database/migrations/02_extend_users_table.sql`: Schema for users, tokens, constraints
- `database/migrations/04_adjust_users_checks.sql`: Ensures consistent enum constraints across environments

---

## Environment Setup

Copy `.env.auth.example` to `.env.auth` and fill in the secrets. Important variables:

| Variable | Description |
|----------|-------------|
| `JWT_PRIVATE_KEY` / `JWT_PUBLIC_KEY` | Base64-encoded PKCS8 RSA keys (2048-bit recommended) |
| `JWT_ALGORITHM` | Signing algorithm (default `RS256`) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime |
| `MAX_LOGIN_ATTEMPTS`, `ACCOUNT_LOCKOUT_DURATION_MINUTES` | Brute-force protection |
| `PASSWORD_*` | Password policy toggles |
| `DEFAULT_ADMIN_*` | Bootstrap admin created on startup |

Also ensure `.env.database`, `.env.storage`, `.env.ai`, `.env.pipeline`, and `.env.external` are configured per [docs/setup/ENV_STRUCTURE.md](../setup/ENV_STRUCTURE.md). The FastAPI app loads all of them during startup.

---

## Roles & Permissions

Roles are stored in `krai_users.users.role` and constrained via database checks. The default role set:

| Role | Description |
|------|-------------|
| `admin` | Full access to management & configuration |
| `editor` | Document upload, pipeline management, monitoring |
| `viewer` | Read-only access to documents & status |
| `user` | Limited self-service capabilities |
| `api_user` | Service account for machine-to-machine integrations |

Permissions are stored separately (see `AuthService.assign_permission`). Common permissions:

- `documents:write` – Upload & reprocess documents
- `documents:read` – View processing status and document info
- `monitoring:read` – Access logs, metrics, and monitoring dashboards
- Additional permissions can be added per product requirements.

`database/migrations/04_adjust_users_checks.sql` guarantees all environments accept `api_user` and `deleted` values.

---

## Token Flow

1. **Login**: `POST /api/v1/auth/login` with username/password
   - Returns access token (short-lived) and optional refresh token
2. **Refresh**: `POST /api/v1/auth/refresh` with refresh token
   - Returns new access/refresh pair
3. **Protected Requests**: Include `Authorization: Bearer <access_token>` header
   - Middleware validates token, checks blacklists, role, status, and permissions
4. **Logout**: `POST /api/v1/auth/logout`
   - Blacklists the access token and associated refresh token

Access tokens embed:

- `sub` (user ID)
- `email`
- `role`
- `permissions` fetched on demand
- `token_type`
- `exp` (expiry)
- `jti` (JWT ID)

---

## API Endpoints

Base prefix: `/api/v1/auth`

### Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
        "email": "user@example.com",
        "username": "user123",
        "password": "TestPass123!",
        "first_name": "Test",
        "last_name": "User"
      }'
```

- Creates a new user with default role `user`
- Returns masked user data and ID

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{ "username": "user@example.com", "password": "TestPass123!" }'
```

Response:

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": { "id": "...", "email": "...", "role": "viewer" }
  }
}
```

### Refresh Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{ "refresh_token": "<token>" }'
```

Returns new tokens when the refresh token is valid and not blacklisted.

### Logout

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access_token>"
```

- Blacklists the access token immediately
- Extracts refresh token `jti` and blacklists it as well

### Admin & User Management

- `GET /api/v1/auth/users` – List users (`require_admin`)
- `POST /api/v1/auth/users` – Create user
- `PATCH /api/v1/auth/users/{user_id}` – Update user details, roles, permissions
- `DELETE /api/v1/auth/users/{user_id}` – Soft delete (status `deleted`)
- `POST /api/v1/auth/users/{user_id}/permissions` – Grant permissions

See the router for full list and response schemas.

---

## Middleware & Dependencies

The middleware module `backend/api/middleware/auth_middleware.py` exposes helpers:

- `AuthMiddleware`: core validator used in `/docs`, `/redoc`
- `get_current_user(required_permissions=[...])`: dependency returning user context
- `require_permission("documents:write")`: convenience wrapper
- `require_role([UserRole.ADMIN])` and `require_admin`
- `public()` decorator for documentation-only marking

Usage example:

```python
from fastapi import APIRouter, Depends
from backend.api.middleware.auth_middleware import require_permission

router = APIRouter()

@router.post("/documents", dependencies=[Depends(require_permission("documents:write"))])
async def create_document(payload: dict):
    ...
```

The main FastAPI app applies these dependencies directly to endpoints like `/upload`, `/status`, `/logs`, ensuring that non-admin actions remain guarded by RBAC.

---

## Token Blacklisting & Logout

Tables involved (defined in migrations):

- `krai_users.user_tokens` – Tracks issued refresh tokens, metadata, and revocation
- `krai_users.token_blacklist` – Stores blacklisted JWT IDs with expiry timestamps

`AuthService.blacklist_token()` and `AuthService.is_token_blacklisted()` govern the lifecycle. The `logout()` endpoint reads the `exp` claim and stores it with `timezone.utc` to ensure comparison consistency.

When a token is blacklisted, any subsequent request with that token returns `401 Token has been revoked`.

---

## RBAC in Practice

Endpoints protected in `backend/api/app.py`:

| Endpoint | Permission |
|----------|------------|
| `POST /upload` | `documents:write` |
| `POST /upload/directory` | `documents:write` |
| `GET /status/{id}` | `documents:read` |
| `GET /status/pipeline` | `documents:read` |
| `GET /logs/{id}` | `monitoring:read` |
| `GET /stages/statistics` | `monitoring:read` |
| `GET /monitoring/system` | `monitoring:read` |

Use `AuthService.assign_permission(user_id, permission)` to grant arbitrary combinations. Admins typically hold `documents:write` and `monitoring:read` by default.

---

## Security Best Practices

1. **Rotate keys** whenever exposure is suspected; update `.env.auth` and restart the service.
2. **Keep tokens short-lived**; default access tokens expire in 60 minutes.
3. **Enable rate limiting and lockouts** (already configured via env vars).
4. **Force HTTPS** in production to protect tokens in transit.
5. **Use refresh tokens sparingly** for long-lived sessions and rotate them on each refresh.
6. **Audit logs** regularly; integrate with SIEM for suspicious activity.
7. **Validate origins** through CORS configuration in `backend/api/app.py`.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Token has expired` | Clock skew or long inactivity | Refresh token or login again |
| `Token has been revoked` | Logout or manual blacklist | Obtain a new token |
| `Invalid authentication credentials` | Missing/invalid `Authorization` header | Include `Bearer <token>` |
| `Insufficient permissions` | Permission missing | Assign permission via admin API |
| `Invalid or expired token` | JWT signature mismatch or altered token | Request new token |
| `User account is not active` | Status not `active` | Reactivate user or check statuses |

Check application logs (`logger` in `auth_service.py` / `auth_middleware.py`) for detailed error output.

---

## Reference Links

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)
- [Supabase Policies](https://supabase.com/docs/guides/auth)
- [OAuth 2.0 Threats & Mitigations](https://datatracker.ietf.org/doc/html/rfc6819)
- [JSON Web Token RFC](https://www.rfc-editor.org/rfc/rfc7519)
- Project Files:
  - `backend/api/routes/auth.py`
  - `backend/api/app.py`
  - `backend/api/middleware/auth_middleware.py`
  - `backend/services/auth_service.py`
  - `database/migrations/02_extend_users_table.sql`
  - `database/migrations/04_adjust_users_checks.sql`

---

**Last Updated:** 2025-10-31
