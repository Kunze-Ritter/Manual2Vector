# Archived Scripts Index and Documentation

## Overview

The `archive/scripts/` directory contains scripts that are no longer actively needed for regular operations but are preserved for reference, debugging, or potential rollback. Scripts are organized by category and include documentation about why they were archived.

## Archiving Categories

### A. Supabase Scripts (`supabase/`)

Already archived during KRAI-002 (Supabase removal).

| Script | Purpose | Archival Reason |
|--------|---------|-----------------|
| `test_supabase_connection.py` | Test Supabase connectivity | Full migration to PostgreSQL-only |
| `export_supabase_schema.py` | Export Supabase schema | PostgreSQL-only architecture |
| `import_supabase_data.py` | Import data to Supabase | PostgreSQL-only architecture |
| `migrate_from_supabase.py` | Migrate data from Supabase | Migration completed |
| `cleanup_supabase.py` | Cleanup Supabase resources | PostgreSQL-only architecture |
| `validate_supabase_sync.py` | Validate Supabase sync | PostgreSQL-only architecture |
| `supabase_backup.py` | Backup Supabase data | PostgreSQL-only architecture |

### B. Analysis Scripts (`analysis/`)

One-off analysis scripts for specific problems that have been resolved.

| Script | Purpose | Archival Reason |
|--------|---------|-----------------|
| `analyze_foliant_matrix.py` | Foliant compatibility matrix analysis | Specific compatibility issue resolved |
| `analyze_dependencies.py` | Project dependency analysis | Dependency analysis completed |
| `analyze_dependencies_corrected.py` | Corrected dependency analysis | Analysis completed |
| `analyze_all_foliants.py` | Comprehensive Foliant analysis | Foliant processing completed |
| `analyze_pandora_tables.py` | Pandora database table analysis | Pandora integration completed |
| `analyze_pdf_chars.py` | PDF character encoding analysis | Specific PDF issue resolved |
| `analyze_specific_pdf.py` | Analysis of specific PDF document | One-time analysis completed |
| `probe_pdf_patterns.py` | PDF pattern probing and detection | Pattern detection completed |

### C. Debug/Check Scripts (`debug/`)

Specific debugging scripts for individual documents or issues.

| Script | Purpose | Archival Reason |
|--------|---------|-----------------|
| `check_66_60_32_images.py` | Check images for document 66_60_32 | Document-specific, not reusable |
| `check_11_00_02.py` | Check document 11_00_02 | Document-specific, not reusable |
| `check_lexmark.py` | Check Lexmark-specific data | Manufacturer-specific issue resolved |
| `check_chunks_11_00_02.py` | Check chunks for document 11_00_02 | Document-specific debugging |
| `check_chunks_for_c9402.py` | Check chunks for error code C9402 | Specific error code debugging |
| `check_parts_for_11_00_02.py` | Check parts for document 11_00_02 | Document-specific parts debugging |
| `check_slot_article_codes.py` | Check slot article codes | Specific validation completed |
| `check_videos_x580.py` | Check X580 video data | Model-specific debugging |
| `check_unknown_videos.py` | Check unknown video entries | Replaced by generic video quality checks |
| `check_video_links.py` | Check video link integrity | Replaced by `check_video_data_quality.py` |
| `debug_video_links.py` | Debug video link issues | Debug version of check_video_links.py |
| `debug_extraction.py` | Debug extraction process | One-time extraction debugging |
| `debug_pdf_error_codes.py` | Debug PDF error code extraction | Specific error debugging completed |
| `find_error_with_real_images.py` | Find errors with real images | Specific image error debugging |
| `find_error_with_media2.py` | Find media errors (version 2) | Media error debugging iteration |
| `find_error_with_media.py` | Find media errors (version 1) | Media error debugging completed |
| `find_error_with_image.py` | Find image-related errors | Image error debugging completed |
| `search_code_in_pdf.py` | Search specific codes in PDFs | One-time code search |
| `search_pdf_string.py` | Search strings in PDFs | One-time string search |
| `search_compatibility_logic.py` | Search compatibility logic | One-time logic search |
| `search_similar_codes.py` | Find similar error codes | One-time similarity analysis |

### D. Migration Scripts (`migrations/`)

Old migration application scripts.

| Script | Purpose | Archival Reason |
|--------|---------|-----------------|
| `apply_migration_14.py` | Apply database migration 14 | Migration completed, DB schema stable |
| `apply_migration_81.bat` | Apply database migration 81 | Migration completed, DB schema stable |
| `apply_migration_82.py` | Apply database migration 82 | Migration completed, DB schema stable |
| `apply_migration_82.bat` | Apply database migration 82 | Migration completed, DB schema stable |
| `apply_migration_123.py` | Apply database migration 123 | Migration completed, DB schema stable |
| `export_schema_for_migration_123.py` | Export schema for migration 123 | Migration completed |
| `MIGRATION_STATUS.md` | Migration status documentation | Outdated, migrations completed |

