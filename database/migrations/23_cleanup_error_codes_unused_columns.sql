-- ======================================================================
-- Migration 23: Cleanup Unused Error Code Columns
-- ======================================================================
-- Description: Remove unused columns from error_codes table
-- Date: 2025-10-05
-- Reason: Supabase PostgREST cache issues + unused fields
-- ======================================================================

-- Remove ALL Migration 09 columns (Supabase PostgREST cache is broken for them!)
ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS ai_extracted;

ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS verified;

ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS verified_by;

ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS verified_at;

ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS context_text;

ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS metadata;

-- Keep these useful columns (BASE SCHEMA - Migration 01):
-- - image_id: Links to screenshot (will be populated via SQL function)
-- - chunk_id: Links to text context (will be populated via SQL function)
-- - extraction_method: How error was found (BASE SCHEMA)
-- All other essential fields from BASE SCHEMA remain

-- NOTE: image_id and chunk_id linking happens AFTER initial INSERT
-- via link_error_codes_to_chunks_and_images() SQL function

-- ======================================================================
-- Verification
-- ======================================================================

-- Show remaining columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'krai_intelligence'
  AND table_name = 'error_codes'
ORDER BY ordinal_position;

-- Expected output: Should NOT show ai_extracted, verified, verified_by, verified_at, context_text, metadata
-- SHOULD show: image_id, chunk_id (from Migration 09 - these work!)
