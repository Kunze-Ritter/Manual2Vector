-- ======================================================================
-- Migration 23: Fix PostgREST Cache via DROP + RECREATE
-- ======================================================================
-- Description: Reset PostgREST cache by dropping and recreating columns
-- Date: 2025-10-05
-- Reason: Supabase PostgREST cache is broken - DROP + RECREATE fixes it!
-- ======================================================================

-- STEP 1: DROP all problematic columns (this clears PostgREST cache)
ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS context_text;

ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS metadata;

-- Remove unused columns while we're at it
ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS ai_extracted;

ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS verified;

ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS verified_by;

ALTER TABLE krai_intelligence.error_codes
DROP COLUMN IF EXISTS verified_at;

-- STEP 2: RECREATE the columns we need (fresh schema, cache will update!)

-- Add image_id if it doesn't exist (from Migration 09 - might not have been run)
ALTER TABLE krai_intelligence.error_codes
ADD COLUMN IF NOT EXISTS image_id UUID REFERENCES krai_content.images(id) ON DELETE SET NULL;

ALTER TABLE krai_intelligence.error_codes
ADD COLUMN context_text TEXT;

ALTER TABLE krai_intelligence.error_codes
ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;

-- Add helpful comments
COMMENT ON COLUMN krai_intelligence.error_codes.image_id IS 
'Reference to screenshot/image where error code was found (for Smart Vision AI matching)';

COMMENT ON COLUMN krai_intelligence.error_codes.context_text IS 
'Surrounding text where error code was found (for context)';

COMMENT ON COLUMN krai_intelligence.error_codes.metadata IS 
'Flexible JSONB storage for extraction metadata (smart matching info, etc.)';

-- ======================================================================
-- Verification
-- ======================================================================

-- Show remaining columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'krai_intelligence'
  AND table_name = 'error_codes'
ORDER BY ordinal_position;

-- Expected output: 
-- Should SHOW: context_text, metadata (freshly created!)
-- Should NOT show: ai_extracted, verified, verified_by, verified_at
-- Should SHOW: image_id, chunk_id (from Migration 09 - these still work!)
