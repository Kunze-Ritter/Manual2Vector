# Performance Features Documentation

This document describes the performance and telemetry features implemented in the KRAI processing pipeline.

## 🛡️ Memory Protection

### Structured Text Cap

**Purpose:** Prevent memory issues when processing PDFs with large structured tables.

**Configuration:**
```python
# In TextExtractor initialization
extractor = TextExtractor(
    max_structured_lines=200,      # Max lines per page (default: 200)
    max_structured_line_len=300    # Max chars per line (default: 300)
)
```

**Environment Variables:**
- None (configured programmatically or via `chunk_settings.json`)

**Behavior:**
- Limits structured text extraction to 200 lines per page
- Trims individual lines to 300 characters (adds "…" ellipsis)
- Prevents memory exhaustion on documents with massive tables

**Example:**
```
Before: 1000+ lines, 500+ chars each → 500KB+ per page
After:  200 lines max, 300 chars each → ~60KB per page
```

---

## 📊 Logger Rotation & Retention

**Purpose:** Prevent log files from consuming unlimited disk space.

**Configuration via Environment Variables:**

```bash
# Log level
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Enable/disable logging
LOG_TO_CONSOLE=true               # Console output
LOG_TO_FILE=true                  # File output

# Log directory
LOG_DIR=backend/logs              # Where to store logs

# Rotation mode
LOG_ROTATION=size                 # 'size' or 'time'

# Size-based rotation (LOG_ROTATION=size)
LOG_MAX_BYTES=10000000           # 10MB per file
LOG_BACKUP_COUNT=5               # Keep 5 backup files

# Time-based rotation (LOG_ROTATION=time)
LOG_ROTATION_WHEN=midnight       # midnight, W0-W6, H
LOG_ROTATION_INTERVAL=1          # Interval count
```

**Behavior:**

**Size-based rotation:**
- Rotates when log file reaches `LOG_MAX_BYTES`
- Keeps `LOG_BACKUP_COUNT` backup files
- Example: `app.log`, `app.log.1`, `app.log.2`, ..., `app.log.5`

**Time-based rotation:**
- Rotates at specified time (e.g., midnight)
- Keeps `LOG_BACKUP_COUNT` backup files
- Example: `app.log`, `app.log.2025-01-27`, `app.log.2025-01-26`, ...

---

## 🔍 PDF Engine Telemetry

**Purpose:** Track which extraction engine was used and monitor fallback usage.

**Telemetry Fields (in `DocumentMetadata`):**

```python
class DocumentMetadata(BaseModel):
    engine_used: str = "pymupdf"           # Primary engine used
    fallback_used: Optional[str] = None    # Fallback used (e.g., "ocr", "pdfplumber")
    pages_failed: int = 0                  # Pages that failed extraction
```

**Tracked Metrics:**
- `engine_used`: Which engine extracted the text (`pymupdf` or `pdfplumber`)
- `fallback_used`: Whether fallback was needed (`ocr`, `pdfplumber`, or `None`)
- `pages_failed`: Count of pages where extraction failed

**Example:**
```json
{
  "engine_used": "pymupdf",
  "fallback_used": "ocr",
  "pages_failed": 3
}
```

This indicates:
- Primary extraction used PyMuPDF
- OCR fallback was triggered for some pages
- 3 pages failed extraction entirely

---

## 🤖 OCR Fallback

**Purpose:** Extract text from scanned PDFs or pages without selectable text.

**Configuration:**

```bash
# Enable OCR fallback
ENABLE_OCR_FALLBACK=false
```

**Requirements:**
```bash
pip install pytesseract pillow
```

