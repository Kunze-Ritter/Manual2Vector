-- Migration 15a: Create public.products VIEW
-- PART 1 of 2: Products table access via public schema

-- ============================================================================
-- Drop existing view if it exists
-- ============================================================================

DROP VIEW IF EXISTS public.products CASCADE;

-- ============================================================================
-- Create public.products VIEW
-- ============================================================================

CREATE VIEW public.products AS
SELECT * FROM krai_core.products;

-- ============================================================================
-- Grant permissions
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON public.products TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.products TO service_role;

-- ============================================================================
-- Enable INSERT/UPDATE/DELETE on view (Rules)
-- ============================================================================

CREATE OR REPLACE RULE products_insert AS
ON INSERT TO public.products DO INSTEAD
INSERT INTO krai_core.products (
    id, model_number, manufacturer_id, product_type, metadata, 
    created_at, updated_at
) VALUES (
    NEW.id, NEW.model_number, NEW.manufacturer_id, NEW.product_type, NEW.metadata,
    NEW.created_at, NEW.updated_at
) RETURNING *;

CREATE OR REPLACE RULE products_update AS
ON UPDATE TO public.products DO INSTEAD
UPDATE krai_core.products SET 
    model_number = NEW.model_number,
    manufacturer_id = NEW.manufacturer_id,
    product_type = NEW.product_type,
    metadata = NEW.metadata,
    updated_at = NEW.updated_at
WHERE id = OLD.id
RETURNING *;

CREATE OR REPLACE RULE products_delete AS
ON DELETE TO public.products DO INSTEAD
DELETE FROM krai_core.products WHERE id = OLD.id
RETURNING *;

-- ============================================================================
-- Verification
-- ============================================================================

-- Check view exists:
-- SELECT schemaname, viewname 
-- FROM pg_views 
-- WHERE schemaname = 'public' AND viewname = 'products';

-- Test view access:
-- SELECT * FROM public.products LIMIT 1;
