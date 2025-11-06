# Performance Testing Guide

This guide describes how to run performance and load tests for the KRAI backend and WebSocket services.

## Prerequisites
- Python 3.11 (used by the backend).
- The backend API must be running (`uvicorn backend.main:app --host 0.0.0.0 --port 8000`).
- A PostgreSQL instance reachable by the backend (Docker compose provides `krai-postgres`).
- Locust installed (`pip install locust`).

## HTTP Load Test (Locust)
```bash
# Install dependencies (if not already installed)
pip install -r backend/requirements.txt
# Run Locust against the API
locust -f tests/performance/load_test.py --host http://localhost:8000
```
Open a browser at `http://localhost:8089` to start the load test. The script exercises typical CRUD endpoints and measures response times and request throughput.

## WebSocket Load Test
```bash
python tests/performance/websocket_load_test.py \
  --connections 100 \
  --duration 600 \
  --url ws://localhost:8000/ws/monitoring?token=$(python -c "import os; print(os.getenv('TEST_JWT', ''))")
```
The script opens many concurrent WebSocket connections, sends periodic `ping` messages, and records latency and reconnection statistics.

## Database Performance Test
```bash
python tests/performance/database_performance_test.py \
  --iterations 1000 \
  --query "SELECT * FROM krai_intelligence.chunks LIMIT 10;"
```
Measures raw query execution time and helps identify bottlenecks in the PostgreSQL schema.

## Interpreting Results
- **Latency**: Aim for < 200 ms for API calls under typical load.
- **Throughput**: Should scale linearly with added workers up to the CPU/RAM limits.
- **WebSocket**: Reconnection rate should stay below 1 % and average latency < 100 ms.
- **Database**: Queries using pgvector should stay under 50 ms for typical vector sizes.

## Common Issues
- **Connection errors**: Ensure the backend is reachable and the `DATABASE_URL` points to the correct host.
- **Locust cannot connect**: Verify the `--host` URL matches the running FastAPI server.
- **WebSocket auth failures**: Provide a valid JWT via the `TEST_JWT` environment variable.

---
*Generated from the implementation and performance test scripts.*
