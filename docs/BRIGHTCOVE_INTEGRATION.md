# Brightcove Integration

## Overview

This project supports optional Brightcove video metadata enrichment as Stage 16 (`video_enrichment`) in the pipeline.

## Prerequisites

- Brightcove Video Cloud account
- OAuth client credentials with CMS API access
- Migration `017_video_enrichment_columns.sql` applied

## Configuration

Set these variables in `.env`:

```bash
ENABLE_BRIGHTCOVE_ENRICHMENT=true
BRIGHTCOVE_ACCOUNT_ID=your_account_id
BRIGHTCOVE_CLIENT_ID=your_client_id
BRIGHTCOVE_CLIENT_SECRET=your_client_secret
BRIGHTCOVE_API_TIMEOUT=30
BRIGHTCOVE_BATCH_SIZE=10
BRIGHTCOVE_RATE_LIMIT_DELAY=1.0
```

## How It Works

1. Stage 13 (`link_extraction`) stores video links with `metadata.needs_enrichment=true`.
2. Stage 16 (`video_enrichment`) loads videos needing enrichment.
3. OAuth 2.0 token is requested from Brightcove.
4. CMS API metadata is fetched and stored in `krai_content.videos`.
5. Successful enrichment sets `metadata.needs_enrichment=false` and updates `enriched_at`.

## Credential Setup

Create credentials in Brightcove Studio:

- https://studio.brightcove.com/products/videocloud/admin/api-authentication

Grant read access for CMS video metadata.

## Fallback Behavior

- Credentials missing:
  - Processor logs warning and skips API enrichment.
  - Videos remain with `metadata.needs_enrichment=true`.
  - `enrichment_error` remains `NULL`.
- API failures:
  - `enrichment_error` is stored.
  - `metadata.needs_enrichment=true` remains for retry.
- Rate limiting (HTTP 429):
  - Exponential backoff is applied (1s, 2s, 4s, 8s).
  - `Retry-After` header is honored when present.

## Troubleshooting

- `No videos enriched in this run`:
  - Check `ENABLE_BRIGHTCOVE_ENRICHMENT=true`.
  - Check credentials and API permission scopes.
- `Failed to obtain Brightcove OAuth token`:
  - Validate `BRIGHTCOVE_CLIENT_ID` and `BRIGHTCOVE_CLIENT_SECRET`.
- Frequent 429 responses:
  - Increase `BRIGHTCOVE_RATE_LIMIT_DELAY`.
  - Reduce `BRIGHTCOVE_BATCH_SIZE`.
