# Dashboard E2E Tests

## Overview

This directory contains end-to-end dashboard validation tests for production pipeline outputs.
The tests use Playwright (Python) to validate login, search, document details, images, and stage status.

## Standalone Usage

```bash
# Run dashboard validation standalone
python tests/e2e/dashboard_production_test.py \
  --base-url http://localhost:8080 \
  --document-ids abc-123-def xyz-789-ghi \
  --output-dir ./test_results
```

## Integrated Usage

```bash
# Run production test with dashboard validation
python scripts/pipeline_processor.py \
  --production-test \
  --validate-dashboard
```

## CI/CD Behavior

- In CI: dashboard validation returns `PENDING` (actual validation runs in a separate workflow step).
- Locally: dashboard validation runs immediately after production pipeline validation.

## Prerequisites

- Laravel dashboard is running at the configured URL.
- `AdminUserSeeder` has been executed (default credentials: `admin@krai.local` / `admin123`).
- Playwright browser binaries are installed:

```bash
playwright install chromium
```
