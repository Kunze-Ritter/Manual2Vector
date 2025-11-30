# Scripts Directory Documentation

## Overview

The `scripts/` directory contains standalone utilities for setup, maintenance, debugging, and automation tasks. These scripts are designed to be run independently and are not part of the main application backend/API.

## Core Utilities

| Script Name | Description | Usage | Status |
|------------|-------------|-------|--------|
| `_env.py` | Environment loader for all scripts | Imported by scripts | Active |
| `migration_helpers.py` | PostgreSQL adapter helpers (create_connected_adapter, pg_fetch_all, pg_execute) | Database operations | Active |
| `pipeline_processor.py` | CLI for stage-based pipeline control | Pipeline management | Active |

## Active Utilities

### Pipeline & Processing

| Script Name | Description | Usage | Status |
|------------|-------------|-------|--------|
| `auto_processor.py` | Auto-processing of PDFs using KRMasterPipeline | `python scripts/auto_processor.py` | Active |

### Database Management

| Script Name | Description | Usage | Status |
|------------|-------------|-------|--------|
| `cleanup_database.py` | Database cleanup operations | `python scripts/cleanup_database.py --dry-run` | Active |
| `delete_document_data.py` | Delete specific document data | `python scripts/delete_document_data.py <document_id>` | Active |
| `list_documents.py` | List all documents in database | `python scripts/list_documents.py` | Active |
| `sync_oem_to_database.py` | Sync OEM information to database | `python scripts/sync_oem_to_database.py` | Active |

### Video Enrichment

| Script Name | Description | Usage | Status |
|------------|-------------|-------|--------|
| `enrich_video_metadata.py` | YouTube metadata enrichment for videos | `python scripts/enrich_video_metadata.py --limit 50` | Active |
| `check_videos.py` | Video data quality checks | `python scripts/check_videos.py` | Active |
| `count_videos.py` | Count videos by manufacturer | `python scripts/count_videos.py` | Active |

### Storage Management

| Script Name | Description | Usage | Status |
|------------|-------------|-------|--------|
| `cleanup_r2_storage.py` | R2 storage cleanup operations | `python scripts/cleanup_r2_storage.py` | Active |
| `delete_r2_bucket_contents.py` | Delete R2 bucket contents | `python scripts/delete_r2_bucket_contents.py` | Active |
| `init_minio.py` | Initialize MinIO storage | `python scripts/init_minio.py` | Active |

### Setup & Configuration

| Script Name | Description | Usage | Status |
|------------|-------------|-------|--------|
| `setup_computer.py` | Computer setup configuration | `python scripts/setup_computer.py` | Active |
| `validate_env.py` | Environment validation | `python scripts/validate_env.py` | Active |
| `generate_jwt_keys.py` | Generate JWT keys for authentication | `python scripts/generate_jwt_keys.py` | Active |
| `generate_env_reference.py` | Generate environment reference documentation | `python scripts/generate_env_reference.py` | Active |

### Documentation Generation

| Script Name | Description | Usage | Status |
|------------|-------------|-------|--------|
| `generate_db_schema_doc.py` | Generate database schema documentation | `python scripts/generate_db_schema_doc.py` | Active |
| `generate_complete_db_doc.py` | Generate complete database documentation | `python scripts/generate_complete_db_doc.py` | Active |

### Git Hooks

| Script Name | Description | Usage | Status |
|------------|-------------|-------|--------|
| `install_git_hooks.py` | Install git hooks for repository | `python scripts/install_git_hooks.py` | Active |
| `git_hooks/pre_commit.py` | Pre-commit hook script | Installed automatically | Active |
| `git_hooks/commit_msg.py` | Commit message hook script | Installed automatically | Active |

### Windows Batch Scripts

| Script Name | Description | Usage | Status |
|------------|-------------|-------|--------|
| `verify_ollama.bat` | Verifies Ollama installation and GPU configuration | `.\scripts\verify_ollama.bat` | Active |
| `fix_ollama_gpu.bat` | Fixes common Ollama GPU detection issues | `.\scripts\fix_ollama_gpu.bat` | Active |
| `fix_vision_crashes.bat` | Troubleshoots vision model crashes | `.\scripts\fix_vision_crashes.bat` | Active |

## Fixes Subdirectory

The `fixes/` subdirectory contains one-time fix scripts for data corrections. See `scripts/fixes/README.md` for detailed documentation.

- `fix_document_metadata.py` - Correct faulty document metadata
- `fix_parts_catalog_products.py` - Fix parts catalog product associations
- `link_videos_to_products.py` - Link videos to products based on metadata
- `update_video_manufacturers.py` - Update manufacturer assignments for videos

## Usage Examples

### Pipeline Control
```bash
# List available stages
python scripts/pipeline_processor.py --list-stages

# Run specific stage for document
python scripts/pipeline_processor.py --document-id <uuid> --stage 5

# Smart processing (automatic stage detection)
python scripts/pipeline_processor.py --document-id <uuid> --smart
```

### Auto-Processing
```bash
# Process all PDFs in data directory
python scripts/auto_processor.py

# Process specific PDF
python scripts/auto_processor.py --pdf-file /path/to/file.pdf
```

### Database Management
```bash
# List all documents
python scripts/list_documents.py

# Dry-run cleanup (recommended first)
python scripts/cleanup_database.py --dry-run

# Actual cleanup
python scripts/cleanup_database.py
```

### Video Enrichment
```bash
# Enrich video metadata with limit
python scripts/enrich_video_metadata.py --limit 50

# Check video data quality
python scripts/check_videos.py

# Count videos by manufacturer
python scripts/count_videos.py
```

### Windows Troubleshooting
```bash
# Verify Ollama installation
.\scripts\verify_ollama.bat

# Fix Ollama GPU issues
.\scripts\fix_ollama_gpu.bat

# Fix vision model crashes
.\scripts\fix_vision_crashes.bat
```

## Archived Scripts

Scripts that are no longer actively needed have been archived to `archive/scripts/`. See `archive/scripts/README.md` for a comprehensive index of all archived scripts and their purposes.

Archived scripts are still available for reference or rollback if needed, but are not part of regular operations.

## Related Documentation

- `docs/PIPELINE_README.md` - Stage-based pipeline documentation
- `docs/STAGE_BASED_PROCESSING.md` - Stage-based processing API endpoints
- `MASTER-TODO.md` - Open tasks and project status
- `docs/PROJECT_CLEANUP_LOG.md` - Cleanup history and changes
- `docs/troubleshooting/OLLAMA_GPU_FIX.md`
- `docs/troubleshooting/VISION_MODEL_TROUBLESHOOTING.md`
- `docs/troubleshooting/GPU_AUTO_DETECTION.md`

## Script Categories

### Core Scripts (3)
Essential utilities used by many other scripts:
- `_env.py` - Environment management
- `migration_helpers.py` - Database helpers
- `pipeline_processor.py` - Pipeline control

### Active Utilities (~15)
Regularly used scripts for maintenance and operations:
- Database management scripts
- Video enrichment tools
- Storage management utilities
- Setup and configuration scripts
- Documentation generation tools

### Fix Scripts (4)
One-time data correction scripts in `fixes/` subdirectory

### Windows Batch Scripts (3)
Windows-specific troubleshooting scripts

All other scripts (100+) have been systematically archived to `archive/scripts/` with comprehensive documentation.
