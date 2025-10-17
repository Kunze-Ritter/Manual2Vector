-- Migration 84: Create missing vw_ views for remaining tables
-- ======================================================================
-- Description: Complete vw_ coverage for all accessed tables
-- Date: 2025-10-17
-- Reason: Consistent vw_ prefix for ALL table access
-- ======================================================================

-- ======================================================================
-- PART 1: Drop old views without vw_ prefix (if they exist)
-- ======================================================================

DROP VIEW IF EXISTS public.product_series CASCADE;
DROP VIEW IF EXISTS public.document_products CASCADE;
DROP VIEW IF EXISTS public.video_products CASCADE;
DROP VIEW IF EXISTS public.system_metrics CASCADE;
DROP VIEW IF EXISTS public.intelligence_chunks CASCADE;
DROP VIEW IF EXISTS public.processing_queue CASCADE;
DROP VIEW IF EXISTS public.images CASCADE;

-- ======================================================================
-- PART 2: Create vw_ views for tables that don't have them yet
-- ======================================================================

-- product_series (used in manufacturer_utils, series_processor, master_pipeline)
CREATE OR REPLACE VIEW public.vw_product_series AS
SELECT * FROM krai_core.product_series;

-- document_products (used in master_pipeline for relationships)
CREATE OR REPLACE VIEW public.vw_document_products AS
SELECT * FROM krai_core.document_products;

-- video_products (used in manufacturer_utils for video-product links)
CREATE OR REPLACE VIEW public.vw_video_products AS
SELECT * FROM krai_content.video_products;

-- system_metrics (used in database_service for health checks)
CREATE OR REPLACE VIEW public.vw_system_metrics AS
SELECT * FROM krai_system.system_metrics;

-- intelligence_chunks (used in database_service, quality_check_service)
-- NOTE: This is krai_intelligence.chunks (NOT krai_content.chunks!)
CREATE OR REPLACE VIEW public.vw_intelligence_chunks AS
SELECT * FROM krai_intelligence.chunks;

-- ======================================================================
-- Grant permissions
-- ======================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_product_series TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_document_products TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_video_products TO anon, authenticated, service_role;
GRANT SELECT ON public.vw_system_metrics TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_intelligence_chunks TO anon, authenticated, service_role;

-- ======================================================================
-- RESULT:
-- All frequently accessed tables now have vw_ views:
-- - vw_product_series
-- - vw_document_products
-- - vw_video_products
-- - vw_system_metrics
--
-- Tables that DON'T need views (internal/junction):
-- - error_code_images (junction table)
-- - intelligence_chunks (internal krai_intelligence)
-- - document_vectors (pgvector internal)
-- - print_defects (rarely used)
-- ======================================================================

-- ======================================================================
-- Verification
-- ======================================================================

-- Check all vw_ views exist:
-- SELECT schemaname, viewname 
-- FROM pg_views 
-- WHERE schemaname = 'public' 
--   AND viewname LIKE 'vw_%'
-- ORDER BY viewname;

-- Should now include:
-- vw_document_products
-- vw_product_series
-- vw_system_metrics
-- vw_video_products
