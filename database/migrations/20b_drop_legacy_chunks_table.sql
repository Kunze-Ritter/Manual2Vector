-- ======================================================================
-- Migration 20b: Drop Legacy krai_content.chunks Table
-- ======================================================================
-- Description: Remove unused duplicate chunks table
-- Date: 2025-10-05
-- Purpose: Clean up schema - only krai_intelligence.chunks should exist
-- Prerequisite: Run 20a first to verify table is empty
-- ======================================================================

-- Drop dependent view first (if it exists)
DROP VIEW IF EXISTS public.vw_chunks CASCADE;

-- Drop the unused chunks table
DROP TABLE IF EXISTS krai_content.chunks CASCADE;

-- Verify table was dropped
SELECT 
    table_schema,
    table_name
FROM information_schema.tables
WHERE table_name = 'chunks'
ORDER BY table_schema;

-- Expected output:
-- | table_schema        | table_name |
-- |---------------------|------------|
-- | krai_intelligence   | chunks     |
--
-- (krai_content.chunks should be GONE)
