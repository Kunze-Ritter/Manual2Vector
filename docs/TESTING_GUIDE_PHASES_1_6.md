# KRAI Testing Guide - Phases 1-6
# ==================================

This guide provides comprehensive instructions for running the KRAI test suite, covering all Phase 1-6 features including multimodal processing, hierarchical chunking, SVG extraction, and advanced search capabilities.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Environment Setup](#test-environment-setup)
3. [Running Tests](#running-tests)
4. [Test Categories](#test-categories)
5. [Expected Outputs](#expected-outputs)
6. [Troubleshooting](#troubleshooting)
7. [Performance Testing](#performance-testing)

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.9+ with pip
- PostgreSQL and MinIO running (via Docker Compose)
- Test environment configured

### Fastest Way to Run Tests

```bash
# 1. Start test services
docker-compose -f archive/docker/docker-compose.test.yml up -d

# 2. Install test dependencies
pip install -r requirements-test.txt

# 3. Run core integration tests
pytest tests/integration/ -v --tb=short

# 4. Run pipeline tests
python scripts/test_full_pipeline_phases_1_6.py --verbose
```

## Test Environment Setup

### 1. Database Setup

Create a test database separate from production:

```sql
-- Create test database
CREATE DATABASE krai_test;
CREATE USER krai_test WITH PASSWORD 'krai_test_password';
GRANT ALL PRIVILEGES ON DATABASE krai_test TO krai_test;
```

### 2. Environment Configuration

Copy and configure the test environment:

```bash
# Copy test environment template
cp .env.test.example .env.test

# Edit test configuration
nano .env.test
```

Key settings to verify:
- `DATABASE_URL` points to test database
- `MINIO_ENDPOINT` uses test buckets
- `TESTING=true` flag is set
- Feature flags are enabled for comprehensive testing

### 3. Service Dependencies

Start required services for testing:

```bash
# Start PostgreSQL and MinIO
docker-compose -f archive/docker/docker-compose.test.yml up -d postgresql minio

# Wait for services to be ready
python scripts/wait_for_services.py

# Apply test migrations (file-based 01-05 Phase 6 migrations)
python scripts/apply_test_migrations.py
```

### 4. Test Data Setup

Prepare test documents and fixtures:

```bash
# Create test directories
mkdir -p tests/fixtures/{documents,images,videos}

# Download or create test documents
python scripts/setup_test_data.py
```

## Running Tests

### Basic Test Commands

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test categories
pytest tests/integration/test_full_pipeline_integration.py::TestFullPipelineIntegration -v
pytest tests/integration/test_full_pipeline_integration.py::TestDatabaseIntegration -v

# Run with coverage
pytest tests/integration/ --cov=backend --cov-report=html

# Run performance tests
pytest tests/performance/ -v -m "not slow"
```

### Pipeline Test Scripts

```bash
# Full pipeline test (all phases)
python scripts/test_full_pipeline_phases_1_6.py --verbose

# Individual scenario tests
python scripts/test_full_pipeline_phases_1_6.py --scenario svg
python scripts/test_full_pipeline_phases_1_6.py --scenario hierarchical

# Multimodal search tests
python scripts/test_multimodal_search.py --verbose
python scripts/test_multimodal_search.py --performance

# Database migration tests
python scripts/test_postgresql_migrations.py --verbose
```

### Advanced Test Options

```bash
# Run tests with custom configuration
TESTING=true pytest tests/integration/ -v

# Run tests with detailed output
pytest tests/integration/ -v -s --tb=long

# Run tests in parallel
pytest tests/integration/ -n auto

# Run tests with markers
pytest tests/integration/ -m "integration and not slow"
pytest tests/integration/ -m "database or storage"
```

## Test Categories

### 1. Integration Tests

**Location**: `tests/integration/`

**Purpose**: End-to-end testing of the complete pipeline

**Key Features Tested**:
- Document upload and processing
- Hierarchical chunking
- SVG extraction and conversion
- Table extraction and analysis
- Context extraction for all media types
- Multimodal embedding generation
- Search functionality across content types

**Example Output**:
```
============================= test session starts =============================
collected 6 items

tests/integration/test_full_pipeline_integration.py::TestFullPipelineIntegration::test_complete_document_processing PASSED [ 16%]
tests/integration/test_full_pipeline_integration.py::TestFullPipelineIntegration::test_hierarchical_chunking_integration PASSED [ 33%]
tests/integration/test_full_pipeline_integration.py::TestFullPipelineIntegration::test_svg_vector_graphics_integration PASSED [ 50%]
tests/integration/test_full_pipeline_integration.py::TestFullPipelineIntegration::test_multimodal_search_integration PASSED [ 66%]
tests/integration/test_full_pipeline_integration.py::TestFullPipelineIntegration::test_context_extraction_integration PASSED [ 83%]
tests/integration/test_full_pipeline_integration.py::TestFullPipelineIntegration::test_embedding_generation_integration PASSED [100%]

============================== 6 passed in 45.23s ==============================
```

### 2. Pipeline Tests

**Location**: `scripts/test_full_pipeline_phases_1_6.py`

**Purpose**: Comprehensive pipeline validation with detailed reporting

**Test Scenarios**:
- SVG Processing: Vector graphics extraction and PNG conversion
- Hierarchical Chunking: Section hierarchy and error code detection
- Table Extraction: Structured data extraction and markdown conversion
- Context Extraction: Media context analysis with AI
- Multimodal Embeddings: Cross-modal embedding generation
- Multimodal Search: Unified search across all content types

**Example Output**:
```
🧪 Pipeline Test Results
==================================================
Total Tests: 6
✅ Passed: 5
❌ Failed: 0
⏸️ Skipped: 1
📊 Success Rate: 83.3% (excluding skipped)

Test Details:
------------------------------
SVG Processing: PASS (12.34s)
Hierarchical Chunking: PASS (8.45s)
Table Extraction: PASS (6.78s)
Context Extraction: PASS (15.23s)
Multimodal Embeddings: PASS (9.87s)
Multimodal Search: SKIP (0.12s)
```

### 3. Search Tests

**Location**: `scripts/test_multimodal_search.py`

**Purpose**: Validate multimodal search functionality

**Test Categories**:
- Unified multimodal search across all content types
- Modality filtering and relevance ranking
- Context-aware image search
- Two-stage retrieval with LLM expansion
- Performance benchmarking

**Example Output**:
```
🔍 Multimodal Search Test Results
┌─────────────────────────────────────┐
│ Total Tests: 5                      │
│ ✅ Passed: 4                        │
│ ❌ Failed: 1                        │
│ 📊 Success Rate: 80.0%              │
└─────────────────────────────────────┘

🔍 Unified Multimodal Search
┌─────────────────────┬───────┬─────────┬──────────────────────┐
│ Metric              │ Value │ Status  │ Details              │
├─────────────────────┼───────┼─────────┼──────────────────────┤
│ Total Queries       │ 5     │ ✅      │                      │
│ Successful Queries  │ 4     │ ✅      │                      │
│ Success Rate        │ 80.0% │ ✅      │                      │
│ Avg Processing Time │ 45.2ms│ ✅      │ Target: 100ms        │
└─────────────────────┴───────┴─────────┴──────────────────────┘
```

### 4. Database Tests

**Location**: `scripts/test_postgresql_migrations.py`

**Purpose**: Validate database schema and RPC functions

**Validation Areas**:
- Schema validation across all KRAI schemas
- RPC function availability and execution
- Migration status and rollback capability
- Database performance and connection pooling
- Data integrity and foreign key relationships

**Example Output**:
```
🗄️ PostgreSQL Migration Test Results
┌─────────────────────────────────────┐
│ Total Tests: 5                      │
│ ✅ Passed: 5                        │
│ ❌ Failed: 0                        │
│ 📊 Success Rate: 100.0%             │
└─────────────────────────────────────┘

🏗️ Schema Validation
┌─────────────────────┬───────┬─────────┬──────────────────────┐
│ Metric              │ Value │ Status  │ Details              │
├─────────────────────┼───────┼─────────┼──────────────────────┤
│ Schema Score        │ 95.8% │ ✅      │                      │
│ Expected Tables     │ 12    │ ✅      │                      │
│ Found Tables        │ 11    │ ⚠️      │ Missing: 1 table     │
└─────────────────────┴───────┴─────────┴──────────────────────┘
```

## Expected Outputs

### Successful Test Run Indicators

1. **All Services Connected**: Database, storage, and AI services connect successfully
2. **Migrations Applied**: All Phase 1-6 migrations (116-119) are present
3. **RPC Functions Available**: Key search functions are executable
4. **Document Processing**: Test documents process through all pipeline stages
5. **Data Consistency**: Cross-references between schemas are maintained
6. **Search Functionality**: Multimodal search returns relevant results

### Performance Benchmarks

- **Document Upload**: < 2 seconds
- **Text Processing**: < 10 seconds per document
- **Embedding Generation**: < 30 seconds for typical document
- **Multimodal Search**: < 100ms response time
- **Database Queries**: < 50ms average response

### Data Validation Points

- **Chunks Created**: Hierarchical structure preserved
- **Embeddings Generated**: Vector embeddings stored for all content types
- **Context Extracted**: Media items have contextual descriptions
- **Search Results**: Relevant content ranked by similarity
- **Metadata Consistency**: Document metadata propagated through pipeline

## Troubleshooting

### Common Test Failures

#### 1. Database Connection Issues

**Error**: `Failed to setup test database: connection refused`

**Solution**:
```bash
# Check PostgreSQL is running
docker-compose ps postgresql

# Restart database service
docker-compose restart postgresql

# Verify connection string in .env.test
echo $DATABASE_URL
```

#### 2. Storage Service Issues

**Error**: `Failed to setup test storage: bucket creation failed`

**Solution**:
```bash
# Check MinIO is running
docker-compose ps minio

# Verify MinIO credentials
docker-compose logs minio | grep "AccessKey"

# Test bucket creation manually
python scripts/test_minio_connection.py
```

#### 3. AI Service Connection Issues

**Error**: `Failed to setup test AI service: connection timeout`

**Solution**:
```bash
# Check Ollama is running
docker-compose ps ollama

# Pull required models
docker-compose exec ollama ollama pull llama2

# Test AI service directly
python scripts/test_ai_service.py
```

#### 4. Migration Issues

**Error**: `Missing critical migrations: 116, 117, 118`

**Solution**:
```bash
# Apply missing migrations
python scripts/apply_migrations.py --version 116
python scripts/apply_migrations.py --version 117
python scripts/apply_migrations.py --version 118

# Verify migration status
python scripts/test_postgresql_migrations.py --validate-only
```

#### 5. Test Data Issues

**Error**: `No test documents available`

**Solution**:
```bash
# Create test documents directory
mkdir -p service_documents

# Download sample documents
python scripts/download_test_documents.py

# Verify test documents
ls -la service_documents/*.pdf
```

### Performance Issues

#### Slow Test Execution

**Symptoms**: Tests taking > 5 minutes

**Solutions**:
```bash
# Reduce test data size
export TEST_DOCUMENT_SIZE_LIMIT=10MB

# Increase parallel execution
pytest tests/integration/ -n auto

# Use in-memory database for faster tests
export DATABASE_URL=postgresql://test:test@localhost:5432/test_db
```

#### Memory Issues

**Symptoms**: Out of memory errors during embedding generation

**Solutions**:
```bash
# Reduce batch sizes
export EMBEDDING_BATCH_SIZE=5

# Limit concurrent processes
export MAX_CONCURRENT_PROCESSES=1

# Use smaller test documents
export TEST_MAX_FILE_SIZE=1MB
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Run tests with debug logging
LOG_LEVEL=DEBUG pytest tests/integration/ -v -s

# Enable database query logging
ENABLE_QUERY_LOGGING=true python scripts/test_full_pipeline_phases_1_6.py

# Run specific test with maximum verbosity
pytest tests/integration/test_full_pipeline_integration.py::TestFullPipelineIntegration::test_complete_document_processing -v -s --tb=long
```

## Performance Testing

### Running Performance Tests

```bash
# Run performance benchmarks
python scripts/test_multimodal_search.py --performance

# Run database performance tests
python scripts/test_postgresql_migrations.py --performance-test

# Run load tests
python scripts/performance/load_test.py --concurrent-users=10 --duration=60
```

### Performance Metrics

Monitor these key metrics during testing:

1. **Response Times**: API endpoint latency
2. **Throughput**: Documents processed per minute
3. **Resource Usage**: CPU, memory, and disk utilization
4. **Database Performance**: Query execution times
5. **Search Performance**: Search result relevance and speed

### Performance Optimization

Based on test results, consider these optimizations:

```bash
# Increase database connection pool
export DATABASE_POOL_SIZE=20

# Optimize embedding batch size
export EMBEDDING_BATCH_SIZE=50

# Enable query caching
export ENABLE_QUERY_CACHE=true

# Use vector index optimizations
export ENABLE_VECTOR_INDEX=true
```

## Continuous Integration

### CI/CD Pipeline Integration

```yaml
# .github/workflows/test.yml
name: KRAI Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test_password
      minio:
        image: cgr.dev/chainguard/minio:latest
        env:
          MINIO_ROOT_PASSWORD: test_password
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run integration tests
        run: pytest tests/integration/ -v --cov=backend
      - name: Run pipeline tests
        run: python scripts/test_full_pipeline_phases_1_6.py
```

### Test Reports

Generate comprehensive test reports:

```bash
# HTML coverage report
pytest tests/integration/ --cov=backend --cov-report=html

# JSON test results
pytest tests/integration/ --json-report=test-results.json

# Performance report
python scripts/generate_test_report.py --output=test-report.html
```

## Best Practices

### Test Organization

1. **Use descriptive test names** that indicate what is being tested
2. **Group related tests** in logical classes and modules
3. **Use fixtures** for common setup and teardown
4. **Mock external dependencies** to ensure test reliability
5. **Clean up test data** to prevent test pollution

### Test Data Management

1. **Use consistent test data** across all test suites
2. **Isolate test data** from production data
3. **Clean up test artifacts** after test completion
4. **Version control test fixtures** for reproducibility
5. **Generate synthetic data** when real data is unavailable

### Error Handling

1. **Provide clear error messages** that help with debugging
2. **Use appropriate assertions** that validate expected behavior
3. **Handle expected failures** gracefully with proper cleanup
4. **Log test progress** for long-running tests
5. **Report test results** in a consistent format

This comprehensive testing guide should help you effectively validate all Phase 1-6 features of the KRAI system and ensure reliable operation across all components.
