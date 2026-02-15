# Processor Tables / DB Matrix

Purpose: clear separation between DB objects required for the KR processor pipeline and objects used by other modules.

## 1) Processor Runtime (required)

These objects are required for regular stage execution (`upload -> ... -> embedding/search`) and resilience features.

### Core document flow
- `krai_core.documents`
- `krai_content.chunks`
- `krai_content.images`
- `krai_content.links`
- `krai_content.videos`
- `krai_intelligence.chunks`
- `krai_intelligence.structured_tables`
- `krai_intelligence.unified_embeddings`
- `krai_intelligence.error_codes`

### Classification / product enrichment
- `krai_core.manufacturers`
- `krai_core.products`
- `krai_core.product_series`
- `krai_core.document_products`
- `krai_core.product_accessories`
- `krai_parts.parts_catalog`
- `krai_intelligence.manufacturer_verification_cache`

### Pipeline orchestration / resilience
- `krai_system.processing_queue`
- `krai_system.stage_tracking`
- `krai_system.stage_metrics`
- `krai_system.stage_completion_markers`
- `krai_system.pipeline_errors`
- `krai_system.retry_policies`
- `krai_system.performance_baselines`

### Required RPC functions in `krai_core`
- `start_stage`
- `update_stage_progress`
- `complete_stage`
- `fail_stage`
- `skip_stage`
- `get_document_progress`
- `get_current_stage`
- `can_start_stage`

## 2) Other modules (not required for core processor run)

These are valid DB objects but not mandatory for basic processor execution.

### Auth / user management
- `krai_users.users`
- `krai_users.user_sessions`
- `krai_users.token_blacklist`
- `krai_integrations.api_keys`
- `krai_integrations.webhook_logs`

### Crawling / scraping
- `krai_system.link_scraping_jobs`
- `krai_system.manufacturer_crawl_schedules`
- `krai_system.manufacturer_crawl_jobs`
- `krai_system.crawled_pages`

### Configuration / service / analytics
- `krai_config.option_groups`
- `krai_config.product_features`
- `krai_config.product_compatibility`
- `krai_config.competition_analysis`
- `krai_service.technicians`
- `krai_service.service_calls`
- `krai_service.service_history`
- `krai_analytics.search_analytics`
- `krai_system.audit_log`
- `krai_system.health_checks`
- `krai_system.alert_configurations`
- `krai_system.alert_queue`

## 3) Fast health checks

### A. Missing processor tables
```sql
SELECT obj
FROM (
  VALUES
    ('krai_core.documents'),
    ('krai_content.chunks'),
    ('krai_content.images'),
    ('krai_intelligence.chunks'),
    ('krai_intelligence.structured_tables'),
    ('krai_intelligence.unified_embeddings'),
    ('krai_system.processing_queue'),
    ('krai_system.stage_tracking'),
    ('krai_system.stage_completion_markers'),
    ('krai_system.pipeline_errors'),
    ('krai_system.retry_policies')
) required(obj)
LEFT JOIN (
  SELECT table_schema || '.' || table_name AS obj
  FROM information_schema.tables
  WHERE table_schema LIKE 'krai_%'
) existing USING (obj)
WHERE existing.obj IS NULL;
```

### B. Missing stage RPCs
```sql
SELECT fn
FROM (
  VALUES
    ('start_stage'),
    ('update_stage_progress'),
    ('complete_stage'),
    ('fail_stage'),
    ('skip_stage'),
    ('get_document_progress'),
    ('get_current_stage'),
    ('can_start_stage')
) required(fn)
LEFT JOIN (
  SELECT proname
  FROM pg_proc p
  JOIN pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname = 'krai_core'
) existing ON existing.proname = required.fn
WHERE existing.proname IS NULL;
```

## 4) Current note (environment-specific)

`krai_system.pipeline_errors` had schema drift and was patched live to include runtime columns used by:
- `backend/services/error_logging_service.py`
- `backend/core/retry_engine.py`

This should be captured in your persistent migration flow for new environments.
