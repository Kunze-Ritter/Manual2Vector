# KRAI Logging System - ProcessorLogger

## 🎨 Overview

`ProcessorLogger` powers the KRAI logging experience with rich-rendered console output, structured log records, and first-class helpers for pipeline reporting. The logger automatically prefers the `rich` library for colorful formatting and falls back to standard Python logging when `rich` is unavailable.

### Key Features

- ✅ **Rich-enhanced console output** with colors, icons, and timestamps
- ✅ **Automatic fallback** to standard logging with UTF-8 formatting when `rich` is missing
- ✅ **Rotating file handlers** configurable via environment variables
- ✅ **Helper methods** for sections, panels, tables, and progress reporting
- ✅ **Success semantic level** for positive pipeline events
- ✅ **PII-aware sanitization utilities** for safe logging

---

## ⚙️ Environment Configuration

`ProcessorLogger` reads its settings from environment variables (see `.env.example`). All variables are optional and ship with safe defaults:

- `LOG_LEVEL` (default `INFO`): Accepts `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- `LOG_TO_CONSOLE` (default `true`): Enable/disable console handler creation.
- `LOG_TO_FILE` (default `true`): Persist logs to rotating files.
- `LOG_DIR` (default `backend/logs`): Directory where log files are created.
- `LOG_ROTATION` (default `size`): Choose `size` for byte-based rotation or `time` for schedule-based rotation.
- `LOG_MAX_BYTES` (default `10_000_000`): Maximum file size before rotation when `LOG_ROTATION=size`.
- `LOG_BACKUP_COUNT` (default `5`): Number of rotated log files to retain.
- `LOG_ROTATION_WHEN` (default `midnight`): Scheduling anchor for time-based rotation (`midnight`, `W0`-`W6`, `H`, etc.).
- `LOG_ROTATION_INTERVAL` (default `1`): Interval multiplier for time rotation (e.g., every day vs. every 2 hours).
- `LOG_REDACT` (default `false`): Enable hashing of document identifiers for privacy.
- `LOG_SANITIZE_MAX_LEN` (default `256`): Maximum preview length when truncating large payloads during sanitization.

### Example Setups

```env
# Development: verbose output, console focus
LOG_LEVEL=DEBUG
LOG_TO_CONSOLE=true
LOG_TO_FILE=false

# Production: rotate daily and keep week's history
LOG_LEVEL=INFO
LOG_TO_CONSOLE=true
LOG_TO_FILE=true
LOG_ROTATION=time
LOG_ROTATION_WHEN=midnight
LOG_ROTATION_INTERVAL=1
LOG_BACKUP_COUNT=7
LOG_DIR=/var/log/krai
```

---

## 🎨 Log Format

ProcessorLogger formats log output in two modes depending on whether the `rich` library is available.

### Rich console output

```text
14:32:05 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ℹ️  [INFO     ] krai.pipeline | Loading configuration
✅ [SUCCESS  ] krai.pipeline | Document processed successfully
⚠️  [WARNING  ] krai.pipeline | Low confidence detected
```

### Standard logging fallback

```text
14:32:05 - krai.pipeline - INFO - Loading configuration
14:32:05 - krai.pipeline - INFO - [OK] Document processed successfully
14:32:05 - krai.pipeline - WARNING - [WARN] Low confidence detected
```

### Level color reference

| Level | Rich style | Fallback prefix | Purpose |
|-------|------------|-----------------|---------|
| DEBUG | Dim gray text | none | Detailed troubleshooting insights |
| INFO | Cyan text | none | Routine pipeline status updates |
| SUCCESS | Green text | `[OK]` | Successful completion events |
| WARNING | Yellow text | `[WARN]` | Potential risk indicators |
| ERROR | Red text | `[ERROR]` | Operational failures |
| CRITICAL | Bold red text | `[CRITICAL]` | Urgent intervention required |

---

## 🚀 Usage Examples

### Basic setup

```python
from backend.processors.logger import get_logger

logger = get_logger(name="krai.pipeline")

logger.info("Application started")
logger.success("Document ingested successfully")
logger.warning("Validation returned low confidence")
logger.error("Database update failed")
```

### Structured sections and panels

```python
from backend.processors.logger import get_logger

logger = get_logger()

logger.section("Stage 1 · Upload")
logger.info("Uploading document 1234")

logger.panel(
    "OCR fallback enabled for 12 pages",
    title="Upload summary",
    style="magenta"
)

logger.table(
    {
        "pages": 12,
        "images": 3,
        "duration": "18.4s"
    },
    title="📊 Upload Metrics"
)
```

### Progress reporting

```python
from backend.processors.logger import get_logger
import time

documents = ["A93E", "ACT9", "ADXM"]
logger = get_logger()

with logger.progress_bar(documents, description="Processing documents") as progress:
    task_id = progress.add_task("document_ingestion", total=len(documents))
    for doc in documents:
        # Long-running work simulated here
        time.sleep(0.5)
        logger.success(f"Completed ingestion for {doc}")
        progress.update(task_id, advance=1)
```

### Logging processing summaries

```python
from backend.processors.logger import get_logger, log_processing_summary

logger = get_logger()
stats = {
    "documents_processed": 3,
    "chunks_created": 540,
    "embeddings_created": 540,
    "products_extracted": 21,
    "error_codes_extracted": 12,
    "validation_failures": 0,
    "avg_confidence": 0.91,
}