Also requires Tesseract binary:
- **Windows:** Download from [GitHub](https://github.com/tesseract-ocr/tesseract)
- **Linux:** `sudo apt-get install tesseract-ocr`
- **macOS:** `brew install tesseract`

**Behavior:**
1. Primary extraction attempts to get text from PDF
2. If page has no text and `ENABLE_OCR_FALLBACK=true`:
   - Render page as image (200 DPI)
   - Run Tesseract OCR
   - Use OCR text if available
3. Track usage in `fallback_used` field

**Performance Impact:**
- OCR is ~10-20x slower than direct text extraction
- Only runs on pages without text
- Recommended: Enable only for scanned documents

---

## 📈 Advanced Statistics

### Confidence Quantiles

**Purpose:** Provide detailed confidence distribution for extracted entities.

**Quantiles Calculated:**
- **P50 (Median):** Middle value of confidence scores
- **P90:** 90th percentile (top 10% threshold)
- **P99:** 99th percentile (top 1% threshold)

**Available For:**
- Error codes: `error_conf_quantiles`
- Products: `product_conf_quantiles`
- Versions: `version_conf_quantiles`

**Example:**
```json
{
  "error_conf_quantiles": {
    "p50": 0.85,
    "p90": 0.92,
    "p99": 0.98
  }
}
```

**Interpretation:**
- 50% of error codes have confidence ≥ 0.85
- 10% of error codes have confidence ≥ 0.92
- 1% of error codes have confidence ≥ 0.98

### Page Coverage

**Purpose:** Measure how much of the document was successfully chunked.

**Fields:**
- `covered`: Number of pages with at least one chunk
- `total`: Total pages in document
- `ratio`: Coverage ratio (0.0 to 1.0)

**Example:**
```json
{
  "page_coverage": {
    "covered": 245,
    "total": 278,
    "ratio": 0.881
  }
}
```

**Interpretation:**
- 245 out of 278 pages have chunks
- 88.1% coverage
- 33 pages (11.9%) have no chunks (likely blank or image-only)

**Use Cases:**
- Quality assurance: Low coverage may indicate extraction issues
- Document classification: Different doc types have different coverage patterns
- Performance monitoring: Track coverage trends over time

---

## 🧪 Testing

### Run Tests

```bash
# Test structured text caps
pytest backend/processors/test_structured_text_cap.py -v

# Test statistics quantiles
pytest backend/processors/test_statistics_quantiles.py -v

# Run all tests
pytest backend/processors/ -v
```

### Test Coverage

- **Structured Text Cap:** Memory protection, line limits
- **Quantiles:** Edge cases, distributions, sorting
- **Page Coverage:** Full, partial, zero coverage scenarios

---

## 📋 Summary

| Feature | Purpose | Configuration | Impact |
|---------|---------|---------------|--------|
| **Structured Text Cap** | Memory protection | `max_structured_lines`, `max_structured_line_len` | Prevents OOM on large tables |
| **Logger Rotation** | Disk space management | `LOG_ROTATION`, `LOG_MAX_BYTES`, `LOG_BACKUP_COUNT` | Prevents unlimited log growth |
| **PDF Engine Telemetry** | Extraction monitoring | Automatic | Tracks engine usage and failures |
| **OCR Fallback** | Scanned PDF support | `ENABLE_OCR_FALLBACK` | Extracts text from images |
| **Confidence Quantiles** | Quality insights | Automatic | Detailed confidence distribution |
| **Page Coverage** | Completeness tracking | Automatic | Measures extraction completeness |

---

## 🎯 Benchmark Suite

**Purpose:** Measure and validate pipeline performance improvements with statistical rigor.

**Key Components:**
- **`scripts/run_benchmark.py`**: Main benchmark execution with baseline storage and comparison
- **`scripts/select_benchmark_documents.py`**: Document selection with stratification
- **Database Tables**: `krai_system.performance_baselines`, `krai_system.benchmark_documents`

**Features:**
- **Baseline Measurement**: Store performance metrics before optimization
- **Comparison Analysis**: Calculate improvement percentage after optimization
- **Statistical Metrics**: Average, P50 (median), P95, P99 percentiles
- **Per-Stage Breakdown**: Identify bottlenecks in pipeline stages
- **Dashboard Integration**: Visualize results in Filament Performance Metrics Widget

**Performance Target:**
- **30%+ improvement** across pipeline stages (from resilience architecture)
- Color-coded indicators: 🟢 Green (30%+), 🟡 Yellow (10-30%), 🔴 Red (<10%)

**Quick Start:**

```bash
# 1. Select benchmark documents
python scripts/select_benchmark_documents.py \
  --snapshot-dir ./staging-snapshots/latest \
  --count 10

# 2. Run baseline benchmark
python scripts/run_benchmark.py \
  --count 10 \
  --baseline \
  --output baseline_results.json

# 3. Implement optimizations
# (Make code changes, adjust configuration)

# 4. Run current benchmark with comparison
python scripts/run_benchmark.py \
  --count 10 \
  --compare \
  --output current_results.json
```

**Statistical Metrics:**
- **Average**: Mean processing time across all documents
- **P50 (Median)**: Typical performance, less affected by outliers
- **P95**: 95th percentile, represents typical worst-case
- **P99**: 99th percentile, captures extreme cases

**Integration with PerformanceCollector:**
- Benchmark results stored in `krai_system.performance_baselines`
- Accessible via `PerformanceCollector` service
- Displayed in Filament dashboard at `/kradmin`
- API endpoint: `GET /api/monitoring/performance`

**For Detailed Usage:**
- See **[docs/testing/BENCHMARK_GUIDE.md](testing/BENCHMARK_GUIDE.md)** for comprehensive workflow
- See **[docs/testing/BENCHMARK_QUICK_REFERENCE.md](testing/BENCHMARK_QUICK_REFERENCE.md)** for quick commands

---

## 🔗 Related Documentation

- [Benchmark Guide](testing/BENCHMARK_GUIDE.md) - Comprehensive benchmarking workflow
- [Benchmark Quick Reference](testing/BENCHMARK_QUICK_REFERENCE.md) - Quick command reference
- [Performance Testing Guide](testing/PERFORMANCE_TESTING_GUIDE.md) - Load testing with Locust
- [Performance Optimization](architecture/PERFORMANCE_OPTIMIZATION.md) - Optimization strategies
- [Installation Guide](../docs/setup/INSTALLATION_GUIDE.md)
- [Configuration Setup](../docs/setup/CONFIGURATION_SETUP.md)
- [Processing Checklist](../PROCESSING_CHECKLIST.md)
