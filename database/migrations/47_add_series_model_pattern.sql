-- Migration: Add model_pattern to series table
-- Date: 2025-10-08
-- Purpose: Support both marketing name and technical pattern

-- Add model_pattern column
ALTER TABLE krai_core.series 
ADD COLUMN IF NOT EXISTS model_pattern TEXT;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_series_model_pattern 
ON krai_core.series(model_pattern);

-- Add index for name + model_pattern combination
CREATE INDEX IF NOT EXISTS idx_series_name_pattern 
ON krai_core.series(name, model_pattern);

-- Update existing series to have model_pattern = name (for backwards compatibility)
UPDATE krai_core.series 
SET model_pattern = name 
WHERE model_pattern IS NULL;

COMMENT ON COLUMN krai_core.series.model_pattern IS 'Technical series pattern (e.g., E500xx, M4xx, C558) for precise matching';
COMMENT ON COLUMN krai_core.series.name IS 'Marketing/user-friendly series name (e.g., LaserJet, bizhub) for broad search';
