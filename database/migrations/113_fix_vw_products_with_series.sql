-- Migration 113: Fix vw_products to include series_name
-- ======================================================================
-- Description: vw_products was broken by migration 86 - missing series_name
-- Date: 2025-10-23
-- Reason: Code expects series_name in vw_products but view only had raw products table
-- ======================================================================

-- Drop the broken view
DROP VIEW IF EXISTS public.vw_products CASCADE;

-- Recreate vw_products with proper JOINs (from migration 72)
CREATE OR REPLACE VIEW public.vw_products AS
SELECT 
    p.*,
    m.name AS manufacturer_name,
    s.series_name
FROM krai_core.products p
LEFT JOIN krai_core.manufacturers m ON p.manufacturer_id = m.id
LEFT JOIN krai_core.product_series s ON p.series_id = s.id;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_products TO anon, authenticated, service_role;

-- Verify
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_schema = 'public' 
--   AND table_name = 'vw_products'
--   AND column_name IN ('series_name', 'manufacturer_name')
-- ORDER BY column_name;
