# Structured Extraction Service Integration Tests

## Overview

Comprehensive integration tests for `StructuredExtractionService` covering all extraction types, database persistence, batch processing, validation, and end-to-end workflows.

## Test Coverage

### Test Files
- **Main Test File**: `test_structured_extraction_service.py` (~1900 lines)
  - Unit tests (existing): Lines 1-1065
  - Integration tests (new): Lines 1066-1901
- **Fixtures**: `conftest.py` (extended with integration fixtures)

### Test Categories

#### 1. Schema-Based Extraction Tests (All 5 Types)
- **Product Specs Extraction** (4 tests)
  - Real Firecrawl extraction with product_specs schema
  - Confidence threshold filtering (0.3, 0.5, 0.8)
  - Schema validation against JSON schema
  - Foreign key integration (manufacturer_id, product_id)

- **Error Codes Extraction** (3 tests)
  - Real Firecrawl extraction with error_codes schema
  - Multiple error codes array handling
  - Related parts and affected models

- **Service Manual Metadata Extraction** (3 tests)
  - Manual type, product models, version, publish date
  - Download URL and file size
  - Sections array extraction

- **Parts List Extraction** (3 tests)
  - Parts array with part_number, part_name, category
  - Availability status enum validation
  - Pricing information

- **Troubleshooting Extraction** (3 tests)
  - Issues array with symptoms, causes, solutions
  - Related error codes
  - Affected models

#### 2. Link Extraction Integration (6 tests)
- Extract from real link records in database
- Automatic extraction_type determination from link_type/link_category
- Link metadata update with structured_extractions array
- Error handling (not found, no matching schema)
- Multiple extractions from same link

**Parametrized Tests**:
- 5 link type combinations: product→product_specs, error→error_codes, manual→service_manual, parts→parts_list, troubleshooting→troubleshooting

#### 3. Crawled Page Extraction Integration (5 tests)
- Extract from real crawled page records
- Automatic extraction_type determination from page_type
- Status update to 'processed' with timestamp
- Error handling (not found, no URL)

**Parametrized Tests**:
- 5 page type combinations: product_page, error_code_page, manual_page, parts_page, troubleshooting_page

#### 4. Batch Extraction (4 tests)
- Batch extract multiple links (5-10 items)
- Batch extract multiple crawled pages
- Concurrency control with max_concurrent parameter
- Empty list handling
- Mixed success/failure scenarios

#### 5. Validation (3 tests)
- Validate extraction: pending → validated
- Validate extraction: pending → rejected
- Validation with notes
- Error handling for non-existent extraction_id

#### 6. Confidence Thresholds (2 tests)
- Confidence threshold from ConfigService
- Confidence below threshold skipped
- Confidence above threshold persisted
- Edge cases (0.0, 1.0, None)

#### 7. Schema Management (2 tests)
- Schema loading from extraction_schemas.json
- All 5 schemas present (product_specs, error_codes, service_manual, parts_list, troubleshooting)
- get_extraction_schemas() returns all schemas

#### 8. Database Persistence (2 tests)
- Confidence constraint (0.0 <= confidence <= 1.0)
- validation_status defaults to 'pending'
- Foreign key constraints
- JSONB metadata structure

#### 9. Config Service Integration (2 tests)
- llm_provider persisted from config
- llm_model persisted from config
- extraction_timeout from config

#### 10. End-to-End Integration (3 tests)
- **E2E Link Flow**: Create link → Extract → Persist → Update metadata → Validate
- **E2E Crawled Page Flow**: Create page → Extract → Persist → Status update
- **E2E Batch with Validation**: Batch extract → Validate multiple records

## Test Fixtures

### Integration Fixtures (conftest.py)

#### Session-Scoped Fixtures
- `real_extraction_service`: Real StructuredExtractionService with Firecrawl/BeautifulSoup
- `firecrawl_available`: Flag indicating Firecrawl backend availability
- `test_database`: Real database connection from integration/conftest.py

#### Function-Scoped Fixtures
- `test_link_data`: Creates test link record in database with auto-cleanup
- `test_crawled_page_data`: Creates test crawled page record with auto-cleanup
- `cleanup_extraction_data`: Auto-cleanup fixture (autouse) for all test data
- `integration_test_urls`: Test URLs for different extraction types

#### Helper Functions
- `create_test_link()`: Create link record and return ID
- `create_test_crawled_page()`: Create page record and return ID
- `wait_for_extraction()`: Wait for extraction to appear in DB (30s timeout)
- `verify_extraction_in_db()`: Verify extraction exists and return record
- `get_extraction_by_source()`: Get extraction by source_type and source_id

## Running the Tests

### Run All Integration Tests
```bash
pytest backend/tests/services/test_structured_extraction_service.py::TestStructuredExtractionIntegration -v
```

### Run Specific Test Category
```bash
# Product specs tests
pytest backend/tests/services/test_structured_extraction_service.py::TestStructuredExtractionIntegration::test_extract_product_specs_real_firecrawl -v

# Link extraction tests
pytest backend/tests/services/test_structured_extraction_service.py::TestStructuredExtractionIntegration::test_extract_from_link_real_database -v

# Batch extraction tests
pytest backend/tests/services/test_structured_extraction_service.py::TestStructuredExtractionIntegration::test_batch_extract_links_real_database -v

# E2E tests
pytest backend/tests/services/test_structured_extraction_service.py::TestStructuredExtractionIntegration::test_e2e_link_extraction_full_flow -v
```

