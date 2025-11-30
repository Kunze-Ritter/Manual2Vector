# KRAI Security Reference

## 1. Overview

KRAI enforces multiple defensive layers to protect the processing pipeline in production:

1. **Centralized security configuration** via `config/security_config.py` (env-driven).
2. **Rate limiting** with SlowAPI (Redis storage optional) for every router class.
3. **Request validation middleware** for payload size, file uploads, and input sanitization.
4. **Security headers + CORS** tuned through environment variables with safe defaults.
5. **API key management** (creation, rotation, revocation) for service-to-service access.
6. **RBAC** using JWT claims + FastAPI dependencies (`require_permission`).

Admins should review this document before deploying to staging/production.

## 2. Configuration Matrix

| Category            | Key Env Vars / Files                                        | Notes |
|---------------------|--------------------------------------------------------------|-------|
| Rate limiting       | `RATE_LIMIT_*`, `REDIS_URL`, `config/security_config.py`     | Select per-endpoint policies (auth/upload/search/standard/health). |
| Request validation  | `MAX_REQUEST_SIZE_MB`, `MAX_FILE_SIZE_MB`, `ALLOWED_FILE_TYPES` | Reject oversized or disallowed uploads before hitting business logic. |
| Timeouts            | `REQUEST_TIMEOUT_SECONDS`, `UPLOAD_TIMEOUT_SECONDS`          | Mirror Uvicorn settings for consistent client behaviour. |
| Security headers    | `CSP_POLICY`, `HSTS_*`                                       | CSP defaults to self-only execution; adjust carefully. |
| CORS                | `CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_METHODS`, etc.           | Use comma-separated origins in `.env`. |
| API keys            | `API_KEY_ROTATION_*`                                         | Controls rotation cadence + grace period. |

> 🔐 All variables live in `.env` / `.env.example`. Update those files and re-run services after changes.

## 3. Rate Limiting Profiles

SlowAPI limiter (`backend/api/middleware/rate_limit_middleware.py`) exposes helper functions consumed by routers. Mapping:

| Profile               | Default Budget | Usage Examples |
|-----------------------|----------------|----------------|
| `rate_limit_auth`     | `5/minute`      | `/api/v1/auth/*` routes. |
| `rate_limit_upload`   | `10/hour`       | Document/Video creation, `/upload`, and enrichment endpoints. |
| `rate_limit_search`   | `60/minute`     | Document/Product/ErrorCode/Video listings + filter endpoints. |
| `rate_limit_standard` | `100/minute`    | CRUD operations, API keys, status endpoints. |
| `rate_limit_health`   | `300/minute`    | `/health` and light telemetry. |

Set `RATE_LIMIT_STORAGE=redis` with `REDIS_URL` for distributed deployments; fallback is per-process memory store.

## 4. Request Validation & Sanitization

`RequestValidationMiddleware` enforces:

1. Max request body size (rejects payloads once read limit exceeded).
2. File uploads: extension + MIME detection (python-magic fallback) and hash validation.
3. Input sanitization: SQL/XSS pattern detection; sanitized search strings.

Complementary Pydantic validators live in `backend/models/validators.py` and are reused by document/product/error-code/video/api-key models.

## 5. Security Headers & CORS

FastAPI middleware applies:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy` from `CSP_POLICY`
- HSTS (if HTTPS) with preload/subdomain toggles
- Referrer, Permissions, COEP/COOP/CORP defaults for modern browser isolation

Edit `.env` to whitelist web clients under `CORS_ALLOWED_ORIGINS`. Avoid `*` in production; use explicit scheme+host entries.

## 6. API Key Management

### 6.1 Schema

Migration `database/migrations/201_add_api_keys_table.sql` provisions `krai_system.api_keys` with:

| Column | Purpose |
| --- | --- |
| `id`, `user_id` | UUID identifiers referencing `krai_core.users` |
| `name`, `key_hash` | Friendly label + SHA-256 hash of the secret (unique) |
| `permissions` | JSONB scopes enforced at request time |
| `version` | Incremented automatically on rotation to support grace periods |
| `created_at`, `updated_at`, `last_used_at` | Lifecycle + validation timestamps (trigger keeps `updated_at` fresh) |
| `expires_at` | Hard expiry aligned with `API_KEY_ROTATION_DAYS` |
| `revoked`, `revoked_at`, `revoked_by` | Manual revocation metadata w/ constraint to keep timestamps in sync |
| `metadata` | JSONB for client fingerprints / notes |

Indexes on `key_hash`, `user_id`, `expires_at`, and active keys plus CHECK constraints (`expires_at > created_at`, revocation timestamps) ensure the schema matches `APIKeyService` queries and rotation cleanup expectations.

### 6.2 Service

`APIKeyService` (backend/services/api_key_service.py):

- Generates prefixed keys (shown once) and stores SHA-256 hashes.
- Supports list/create/rotate/revoke, expiration, and cleanup.
- Rotation increments version and resets expiry + revoke flags.

### 6.3 API Routes

- **List keys**: `GET /api/v1/api-keys` (rate-limit: search)
- **Create**: `POST /api/v1/api-keys` (returns `key` once) (rate-limit: standard)
- **Rotate**: `POST /api/v1/api-keys/{key_id}/rotate` (returns new secret) (rate-limit: standard)
- **Revoke**: `POST /api/v1/api-keys/{key_id}/revoke`

All endpoints require `api_keys:manage` permission. Admins may supply `user_id` to manage someone else's keys; non-admins are limited to their own data.

### 6.4 Operational Guidance

1. **Storage**: Treat plaintext key values like passwords. They are never persisted—store them in a secure vault.
2. **Rotation**: Align `API_KEY_ROTATION_DAYS` with organizational policy (default 90 days). Each rotation increments `version` and refreshes `expires_at` without losing audit history.
3. **Grace Period & Cleanup**: `API_KEY_GRACE_PERIOD_DAYS` controls cleanup of expired keys. `APIKeyService.cleanup_expired_keys()` deletes rows where `expires_at` is older than the grace window, keeping revoked/expired secrets from lingering.
4. **Permissions**: Keep lists minimal. Example: "documents:read", "metrics:read".
5. **Revocation**: On suspected compromise, call revoke endpoint and redeploy affected services with new secrets. `revoked_by` tracks the admin initiating the action.

## 7. Monitoring & Logging

- Rate-limit breaches: `krai.rate_limit` logger warns and emits IP + path.
- API key lifecycle: `krai.api_keys` logger captures create/rotate/revoke operations.
- Startup logs print security posture (CORS, rate limit enabled, validation enabled) for quick verification in orchestrators.

## 8. Deployment Checklist

1. Confirm `.env` contains production values (origins, timeouts, CSP, Redis URL).
2. Run migrations (including `201_add_api_keys_table.sql`).
3. Enable HTTPS termination (CSP/HSTS assume TLS).
4. Provision Redis if horizontal scaling is required for rate limiting.
5. Distribute API keys using the new management endpoints; store only hashed versions server-side.
6. Document rotation schedules and incorporate them into runbooks.

---

For additional hardening (TLS certificates, network ACLs, secrets management), integrate with your infrastructure provider (Kubernetes secrets, HashiCorp Vault, AWS IAM, etc.).
