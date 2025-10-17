-- Migration 83: Remove non-vw_ views (keep only vw_ prefixed views)
-- ======================================================================
-- Description: Clean naming - all views use vw_ prefix for clarity
-- Date: 2025-10-17
-- Reason: Consistent naming convention (vw_ = view, no prefix = table)
-- ======================================================================

-- ======================================================================
-- STRATEGY:
-- - Keep all vw_ prefixed views (main views)
-- - Drop all non-vw_ views (they were aliases/duplicates)
-- - Code now uses vw_ prefix exclusively
-- ======================================================================

-- ======================================================================
-- Drop old views without vw_ prefix
-- ======================================================================

-- Core views
DROP VIEW IF EXISTS public.documents CASCADE;
DROP VIEW IF EXISTS public.manufacturers CASCADE;
DROP VIEW IF EXISTS public.products CASCADE;
DROP VIEW IF EXISTS public.error_codes CASCADE;
DROP VIEW IF EXISTS public.chunks CASCADE;

-- Content views
DROP VIEW IF EXISTS public.links CASCADE;
DROP VIEW IF EXISTS public.videos CASCADE;
DROP VIEW IF EXISTS public.images CASCADE;

-- Parts view
DROP VIEW IF EXISTS public.parts_catalog CASCADE;

-- Embeddings view (if exists without vw_ prefix)
DROP VIEW IF EXISTS public.embeddings CASCADE;

-- ======================================================================
-- RESULT:
-- All tables now accessed via vw_ prefix:
-- - vw_documents, vw_manufacturers, vw_products
-- - vw_error_codes, vw_chunks, vw_embeddings
-- - vw_links, vw_videos, vw_images
-- - vw_parts
-- 
-- Benefits:
-- - Clear distinction: vw_ = view, no prefix = table
-- - No duplicate views
-- - Consistent naming across entire codebase
-- ======================================================================

-- ======================================================================
-- Verification
-- ======================================================================

-- Check all public views now have vw_ prefix:
-- SELECT schemaname, viewname 
-- FROM pg_views 
-- WHERE schemaname = 'public'
-- ORDER BY viewname;

-- Should show only vw_ prefixed views:
-- vw_agent_memory
-- vw_audit_log
-- vw_chunks
-- vw_documents
-- vw_embeddings
-- vw_error_codes
-- vw_images
-- vw_links
-- vw_manufacturers
-- vw_parts
-- vw_processing_queue
-- vw_products
-- vw_search_analytics
-- vw_videos
-- vw_webhook_logs
