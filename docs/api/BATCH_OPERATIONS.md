# Batch Operations API

The Batch Operations API provides transactional tools for deleting, updating, and changing the status of records across multiple resource tables. Operations support synchronous execution for small batches and asynchronous background execution for larger workloads, with automatic audit logging and rollback metadata.

## Endpoints

All endpoints are mounted under the main API prefix (`/api/v1`):

| Method | Path | Description | Required Permission |
| --- | --- | --- | --- |
| `POST` | `/batch/delete` | Delete multiple records by ID | `batch:delete` + resource delete permission |
| `PUT` | `/batch/update` | Apply field updates to multiple records | `batch:update` + resource write permission |
| `POST` | `/batch/status-change` | Change the `status` field for multiple records | `batch:update` + resource write permission |
| `GET` | `/batch/tasks/{task_id}` | Get status/progress for an async batch task | `batch:read` |
| `GET` | `/batch/tasks` | List your recent batch tasks | `batch:read` |
| `POST` | `/batch/tasks/{task_id}/cancel` | Cancel a queued/running batch task | `batch:delete` |
| `POST` | `/batch/rollback` | Execute compensating actions for a finished task | `batch:rollback` |

### Supported Resources

The API maps resource slugs to schema-qualified tables:

| Resource | Table |
| --- | --- |
| `documents` | `krai_core.documents` |
| `products` | `krai_core.products` |
| `manufacturers` | `krai_core.manufacturers` |
| `error_codes` | `krai_intelligence.error_codes` |
| `videos` | `krai_content.videos` |
| `images` | `krai_content.images` |

Permissions reuse existing resource scopes (`documents`, `products`, `videos`, etc.) combined with batch actions (`read`, `update`, `delete`, `rollback`). The `require_permission` dependency ensures the current user carries the necessary batch scope, while `_ensure_user_permission` enforces resource-level rights.

## Execution Model

### Synchronous vs Asynchronous

The API runs batches synchronously when the item count is below `ASYNC_THRESHOLD` (50 by default). Above this threshold, requests schedule a background `BatchTask` and immediately return a `task_id` for polling.

### Transaction Handling

`TransactionManager.execute_batch_with_transaction()` acquires an asyncpg transaction. Each per-record operation receives the transactional connection, enabling parameterized SQL (`DELETE` / `UPDATE`) for deterministic behavior.

The response tracks:

- `total` – number of requested records
- `successful` / `failed` – counts of processed results
- `results` – per-record status, identifier, and rollback metadata

Failures inside a transaction trigger a rollback when `rollback_on_error=True`. Outside of a transaction, the TransactionManager stops short of claiming atomic rollback and returns per-record outcome data for compensating actions.

### Audit Logging & Rollback Metadata

Every mutation writes to `krai_system.audit_log` with schema-qualified table names. Entries capture:

- `operation` (`DELETE`, `UPDATE`, `STATUS_CHANGE`, `ROLLBACK`, etc.)
- `old_values` / `new_values`
- `changed_by`
- optional `notes`

Rollback metadata (`rollback_data`) is returned per record so that the rollback endpoint can attempt compensating transactions (e.g., reinserting deleted rows or restoring fields).

## Asynchronous Task Lifecycle

When operations run in the background:

1. A `BatchTask` is created in `krai_system.processing_queue` and marked `QUEUED`.
2. FastAPI `BackgroundTasks` schedules a coroutine to execute the batch.
3. Before execution, metadata stores `total_items` and initial zero counts.
4. After each record, the progress callback updates `processed_items`, `successful_items`, `failed_items`, `progress`, and appends the latest result.
5. On completion or failure, the task status is updated (`COMPLETED`, `FAILED`, or `CANCELLED`).

The `GET /batch/tasks/{task_id}` endpoint returns live progress and individual record outcomes. `GET /batch/tasks` lists recent tasks, filtered by optional status/user criteria.

## Maintenance & Cleanup

### Health Reporting

The application health endpoint includes batch status, confirming whether asyncpg transaction support is active and the processing queue is reachable.

### Cleanup

`BatchTaskService.cleanup_completed_tasks()` removes completed, failed, or cancelled tasks older than a configurable number of hours (default 24). The cleanup logic:

- Filters by `task_type LIKE 'batch_%'`
- Uses exact-count selection before deletion
- Removes matching in-memory task metadata for consistency

A matching database helper (`krai_system.cleanup_old_batch_tasks`) uses `GET DIAGNOSTICS ROW_COUNT` to report deleted rows.

## Usage Tips

- Prefer smaller synchronous batches for quick, atomic updates when the asyncpg pool is available.
- When scheduling large jobs, poll `/batch/tasks/{task_id}` or list active tasks to monitor progress.
- Always validate that `status_change` requests include `options.new_status`; the API rejects empty values.
- Use the rollback endpoint promptly after failures to maximize compensating success, leveraging the audit log metadata.
- Ensure service roles have access to `krai_system.processing_queue` and `krai_system.audit_log` per migration `50_batch_operations_enhancements.sql`.
