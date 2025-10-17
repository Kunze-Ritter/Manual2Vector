-- Migration 85: Cleanup all data before fresh reprocessing
-- ======================================================================
-- Description: Delete all documents, products, content (videos/links/images)
-- Date: 2025-10-17
-- Reason: Fresh start with new video-product linking and vw_ views
-- ======================================================================

-- ⚠️  WARNING: This will delete ALL processed data!
-- ⚠️  Manufacturers will be kept (they are correct)
-- ⚠️  Schema/Views will be kept (they are correct)

-- ======================================================================
-- PART 1: Delete all content (videos, links, images)
-- ======================================================================

-- Delete videos (will cascade to video_products)
DELETE FROM krai_content.videos;

-- Delete links
DELETE FROM krai_content.links;

-- Delete images
DELETE FROM krai_content.images;

-- ======================================================================
-- PART 2: Delete all intelligence data
-- ======================================================================

-- Delete intelligence chunks (deduplicated chunks)
DELETE FROM krai_intelligence.chunks;

-- ======================================================================
-- PART 3: Delete all products and relationships
-- ======================================================================

-- Delete document-product relationships
DELETE FROM krai_core.document_products;

-- Delete products (keep product_series for now)
DELETE FROM krai_core.products;

-- ======================================================================
-- PART 4: Delete all document data (CASCADE will handle embeddings/chunks)
-- ======================================================================

-- Delete embeddings (will be recreated)
DELETE FROM krai_embeddings.embeddings;

-- Delete chunks (will be recreated)
DELETE FROM krai_content.chunks;

-- Delete documents (this is the main table)
DELETE FROM krai_core.documents;

-- ======================================================================
-- PART 5: Clear processing queue
-- ======================================================================

DELETE FROM krai_system.processing_queue;

-- ======================================================================
-- PART 6: Clear audit log (optional - keeps history clean)
-- ======================================================================

-- Uncomment if you want to clear audit log:
-- DELETE FROM krai_system.audit_log;

-- ======================================================================
-- WHAT IS KEPT:
-- ======================================================================
-- ✅ Manufacturers (krai_core.manufacturers)
-- ✅ Product Series (krai_core.product_series)
-- ✅ All Views (vw_*)
-- ✅ All Functions/Triggers
-- ✅ All Schemas
-- ✅ System Metrics (krai_system.system_metrics)

-- ======================================================================
-- RESULT:
-- ======================================================================
-- Database is now clean and ready for fresh processing with:
-- - New video-product linking
-- - Consistent vw_ prefix views
-- - Clean data structure

-- ======================================================================
-- Verification
-- ======================================================================

-- Check counts (should all be 0):
-- SELECT 
--   (SELECT COUNT(*) FROM krai_core.documents) as documents,
--   (SELECT COUNT(*) FROM krai_core.products) as products,
--   (SELECT COUNT(*) FROM krai_content.chunks) as chunks,
--   (SELECT COUNT(*) FROM krai_embeddings.embeddings) as embeddings,
--   (SELECT COUNT(*) FROM krai_intelligence.chunks) as intelligence_chunks,
--   (SELECT COUNT(*) FROM krai_content.videos) as videos,
--   (SELECT COUNT(*) FROM krai_content.links) as links,
--   (SELECT COUNT(*) FROM krai_content.images) as images;

-- Check what's kept (should have data):
-- SELECT 
--   (SELECT COUNT(*) FROM krai_core.manufacturers) as manufacturers,
--   (SELECT COUNT(*) FROM krai_core.product_series) as product_series;
