-- ======================================================================
-- Migration 81: Create vw_parts View for Agent
-- ======================================================================
-- Description: Create public view for parts catalog access
-- Date: 2025-10-16
-- Reason: Agent needs to search for parts/accessories
-- ======================================================================

-- Drop existing view if exists
DROP VIEW IF EXISTS public.vw_parts CASCADE;

-- Create parts view
CREATE OR REPLACE VIEW public.vw_parts AS
SELECT 
    pc.id,
    pc.manufacturer_id,
    pc.part_number,
    pc.part_name,
    pc.part_description as description,
    pc.part_category as category,
    pc.unit_price_usd as price_usd,
    pc.created_at,
    m.name as manufacturer_name,
    m.short_name as manufacturer_code
FROM krai_parts.parts_catalog pc
LEFT JOIN krai_core.manufacturers m ON pc.manufacturer_id = m.id;

-- Grant permissions
GRANT SELECT ON public.vw_parts TO anon, authenticated, service_role;

-- Add comment
COMMENT ON VIEW public.vw_parts IS 'Agent Knowledge: Parts catalog with manufacturer information';

-- ======================================================================
-- Verification
-- ======================================================================

-- Test the view
SELECT 
    part_number,
    part_name,
    manufacturer_name,
    category,
    price_usd
FROM public.vw_parts
LIMIT 10;

-- Expected: List of parts with manufacturer info

-- ======================================================================
-- DONE
-- ======================================================================