### E. Test Scripts (`tests/`)
Integration and smoke tests that should be in the `tests/` directory.

| Script | Purpose | Archival Reason |
|--------|---------|-----------------|
| `test_version_hook.py` | Test version hook functionality | Should be in tests/ directory |
| `test_vector_extraction.py` | Test vector extraction | Redundant with tests/processors/test_embedding_processor.py |
| `test_svg_extraction.py` | Test SVG extraction | Should be in tests/ directory |
| `test_postgresql_migrations.py` | Test PostgreSQL migrations | DB schema stable, migrations completed |
| `test_postgresql_connection_simple.py` | Test PostgreSQL connection | Redundant with tests/test_database_adapters.py |
| `test_playwright_endpoint.py` | Test Playwright endpoint | Should be in tests/ directory |
| `test_playwright_docker.py` | Test Playwright Docker setup | Should be in tests/ directory |
| `test_phase6_integration.py` | Test Phase 6 integration | Deprecated pipeline phase |
| `test_page_labels.py` | Test page label extraction | Should be in tests/ directory |
| `test_multimodal_search.py` | Test multimodal search | Should be in tests/ directory |
| `test_monitoring.py` | Test monitoring system | Redundant with tests/test_monitoring_system.py |
| `test_minio_storage_operations.py` | Test MinIO storage operations | Should be in tests/ directory |
| `test_migration_helpers.py` | Test migration helpers | Should be in tests/ if still relevant |
| `test_hp_pattern.py` | Test HP pattern matching | Redundant with tests/test_hp_series.py |
| `test_hierarchical_chunking.py` | Test hierarchical chunking | Should be in tests/ directory |
| `test_generic_check.py` | Generic check functionality | Should be in tests/ directory |
| `test_full_pipeline_phases_1_6.py` | Test full pipeline phases 1-6 | Deprecated pipeline stages |
| `test_error_code_extraction.py` | Test error code extraction | Should be in tests/ directory |
| `test_context_extraction_integration.py` | Test context extraction integration | Should be in tests/ directory |
| `test_content_text_usefulness.py` | Test content text usefulness | Should be in tests/ directory |
| `test_adapter_quick.py` | Quick adapter test | Redundant with tests/test_database_adapters.py |

### F. Extraction/Import Scripts (`extraction/`)

Specific data extraction and import scripts that completed their tasks.

| Script | Purpose | Archival Reason |
|--------|---------|-----------------|
| `extract_foliant_logic.py` | Extract Foliant compatibility logic | Foliant extraction completed |
| `extract_registry_from_pdf.py` | Extract registry data from PDFs | Registry extraction completed |
| `extract_pdf_javascript.py` | Extract JavaScript from PDFs | JavaScript extraction completed |
| `extract_js_simple.py` | Simple JavaScript extraction | JavaScript extraction completed |
| `extract_article_codes_for_slots.py` | Extract article codes for slots | Article code extraction completed |
| `extract_all_sprites.py` | Extract all sprite data | Sprite extraction completed |
| `extract_all_javascript.py` | Extract all JavaScript | JavaScript extraction completed |
| `import_foliant_to_db.py` | Import Foliant data to database | Foliant import completed |
| `import_all_foliants.py` | Import all Foliant data | Foliant import completed |
| `parse_foliant_compatibility.py` | Parse Foliant compatibility data | Foliant parsing completed |
| `parse_foliant_data.py` | Parse Foliant data structures | Foliant parsing completed |
| `build_compatibility_matrix.py` | Build compatibility matrix | Matrix building completed |

### G. Deprecated Utilities (`deprecated/`)
Old utility scripts replaced by newer implementations.