log_processing_summary(logger, stats, duration_seconds=84.2)
```

---

## 🛠 ProcessorLogger Features

- **Rich-aware console handler** – automatically uses `RichHandler` with markup support when available.
- **UTF-8 safe fallback** – wraps stdout to ensure Windows-compatible Unicode output.
- **File rotation strategies** – size-based (`RotatingFileHandler`) or time-based (`TimedRotatingFileHandler`).
- **PII protection helpers** – `sanitize_text`, `sanitize_document_name`, and `text_stats` mask sensitive data.
- **Convenience helpers** – `section()`, `panel()`, `table()`, `progress_bar()` streamline pipeline dashboards.
- **Success semantic level** – `logger.success()` maps to green output for positive milestones.
- **Singleton access** – `get_logger()` caches one configured instance per process.

---

## 🔄 Migration Guide

### Replacing `print()` statements

| Before | After |
|--------|-------|
| `print(f"Error starting stage: {e}")` | `logger.error("Error starting stage %s: %s", stage, e, exc_info=True)` |
| `print("Stage Status Tracker Demo")` | `logger.info("Stage Status Tracker Demo")` |

### Migrating from `colored_logging`

| Legacy approach | ProcessorLogger equivalent |
|-----------------|----------------------------|
| `apply_colored_logging_globally(level=logging.INFO)` | `logger = get_logger(name="krai.pipeline")` |
| `log_section("STAGE 1")` | `logger.section("STAGE 1")` |
| `log_progress(i, total, label)` | `progress.update(task_id, advance=1)` via `logger.progress_bar()` |
| `log_metric("Processed", count)` | `logger.table({...}, title="📊 Metrics")` or `log_processing_summary()` |

### Best practices

- Use `logger.info()` for routine milestones and state changes.
- Prefer `logger.debug()` for verbose instrumentation hidden at higher log levels.
- Emit user-facing successes with `logger.success()` to keep feedback positive.
- Always attach context (document IDs, stage names) to warnings and errors.
- Include `exc_info=True` when logging exceptions to capture tracebacks.

---

## 🪂 Fallback Behavior

When `rich` is not installed or the environment is non-interactive (`LOG_TO_CONSOLE=false`), ProcessorLogger reconfigures itself to the Python standard logging stack.

- Console output uses the format `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"` with 24-hour timestamps.
- Success, warning, and error helpers prefix messages with `[OK]`, `[WARN]`, and `[ERROR]` to preserve semantics.
- Helper methods (`section`, `panel`, `table`) degrade gracefully by emitting structured multi-line log entries via `logger.info()`.
- Progress bars switch to debug-level counter messages (`description: current/total`).

---

## 🧪 Testing

Use the built-in demo blocks to validate your setup:

```bash
# From project root
python backend/processors/logger.py
python backend/processors/stage_tracker.py
```

These demos exercise console formatting, fallback handlers, and Supabase integration stubs without mutating production data.

---

## 🎯 Best Practices

1. **Announce stage boundaries**

   ```python
   logger.section("Stage · Chunk Extraction")
   logger.info("Extracting text from 42 pages")
   ```

2. **Attach context to errors**

   ```python
   logger.error(
       "Failed to persist metadata",
       extra={"document_id": doc_id, "stage": stage_name},
       exc_info=True
   )
   ```

3. **Summarize results**

   ```python
   logger.table(
       {
           "documents": stats.documents,
           "chunks": stats.chunks,
           "avg_confidence": f"{stats.avg_confidence:.2f}",
       },
       title="📊 Pipeline Summary"
   )
   ```

4. **Guard PII**

   ```python
   from backend.processors.logger import sanitize_text

   logger.debug("Request preview: %s", sanitize_text(raw_payload))
   ```

---

## 🔧 Configuration Tips

### Programmatic overrides

```python
from backend.processors.logger import ProcessorLogger

custom_logger = ProcessorLogger(
    name="krai.scheduler",
    log_file="/var/log/krai/scheduler.log"
)
custom_logger.info("Scheduler boot complete")
```

### Dynamic log level adjustments

```python
logger = get_logger()
logger.setLevel("DEBUG")
logger.debug("Verbose diagnostics enabled")
```

### Sending logs to additional handlers

```python
import logging
from backend.processors.logger import get_logger

logger = get_logger()
alert_handler = logging.StreamHandler()
alert_handler.setLevel(logging.ERROR)
logger.logger.addHandler(alert_handler)
```

---

## 📊 Performance

ProcessorLogger introduces negligible overhead in production use:

- Rich console formatting adds ~0.2 ms per message on modern hardware.
- Fallback mode uses the standard library only and is thread-safe.
- File rotation handlers flush asynchronously to minimize I/O blocking.

---

## 📝 Summary

### What's new in 2.1

- ✅ Unified ProcessorLogger for console and file output
- ✅ Rich-aware formatting with automatic fallback
- ✅ Helper methods for sections, panels, tables, and progress bars
- ✅ Sanitization utilities for PII-safe diagnostics
- ✅ Comprehensive environment-based configuration

### Benefits

- 📖 **Consistent** – same helper API across processors and scripts
- 🎨 **Readable** – rich formatting improves situational awareness
- 🛡️ **Safe** – masking utilities reduce accidental data leakage
- ⚡ **Efficient** – lightweight handlers keep pipelines fast
- 🧪 **Testable** – demo scripts verify setup end-to-end

---

**Last Updated**: October 29, 2025

**Version**: 2.1
