-- Migration 018: Add error code hierarchy support
-- Adds parent_code and is_category columns for hierarchical error code grouping
-- Example: HP 13.B9.Az (specific) → parent_code = "13.B9" (category)

ALTER TABLE krai_intelligence.error_codes
  ADD COLUMN IF NOT EXISTS parent_code VARCHAR(50),
  ADD COLUMN IF NOT EXISTS is_category BOOLEAN DEFAULT false;

-- Index for querying children of a category
CREATE INDEX IF NOT EXISTS idx_error_codes_parent
  ON krai_intelligence.error_codes(parent_code)
  WHERE parent_code IS NOT NULL;

-- Partial index for fast category lookups
CREATE INDEX IF NOT EXISTS idx_error_codes_category
  ON krai_intelligence.error_codes(is_category)
  WHERE is_category = true;
