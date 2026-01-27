# End‑to‑End (E2E) Testing Guide

**Note:** This guide was originally written for a React frontend. It should be updated for Laravel/Filament dashboard testing or archived if no longer applicable.

This guide explains how to set up and run the Playwright end‑to‑end test suite for the KRAI dashboard.

## Prerequisites
- Node.js 20+ (as defined in `laravel-admin/package.json`).
- Playwright browsers installed: `npx playwright install --with-deps`.
- The backend API must be running (`uvicorn backend.main:app --host 0.0.0.0 --port 8000`).
- A PostgreSQL instance reachable by the backend (Docker compose provides `krai-postgres`).

## Running the Tests
```bash
# Install dependencies (if not already done)
npm ci
# Install browsers (once)
npx playwright install --with-deps
# Run the full suite
npm run test:e2e
```

### UI Mode (headed)
```bash
npm run test:e2e:ui
```
This opens a visible browser window for debugging.

### Running a Single Spec
```bash
npx playwright test path/to/spec.ts
```
Replace `path/to/spec.ts` with the relative path under `laravel-admin/tests/e2e/`.

## Test Structure
- **fixtures/** – reusable login/auth fixtures.
- **e2e/** – individual spec files, each focusing on a feature (documents, products, monitoring, etc.).
- Tests use **data‑testid** attributes for stable selectors.

## CI Integration
The workflow `.github/workflows/e2e-tests.yml` runs the suite on every push/PR to `main` and `develop`. It starts a PostgreSQL service, launches the FastAPI backend, and executes the Playwright tests.

## Common Issues & Troubleshooting
- **Browser not installed** – run `npx playwright install`.
- **Backend not reachable** – ensure the service is listening on `http://localhost:8000/health`.
- **Flaky tests** – increase the timeout in the Playwright config or add explicit `await page.waitFor...` statements.

---
*Generated from the implementation and CI configuration.*