| Script | Purpose | Archival Reason |
|--------|---------|-----------------|
| `cleanup_internal_sprites.py` | Cleanup internal sprite data | Replaced by cleanup_database.py |
| `cleanup_orphaned_data.py` | Cleanup orphaned data | Replaced by cleanup_database.py |
| `cleanup_production_db.py` | Cleanup production database | Replaced by cleanup_database.py |
| `cleanup_orphaned_chunks.py` | Cleanup orphaned chunks | Replaced by cleanup_database.py |
| `cleanup_r2_images_with_hashes.py` | Cleanup R2 images with hashes | Replaced by cleanup_r2_storage.py |
| `cleanup_test_environment.py` | Cleanup test environment | Replaced by setup_test_environment.py |
| `deduplicate_error_codes.py` | Deduplicate error codes | One-time deduplication completed |
| `delete_by_manufacturer.py` | Delete data by manufacturer | Replaced by delete_document_data.py |
| `delete_konica_minolta_data.py` | Delete Konica Minolta data | Manufacturer-specific cleanup completed |
| `delete_all_processed_data.py` | Delete all processed data | Dangerous, replaced by cleanup_database.py |
| `refactor_to_vw_prefix.py` | Refactor to vw prefix | One-time refactoring completed |
| `update_documentation_references.py` | Update documentation references | One-time documentation update |
| `clean_openai_api.py` | Clean OpenAI API usage | No longer relevant |
| `generate_phase_7_report.py` | Generate Phase 7 report | Deprecated pipeline phase |
| `export_page_12.py` | Export specific page 12 | Document-specific export |
| `find_registry_logic.py` | Find registry logic | One-time registry search |

### H. Setup Scripts (`setup/`)

Old setup scripts replaced by Docker-based processes.

| Script | Purpose | Archival Reason |
|--------|---------|-----------------|
| `setup_test_environment.py` | Setup test environment | Docker-based setup now |
| `setup-n8n-https.ps1` | Setup n8n with HTTPS | No longer used |
| `setup-cloudflare-tunnel.ps1` | Setup Cloudflare tunnel | No longer used |
| `start_agent_env.ps1` | Start agent environment | No longer used |
| `start_ollama.ps1` | Start Ollama service | Docker-based setup now |
| `reload_postgrest_schema.py` | Reload PostgREST schema | No PostgREST anymore |

### I. Visualization Scripts (`visualization/`)
One-time visualization and display scripts.

| Script | Purpose | Archival Reason |
|--------|---------|-----------------|
| `visualize_foliant_config.py` | Visualize Foliant configuration | One-time visualization |
| `show_pandora.py` | Display Pandora data | One-time data display |
| `show_slot_sprites.py` | Display slot sprites | One-time visualization |
| `show_article_code_examples.py` | Show article code examples | One-time examples display |
| `inspect_pdf_page.py` | Inspect PDF page structure | One-time inspection |
| `inspect_pdf_structured.py` | Inspect structured PDF data | One-time inspection |
| `diagnose_structured_text.py` | Diagnose structured text issues | One-time diagnosis |

## Migration Table

| Original Script | Archive Path | Archive Date | Reason | Replaced By |
|----------------|--------------|--------------|--------|-------------|
| `analyze_foliant_matrix.py` | `archive/scripts/analysis/` | 2025-11-29 | One-off analysis completed | N/A |
| `test_postgresql_connection_simple.py` | `archive/scripts/tests/` | 2025-11-29 | Redundant with existing tests | `tests/test_database_adapters.py` |
| `cleanup_orphaned_data.py` | `archive/scripts/deprecated/` | 2025-11-29 | Replaced by unified cleanup | `cleanup_database.py` |
| `setup_test_environment.py` | `archive/scripts/setup/` | 2025-11-29 | Docker-based setup | Docker containers |
| `check_video_links.py` | `archive/scripts/debug/` | 2025-11-29 | Replaced by generic checks | `check_video_data_quality.py` |

## Rollback Guidelines

If you need to reactivate an archived script:

1. **Check Git History**: Review the commit history to understand why it was archived
2. **Update Dependencies**: Update imports and dependencies to match current codebase
3. **Test Thoroughly**: Ensure the script works with current database schema and API
4. **Consider Integration**: Evaluate if the functionality should be integrated into existing active scripts
5. **Update Documentation**: Update relevant documentation if reactivating

## Archive Statistics

- **Total Scripts Archived**: 100+
- **Analysis Scripts**: 8
- **Debug/Check Scripts**: 22
- **Migration Scripts**: 7
- **Test Scripts**: 17
- **Extraction/Import Scripts**: 13
- **Deprecated Utilities**: 14
- **Setup Scripts**: 6
- **Visualization Scripts**: 7
- **Supabase Scripts**: 7 (already archived)

## Related Documentation

- `scripts/README.md` - Active scripts documentation
- `docs/PROJECT_CLEANUP_LOG.md` - Detailed cleanup history
- `MASTER-TODO.md` - Project status and open tasks
- KRAI-002 documentation - Supabase removal
- KRAI-003 documentation - Pipeline refactoring

## Notes

- All archived scripts retain their original Git history
- Scripts are archived, not deleted, to maintain project history
- Some scripts may contain outdated dependencies or imports
- Review script compatibility before reactivating archived scripts
- Consider creating new scripts based on archived functionality rather than direct reactivation
