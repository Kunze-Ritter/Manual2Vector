-- ======================================================================
-- Migration 23: Cleanup Unused Error Code Columns
-- ======================================================================
-- Description: Remove unused columns from error_codes table
-- Date: 2025-10-05
-- Reason: Supabase PostgREST cache issues + unused fields
-- ======================================================================

-- Remove ai_extracted (causing cache issues, not used)
ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS ai_extracted;

-- Remove verified columns (not currently used)
-- Can be re-added later if needed for quality control workflow
ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS verified;

ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS verified_by;

ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS verified_at;

-- Keep these useful columns:
-- - image_id: Links to screenshot (ACTIVELY USED)
-- - context_text: Surrounding text (ACTIVELY USED)
-- - metadata: Flexible JSONB (ACTIVELY USED for smart matching info)
-- - extraction_method: How error was found (ACTIVELY USED)
-- - chunk_id: Links to text context (ACTIVELY USED)

-- ======================================================================
-- Verification
-- ======================================================================

-- Show remaining columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'krai_intelligence'
  AND table_name = 'error_codes'
ORDER BY ordinal_position;

-- Expected output: Should NOT show ai_extracted, verified, verified_by, verified_at
