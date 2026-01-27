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

## Benchmark Testing vs. Load Testing

This guide focuses on **load testing** (concurrent users, throughput, scalability). For **benchmark testing** (performance measurement, optimization validation, baseline comparison), see:

**[BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md)** - Comprehensive guide for:
- Running baseline and current benchmarks
- Measuring pipeline performance improvements
- Validating 30%+ optimization targets
- Statistical analysis (avg, P50, P95, P99)
- Staging environment setup

### Key Differences

| Aspect | Load Testing (This Guide) | Benchmark Testing (BENCHMARK_GUIDE.md) |
|--------|---------------------------|----------------------------------------|
| **Purpose** | Test system under concurrent load | Measure and compare performance metrics |
| **Tools** | Locust, custom WebSocket scripts | `run_benchmark.py`, `select_benchmark_documents.py` |
| **Metrics** | Throughput, latency, error rate | Processing time, statistical percentiles |
| **Environment** | Production or staging | Staging with controlled document set |
| **Use Case** | Capacity planning, stress testing | Optimization validation, regression detection |

## Common Issues
- **Connection errors**: Ensure the backend is reachable and the `DATABASE_URL` points to the correct host.
- **Locust cannot connect**: Verify the `--host` URL matches the running FastAPI server.
- **WebSocket auth failures**: Provide a valid JWT via the `TEST_JWT` environment variable.

## Related Documentation

- **[BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md)** - Performance benchmarking and optimization validation
- **[BENCHMARK_QUICK_REFERENCE.md](BENCHMARK_QUICK_REFERENCE.md)** - Quick command reference for benchmarks
- **[PERFORMANCE_OPTIMIZATION.md](../architecture/PERFORMANCE_OPTIMIZATION.md)** - Optimization strategies
- **[PERFORMANCE_FEATURES.md](../PERFORMANCE_FEATURES.md)** - Performance features overview

---
*Generated from the implementation and performance test scripts.*
