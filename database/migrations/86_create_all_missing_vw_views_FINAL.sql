-- Migration 86: Create ALL missing vw_ views - FINAL FIX
-- ======================================================================
-- Description: Systematically create ALL vw_ views that are actually used in code
-- Date: 2025-10-17
-- Reason: Complete fix - no more PGRST205 errors
-- ======================================================================

-- ======================================================================
-- CORE VIEWS (from krai_core schema)
-- ======================================================================

-- vw_documents (MAIN TABLE - MUST EXIST!)
CREATE OR REPLACE VIEW public.vw_documents AS 
SELECT * FROM krai_core.documents;

-- vw_manufacturers
CREATE OR REPLACE VIEW public.vw_manufacturers AS 
SELECT * FROM krai_core.manufacturers;

-- vw_products
CREATE OR REPLACE VIEW public.vw_products AS 
SELECT * FROM krai_core.products;

-- vw_product_series
CREATE OR REPLACE VIEW public.vw_product_series AS 
SELECT * FROM krai_core.product_series;

-- vw_document_products (junction table)
CREATE OR REPLACE VIEW public.vw_document_products AS 
SELECT * FROM krai_core.document_products;

-- ======================================================================
-- CONTENT VIEWS (from krai_content schema)
-- ======================================================================

-- vw_chunks
CREATE OR REPLACE VIEW public.vw_chunks AS 
SELECT * FROM krai_content.chunks;

-- vw_links
CREATE OR REPLACE VIEW public.vw_links AS 
SELECT * FROM krai_content.links;

-- vw_videos
CREATE OR REPLACE VIEW public.vw_videos AS 
SELECT * FROM krai_content.videos;

-- vw_images
CREATE OR REPLACE VIEW public.vw_images AS 
SELECT * FROM krai_content.images;

-- vw_video_products (junction table)
CREATE OR REPLACE VIEW public.vw_video_products AS 
SELECT * FROM krai_content.video_products;

-- ======================================================================
-- PARTS VIEWS (from krai_parts schema)
-- ======================================================================

-- vw_parts (NOT parts_catalog!)
CREATE OR REPLACE VIEW public.vw_parts AS 
SELECT * FROM krai_parts.parts;

-- ======================================================================
-- ERROR CODE VIEWS (from krai_error_codes schema)
-- ======================================================================

-- vw_error_codes
CREATE OR REPLACE VIEW public.vw_error_codes AS 
SELECT * FROM krai_error_codes.error_codes;

-- ======================================================================
-- EMBEDDINGS VIEWS (from krai_embeddings schema)
-- ======================================================================

-- vw_embeddings
CREATE OR REPLACE VIEW public.vw_embeddings AS 
SELECT * FROM krai_embeddings.embeddings;

-- ======================================================================
-- INTELLIGENCE VIEWS (from krai_intelligence schema)
-- ======================================================================

-- vw_intelligence_chunks
CREATE OR REPLACE VIEW public.vw_intelligence_chunks AS 
SELECT * FROM krai_intelligence.chunks;

-- ======================================================================
-- SYSTEM VIEWS (from krai_system schema)
-- ======================================================================

-- vw_processing_queue
CREATE OR REPLACE VIEW public.vw_processing_queue AS 
SELECT * FROM krai_system.processing_queue;

-- vw_system_metrics
CREATE OR REPLACE VIEW public.vw_system_metrics AS 
SELECT * FROM krai_system.system_metrics;

-- vw_audit_log
CREATE OR REPLACE VIEW public.vw_audit_log AS 
SELECT * FROM krai_system.audit_log;

-- vw_webhook_logs
CREATE OR REPLACE VIEW public.vw_webhook_logs AS 
SELECT * FROM krai_system.webhook_logs;

-- ======================================================================
-- ANALYTICS VIEWS (from krai_analytics schema)
-- ======================================================================

-- vw_search_analytics
CREATE OR REPLACE VIEW public.vw_search_analytics AS 
SELECT * FROM krai_analytics.search_analytics;

-- vw_agent_memory
CREATE OR REPLACE VIEW public.vw_agent_memory AS 
SELECT * FROM krai_analytics.agent_memory;

-- ======================================================================
-- GRANT PERMISSIONS TO ALL VIEWS
-- ======================================================================

-- Core views
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_documents TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_manufacturers TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_products TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_product_series TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_document_products TO anon, authenticated, service_role;

-- Content views
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_chunks TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_links TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_videos TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_images TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_video_products TO anon, authenticated, service_role;

-- Parts views
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_parts TO anon, authenticated, service_role;

-- Error code views
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_error_codes TO anon, authenticated, service_role;

-- Embeddings views
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_embeddings TO anon, authenticated, service_role;

-- Intelligence views
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_intelligence_chunks TO anon, authenticated, service_role;

-- System views
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_processing_queue TO anon, authenticated, service_role;
GRANT SELECT ON public.vw_system_metrics TO anon, authenticated, service_role;
GRANT SELECT, INSERT ON public.vw_audit_log TO anon, authenticated, service_role;
GRANT SELECT, INSERT ON public.vw_webhook_logs TO anon, authenticated, service_role;

-- Analytics views
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_search_analytics TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_agent_memory TO anon, authenticated, service_role;

-- ======================================================================
-- VERIFICATION
-- ======================================================================

-- Check all vw_ views exist:
-- SELECT schemaname, viewname 
-- FROM pg_views 
-- WHERE schemaname = 'public' 
--   AND viewname LIKE 'vw_%'
-- ORDER BY viewname;

-- Should show 18 views:
-- vw_agent_memory
-- vw_audit_log
-- vw_chunks
-- vw_document_products
-- vw_documents
-- vw_embeddings
-- vw_error_codes
-- vw_images
-- vw_intelligence_chunks
-- vw_links
-- vw_manufacturers
-- vw_parts
-- vw_processing_queue
-- vw_product_series
-- vw_products
-- vw_search_analytics
-- vw_system_metrics
-- vw_video_products
-- vw_videos
-- vw_webhook_logs
