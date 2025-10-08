-- Migration: Add model_pattern to product_series table
-- Date: 2025-10-08
-- Purpose: Support both marketing name and technical pattern

-- Add model_pattern column to the base table
ALTER TABLE krai_core.product_series 
ADD COLUMN IF NOT EXISTS model_pattern TEXT;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_product_series_model_pattern 
ON krai_core.product_series(model_pattern);

-- Add index for name + model_pattern combination
CREATE INDEX IF NOT EXISTS idx_product_series_name_pattern 
ON krai_core.product_series(series_name, model_pattern);

-- Update existing series to have model_pattern = series_name (for backwards compatibility)
UPDATE krai_core.product_series 
SET model_pattern = series_name 
WHERE model_pattern IS NULL;

-- Recreate the public.product_series view to include model_pattern
DROP VIEW IF EXISTS public.product_series;
CREATE VIEW public.product_series AS
SELECT 
    id,
    manufacturer_id,
    series_name,
    series_code,
    model_pattern,  -- NEW!
    launch_date,
    end_of_life_date,
    target_market,
    price_range,
    key_features,
    series_description,
    marketing_name,
    successor_series_id,
    created_at,
    updated_at
FROM krai_core.product_series;

COMMENT ON COLUMN krai_core.product_series.model_pattern IS 'Technical series pattern (e.g., E500xx, M4xx, C558) for precise matching';
COMMENT ON COLUMN krai_core.product_series.series_name IS 'Marketing/user-friendly series name (e.g., LaserJet, bizhub) for broad search';