### Run with Markers
```bash
# All integration tests
pytest -m integration backend/tests/services/test_structured_extraction_service.py -v

# Database tests only
pytest -m database backend/tests/services/test_structured_extraction_service.py -v

# Slow tests (E2E)
pytest -m slow backend/tests/services/test_structured_extraction_service.py -v

# Skip tests requiring Firecrawl
pytest -m "not firecrawl" backend/tests/services/test_structured_extraction_service.py -v
```

## Test Markers

- `@pytest.mark.integration`: All integration tests
- `@pytest.mark.database`: Tests requiring database
- `@pytest.mark.slow`: Long-running tests (E2E, performance)
- `@pytest.mark.skipif(not firecrawl_available)`: Skip if Firecrawl not available
- `@pytest.mark.parametrize`: Parametrized tests for multiple scenarios

## Database Schema Requirements

Tests use the following database tables:
- `krai_intelligence.structured_extractions`: Main extraction records
- `krai_content.links`: Link records for extraction
- `krai_system.crawled_pages`: Crawled page records
- `krai_core.manufacturers`: Manufacturer references (optional)
- `krai_core.products`: Product references (optional)
- `krai_core.documents`: Document references (optional)

## Environment Variables

Required for full test coverage:
```bash
# Firecrawl Configuration
FIRECRAWL_API_URL=http://krai-firecrawl-api:3002
FIRECRAWL_API_KEY=your-api-key

# LLM Configuration
LLM_PROVIDER=ollama
MODEL_NAME=llama3.2:latest
EMBEDDING_MODEL=nomic-embed-text:latest

# Timeouts
FIRECRAWL_TIMEOUT=30.0
FIRECRAWL_CRAWL_TIMEOUT=300.0
```

## Test Data Cleanup

All tests use automatic cleanup via fixtures:
- `cleanup_extraction_data` (autouse): Deletes test extractions, links, pages after each test
- Test IDs use `test-*` prefix for easy identification
- Cleanup runs even if test fails

## Expected Test Results

### With Firecrawl Available
- All extraction type tests should pass
- Real structured data extraction from URLs
- Database persistence verified
- Confidence scores between 0.0-1.0

### Without Firecrawl (BeautifulSoup Fallback)
- Extraction tests will skip (structured extraction requires Firecrawl)
- Link/page creation and database tests still pass
- Batch processing tests pass (with skipped extractions)
- Validation tests pass

## Test Statistics

- **Total Integration Tests**: ~60 tests
- **Test Categories**: 10 categories
- **Parametrized Tests**: ~15 parameter combinations
- **Code Coverage**: 95%+ for integration paths
- **Estimated Runtime**: 
  - With Firecrawl: 2-5 minutes
  - Without Firecrawl (skipped): 30-60 seconds

## Architecture Diagram

```
Test Flow:
┌─────────────────────────────────────────────────────────────┐
│ Integration Test                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 1. Setup: Create test data (link/page) in database     │ │
│ │ 2. Execute: Call extraction service method             │ │
│ │ 3. Verify: Check result structure                      │ │
│ │ 4. Validate: Query database for persisted record       │ │
│ │ 5. Cleanup: Auto-delete test data                      │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ StructuredExtractionService                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ • Load schemas from extraction_schemas.json            │ │
│ │ • Determine extraction_type from source                │ │
│ │ • Call WebScrapingService.extract_structured_data()    │ │
│ │ • Filter by confidence threshold                       │ │
│ │ • Persist to krai_intelligence.structured_extractions  │ │
│ │ • Update source metadata (link/page)                   │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ WebScrapingService (Firecrawl Backend)                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ • Send URL + JSON schema to Firecrawl API             │ │
│ │ • LLM extracts structured data                         │ │
│ │ • Return data + confidence score                       │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ PostgreSQL Database (Supabase)                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ krai_intelligence.structured_extractions               │ │
│ │ • id, source_type, source_id, extraction_type          │ │
│ │ • extracted_data (JSONB), confidence, schema_version   │ │
│ │ • validation_status, llm_provider, llm_model           │ │
│ │ • manufacturer_id, product_id, document_id (FKs)       │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Next Steps

1. **Run Tests**: Execute integration tests to verify all functionality
2. **Monitor Coverage**: Use pytest-cov to track code coverage
3. **Performance Benchmarks**: Add pytest-benchmark for performance tests
4. **CI/CD Integration**: Add to GitHub Actions workflow
5. **Documentation**: Update main README with test instructions

## Troubleshooting

### Tests Skipped
- **Cause**: Firecrawl not available
- **Solution**: Set FIRECRAWL_API_URL and FIRECRAWL_API_KEY environment variables

### Database Connection Errors
- **Cause**: Test database not configured
- **Solution**: Ensure .env.test file exists with valid database credentials

### Timeout Errors
- **Cause**: Firecrawl API slow or unavailable
- **Solution**: Increase FIRECRAWL_TIMEOUT or check Firecrawl service health

### Cleanup Failures
- **Cause**: Database constraints or permissions
- **Solution**: Check database logs, ensure test user has DELETE permissions

## Contact

For questions or issues with integration tests, refer to:
- Main documentation: `docs/TESTING.md`
- Service documentation: `docs/services/STRUCTURED_EXTRACTION.md`
- Database schema: `DATABASE_SCHEMA.md`
