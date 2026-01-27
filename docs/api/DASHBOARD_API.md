# Dashboard API Documentation

This document consolidates all API endpoints and WebSocket protocols used by the Laravel Dashboard.

## REST Endpoints

| Method | Path | Description | Permissions |
|--------|------|-------------|-------------|
| GET | `/api/v1/products` | List all products | `products:read` |
| POST | `/api/v1/products` | Create a new product | `products:create` |
| GET | `/api/v1/products/{id}` | Retrieve product details | `products:read` |
| PATCH | `/api/v1/products/{id}` | Update product | `products:update` |
| DELETE | `/api/v1/products/{id}` | Delete product | `products:delete` |
| GET | `/api/v1/documents` | List documents | `documents:read` |
| POST | `/api/v1/documents` | Create document | `documents:create` |
| ... | ... | ... | ... |

## WebSocket Protocol

The Dashboard connects to the WebSocket endpoint at **`/ws/monitoring?token=<jwt>`**. Authentication is performed via a `token` query parameter containing the JWT. If the token is missing or invalid, the server closes the connection with a 1008 (policy violation) code.

### Message Types

| Type | Payload | Direction | Description |
|------|---------|-----------|-------------|
| `ping` | `{}` | client → server | Keep‑alive ping. Server replies with `pong`. |
| `pong` | `{}` | server → client | Response to `ping`.
| `pipeline_update` | `{ "pipeline_id": number, "status": string, "progress": number }` | server → client | Real‑time pipeline status updates.
| `queue_update` | `{ "queue_id": number, "pending": number, "processing": number, "failed": number }` | server → client | Queue metrics updates.
| `hardware_update` | `{ "cpu": number, "memory": number, "disk": number }` | server → client | System hardware metrics.
| `alert_triggered` | `{ "id": number, "title": string, "message": string, "severity": "info" or "warning" or "error" }` | server → client | Alert notifications (new naming).
| `stage_completed` | `{ "stage": string, "duration_ms": number }` | server → client | Notification when a processing stage completes.
| `acknowledge_alert` | `{ "id": number }` | client → server | Acknowledge/dismiss an alert.
| `ping` | `{}` | client → server | Keep‑alive ping.
| `pong` | `{}` | server → client | Response to `ping`.

### Reconnection Strategy

The client library (`useWebSocket` hook) implements exponential back‑off reconnection with a maximum of 5 attempts (delay = `reconnectInterval * 2^(attempt‑1)` capped at 30 s). Upon reconnection, the client re‑subscribes to the required channels.

## Error Handling

All error responses follow the standard **`ErrorResponse`** schema:

```json
{
  "detail": "Error message",
  "code": "ERR_CODE",
  "status": 400
}
```

WebSocket errors are sent as messages with type `error` and include a `code` field.

---

*Generated from the API implementation and monitoring specifications.*
