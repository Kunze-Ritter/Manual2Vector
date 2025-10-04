-- Migration 18: Create public view for parts_catalog
-- Allows Supabase PostgREST to access krai_parts.parts_catalog via public schema

-- ============================================================================
-- PART 1: Create public.parts_catalog VIEW
-- ============================================================================

DROP VIEW IF EXISTS public.parts_catalog CASCADE;

CREATE VIEW public.parts_catalog AS
SELECT * FROM krai_parts.parts_catalog;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.parts_catalog TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.parts_catalog TO service_role;

-- Enable INSERT/UPDATE/DELETE on view
CREATE OR REPLACE RULE parts_catalog_insert AS
ON INSERT TO public.parts_catalog DO INSTEAD
INSERT INTO krai_parts.parts_catalog (
    id, manufacturer_id, part_number, part_name, part_description,
    part_category, unit_price_usd, created_at
) VALUES (
    COALESCE(NEW.id, uuid_generate_v4()),
    NEW.manufacturer_id,
    NEW.part_number,
    NEW.part_name,
    NEW.part_description,
    NEW.part_category,
    NEW.unit_price_usd,
    COALESCE(NEW.created_at, NOW())
) RETURNING *;

CREATE OR REPLACE RULE parts_catalog_update AS
ON UPDATE TO public.parts_catalog DO INSTEAD
UPDATE krai_parts.parts_catalog SET 
    part_number = NEW.part_number,
    part_name = NEW.part_name,
    part_description = NEW.part_description,
    part_category = NEW.part_category,
    unit_price_usd = NEW.unit_price_usd
WHERE id = OLD.id
RETURNING *;

CREATE OR REPLACE RULE parts_catalog_delete AS
ON DELETE TO public.parts_catalog DO INSTEAD
DELETE FROM krai_parts.parts_catalog WHERE id = OLD.id
RETURNING *;

-- ============================================================================
-- Verification
-- ============================================================================

-- Check view exists:
-- SELECT schemaname, viewname 
-- FROM pg_views 
-- WHERE schemaname = 'public' 
--   AND viewname = 'parts_catalog';

-- Should return 1 row

-- Test access:
-- SELECT * FROM public.parts_catalog LIMIT 1;
