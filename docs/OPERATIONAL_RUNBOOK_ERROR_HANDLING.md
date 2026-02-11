# Operational Runbook: Error Handling and Resilience

This runbook provides commands and procedures for operating and troubleshooting the KRAI pipeline error handling and retry system.

---

## Checking Error Status

List recent pending or retrying errors:

```sql
SELECT error_id, document_id, stage_name, status, error_type, correlation_id, created_at, next_retry_at
FROM krai_system.pipeline_errors
WHERE status IN ('pending', 'retrying')
ORDER BY created_at DESC
LIMIT 10;
```

---

## Monitoring Retry Chains

View all errors for a given request (replace `req_<id>` with the correlation prefix, e.g. `req_a3f2e8d1`):

```sql
SELECT error_id, stage_name, retry_count, status, correlation_id, created_at, next_retry_at
FROM krai_system.pipeline_errors
WHERE correlation_id LIKE 'req_<id>%'
ORDER BY created_at;
```

---

## Checking Advisory Locks

See currently held advisory locks:

```sql
SELECT * FROM pg_locks WHERE locktype = 'advisory';
```

Advisory locks are session-scoped; when the session ends (e.g. process exit), locks are released automatically.

---

## Checking Completion Markers

Check completion markers for a document (replace `{id}` with document UUID):

```sql
SELECT document_id, stage_name, data_hash, completed_at, metadata
FROM krai_system.stage_completion_markers
WHERE document_id = '{id}';
```

---

## Resolving Stuck Retries

If errors remain in `retrying` with no further retries (e.g. after long outage), mark them failed after a timeout:

```sql
UPDATE krai_system.pipeline_errors
SET status = 'failed',
    resolution_notes = 'Marked failed by operator: stuck in retrying (timeout)',
    updated_at = NOW()
WHERE status = 'retrying'
  AND updated_at < NOW() - INTERVAL '1 hour';
```

Adjust the interval as needed (e.g. `'30 minutes'`).

---

## Clearing Completion Markers

To force re-processing of a stage for a document (replace `{id}` and `{stage}`):

```sql
DELETE FROM krai_system.stage_completion_markers
WHERE document_id = '{id}' AND stage_name = '{stage}';
```

---

## Restarting Failed Stages

- **API:** Use the document/stage API to re-trigger the stage for the document.
- **Dashboard:** Use the Laravel dashboard to re-run the failed stage for the document.

No built-in “retry all failed” command; re-trigger is per document/stage.

---

## Known Issues and Mitigations

| Issue | Mitigation |
|-------|------------|
| Ollama connection errors | Restart Ollama: `docker start ollama` or `systemctl start ollama` |
| MinIO upload errors | Check MinIO service and OBJECT_STORAGE_* credentials in .env |
| PostgreSQL connection pool exhaustion | Increase pool size or reduce concurrent pipeline load |
| Advisory lock “leaks” | Locks are per-session; restart backend to release. Query `pg_locks` to confirm. |
| Stuck retries | Run the “Resolving Stuck Retries” UPDATE above after a suitable timeout |

---

## Verification Scripts

- **Schema:** `python scripts/verify_error_handling_schema.py`
- **Transient errors:** `python scripts/test_transient_errors.py` (and `--simulate` for steps)
- **Permanent errors:** `python scripts/test_permanent_errors.py`
- **Advisory locks:** `python scripts/test_advisory_locks.py`
- **Correlation IDs:** `python scripts/test_correlation_ids.py`

See also **VERIFICATION_REPORT_ERROR_HANDLING.md** for full test commands and pass criteria.
