# Testing Guide

This guide outlines how to run the various test suites for the KRAI project.

## End‑to‑End (E2E) Tests

- **Location:** `frontend/tests/e2e/`
- **Run:** `npm run test:e2e`
- **Prerequisites:**
  - Backend API must be running (`uvicorn backend.main:app`).
  - Database service must be available.
  - Playwright browsers installed (`npx playwright install`).
- **What is covered:** Authentication flows, CRUD operations for documents and products, permission checks, monitoring WebSocket reconnection and alert handling.

## Backend API Tests

- **Location:** `tests/api/`
- **Run:** `pytest tests/api/`
- **Prerequisites:**
  - Test database (can reuse the same local PostgreSQL instance).
  - Environment variables for test users (`ADMIN_USERNAME`, `ADMIN_PASSWORD`).
- **What is covered:** Auth endpoints, document CRUD, batch delete, WebSocket connection endpoint.

## Performance Tests

- **Location:** `tests/performance/`
- **Run:**
  - Load test (HTTP): `locust -f tests/performance/load_test.py`
  - WebSocket load test: `python tests/performance/websocket_load_test.py`
  - Database performance test: `python tests/performance/database_performance_test.py`
- **Purpose:** Validate scalability and latency under load.

## Checklist

See `../dashboard/TESTING_CHECKLIST.md` for a quick verification checklist before merging.
