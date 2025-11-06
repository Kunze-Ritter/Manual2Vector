# Testing Checklist

## Authentication

- [ ] Verify login flow for admin, editor, viewer roles
- [ ] Ensure JWT token is stored and refreshed correctly

## CRUD Operations

- [ ] Documents: create, read, update, delete
- [ ] Products: create, read, update, delete
- [ ] Manufacturers: create, read, update, delete
- [ ] Error Codes: create, read, update, delete
- [ ] Videos: upload, metadata, delete
- [ ] Images: upload, retrieve, delete

## Batch Operations

- [ ] Batch delete multiple entities
- [ ] Batch update status changes

## Monitoring

- [ ] WebSocket connects on page load
- [ ] Reconnection with exponential backoff after forced close
- [ ] Alert appears, can be acknowledged
- [ ] Alert can be dismissed (DELETE request)
- [ ] Metrics update in real‑time (pipeline, queue, hardware)

## Permissions

- [ ] Admin can access all endpoints
- [ ] Editor can read/write but not delete protected resources
- [ ] Viewer can only read data

## Performance

- [ ] HTTP load test (locust) runs without errors
- [ ] WebSocket load test maintains connection under load
- [ ] Database performance test meets latency thresholds

## Error Handling

- [ ] API returns proper error codes and messages
- [ ] UI displays user‑friendly error notifications

## UI/UX

- [ ] Responsive layout on various screen sizes
- [ ] Accessibility checks (ARIA labels, keyboard navigation)
- [ ] Data tables support sorting, filtering, pagination

## Documentation

- [ ] All internal links resolve correctly
- [ ] README references the testing checklist
- [ ] API docs reflect current endpoints and auth mechanisms

## Authentication

- [ ] Verify login flow for admin, editor, viewer roles
- [ ] Ensure JWT token is stored and refreshed correctly

## CRUD Operations

- [ ] Documents: create, read, update, delete
- [ ] Products: create, read, update, delete
- [ ] Manufacturers: create, read, update, delete
- [ ] Error Codes: create, read, update, delete
- [ ] Videos: upload, metadata, delete
- [ ] Images: upload, retrieve, delete

## Batch Operations

- [ ] Batch delete multiple entities
- [ ] Batch update status changes

## Monitoring

- [ ] WebSocket connects on page load
- [ ] Reconnection with exponential backoff after forced close
- [ ] Alert appears, can be acknowledged
- [ ] Alert can be dismissed (DELETE request)
- [ ] Metrics update in real‑time (pipeline, queue, hardware)

## Permissions

- [ ] Admin can access all endpoints
- [ ] Editor can read/write but not delete protected resources
- [ ] Viewer can only read data

## Performance

- [ ] HTTP load test (locust) runs without errors
- [ ] WebSocket load test maintains connection under load
- [ ] Database performance test meets latency thresholds

## Error Handling

- [ ] API returns proper error codes and messages
- [ ] UI displays user‑friendly error notifications

## UI/UX

- [ ] Responsive layout on various screen sizes
- [ ] Accessibility checks (ARIA labels, keyboard navigation)
- [ ] Data tables support sorting, filtering, pagination

## Documentation

- [ ] All internal links resolve correctly
- [ ] README references the testing checklist
- [ ] API docs reflect current endpoints and auth mechanisms
