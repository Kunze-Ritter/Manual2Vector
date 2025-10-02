-- ===========================================
-- COMPLETE AGENT VIEWS FOR POSTGREST ACCESS
-- ===========================================
-- All krai_* schemas accessible via public views for Agent/PostgREST

-- Drop existing agent views
DROP VIEW IF EXISTS public.vw_audit_log CASCADE;
DROP VIEW IF EXISTS public.vw_processing_queue CASCADE;
DROP VIEW IF EXISTS public.vw_documents CASCADE;
DROP VIEW IF EXISTS public.vw_error_codes CASCADE;
DROP VIEW IF EXISTS public.vw_webhook_logs CASCADE;
DROP VIEW IF EXISTS public.vw_manufacturers CASCADE;
DROP VIEW IF EXISTS public.vw_products CASCADE;

-- ============================================
-- SYSTEM VIEWS (Logs, Queue, Metrics)
-- ============================================

-- Audit Log (THE LOG for Agent!)
CREATE OR REPLACE VIEW public.vw_audit_log AS
SELECT 
    id, table_name, record_id, operation, old_values, new_values,
    changed_by, changed_at, session_id, ip_address, user_agent
FROM krai_system.audit_log;

-- Processing Queue (Task Status)
CREATE OR REPLACE VIEW public.vw_processing_queue AS
SELECT 
    id, document_id, chunk_id, image_id, video_id, task_type,
    priority, status, scheduled_at, started_at, completed_at,
    error_message, retry_count, max_retries, created_at
FROM krai_system.processing_queue;

-- ============================================
-- CORE VIEWS (Documents, Manufacturers, Products)
-- ============================================

-- Documents (Essential for Agent!)
CREATE OR REPLACE VIEW public.vw_documents AS
SELECT 
    id, manufacturer_id, product_id, filename, original_filename,
    file_size, file_hash, storage_path, storage_url, document_type,
    language, version, publish_date, page_count, word_count, character_count,
    content_text, content_summary, extracted_metadata, processing_status,
    confidence_score, manual_review_required, manual_review_completed,
    manual_review_notes, ocr_confidence, created_at, updated_at,
    manufacturer, series, models
FROM krai_core.documents;

-- Manufacturers (corrected columns)
CREATE OR REPLACE VIEW public.vw_manufacturers AS
SELECT 
    id, name, short_name, country, founded_year, website, support_email, support_phone,
    logo_url, is_competitor, market_share_percent, annual_revenue_usd, employee_count,
    headquarters_address, stock_symbol, primary_business_segment, created_at, updated_at
FROM krai_core.manufacturers;

-- Products (corrected columns)
CREATE OR REPLACE VIEW public.vw_products AS
SELECT 
    id, parent_id, manufacturer_id, series_id, model_number, model_name,
    product_type, launch_date, end_of_life_date, msrp_usd, weight_kg, dimensions_mm,
    color_options, connectivity_options, print_technology, max_print_speed_ppm,
    max_resolution_dpi, max_paper_size, duplex_capable, network_capable,
    mobile_print_support, supported_languages, energy_star_certified, warranty_months,
    service_manual_url, parts_catalog_url, driver_download_url, firmware_version,
    option_dependencies, replacement_parts, common_issues, created_at, updated_at
FROM krai_core.products;

-- ============================================
-- INTELLIGENCE VIEWS (Error Codes)
-- ============================================

-- Error Codes (Important for troubleshooting!)
CREATE OR REPLACE VIEW public.vw_error_codes AS
SELECT 
    id, chunk_id, document_id, manufacturer_id, error_code, error_description,
    solution_text, page_number, confidence_score, extraction_method,
    requires_technician, requires_parts, estimated_fix_time_minutes,
    severity_level, created_at
FROM krai_intelligence.error_codes;

-- ============================================
-- INTEGRATION VIEWS (Webhooks)
-- ============================================

-- Webhook Logs (corrected columns)
CREATE OR REPLACE VIEW public.vw_webhook_logs AS
SELECT 
    id, webhook_url, request_payload, response_status, response_body, processed_at
FROM krai_integrations.webhook_logs;

-- ============================================
-- GRANTS
-- ============================================

-- Grant SELECT to all roles
GRANT SELECT ON public.vw_audit_log TO anon, authenticated, service_role;
GRANT SELECT ON public.vw_processing_queue TO anon, authenticated, service_role;
GRANT SELECT ON public.vw_documents TO anon, authenticated, service_role;
GRANT SELECT ON public.vw_manufacturers TO anon, authenticated, service_role;
GRANT SELECT ON public.vw_products TO anon, authenticated, service_role;
GRANT SELECT ON public.vw_error_codes TO anon, authenticated, service_role;
GRANT SELECT ON public.vw_webhook_logs TO anon, authenticated, service_role;

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON VIEW public.vw_audit_log IS 'Agent Log: All system changes and operations';
COMMENT ON VIEW public.vw_processing_queue IS 'Agent Queue: Current task status and history';
COMMENT ON VIEW public.vw_documents IS 'Agent Documents: All document metadata and content';
COMMENT ON VIEW public.vw_error_codes IS 'Agent Knowledge: Error codes and solutions';
COMMENT ON VIEW public.vw_webhook_logs IS 'Agent Integrations: Webhook event history';
COMMENT ON VIEW public.vw_manufacturers IS 'Agent Context: Manufacturer information';
COMMENT ON VIEW public.vw_products IS 'Agent Context: Product specifications';

-- ============================================
-- AGENT MEMORY (See migration 07_agent_memory_table.sql)
-- ============================================
-- Memory table created in separate migration:
-- - krai_agent.memory (n8n Postgres Memory Module compatible)
-- - public.vw_agent_memory (PostgREST accessible)
--
-- FUTURE: Add feedback table when needed:
-- CREATE OR REPLACE VIEW public.vw_agent_feedback AS SELECT * FROM krai_agent.feedback;
