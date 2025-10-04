-- Migration 15: Create public views for products and document_products
-- Allows Supabase PostgREST to access krai_core tables via public schema

-- ============================================================================
-- PART 1: Create public.products VIEW
-- ============================================================================

CREATE OR REPLACE VIEW public.products AS
SELECT * FROM krai_core.products;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.products TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.products TO service_role;

-- Enable INSERT/UPDATE/DELETE on view
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
-- PART 2: Create public.document_products VIEW
-- ============================================================================

CREATE OR REPLACE VIEW public.document_products AS
SELECT * FROM krai_core.document_products;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.document_products TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.document_products TO service_role;

-- Enable INSERT/UPDATE/DELETE on view
CREATE OR REPLACE RULE document_products_insert AS
ON INSERT TO public.document_products DO INSTEAD
INSERT INTO krai_core.document_products (
    id, document_id, product_id, is_primary_product, confidence_score,
    extraction_method, page_numbers, created_at, updated_at
) VALUES (
    NEW.id, NEW.document_id, NEW.product_id, NEW.is_primary_product, NEW.confidence_score,
    NEW.extraction_method, NEW.page_numbers, NEW.created_at, NEW.updated_at
) RETURNING *;

CREATE OR REPLACE RULE document_products_update AS
ON UPDATE TO public.document_products DO INSTEAD
UPDATE krai_core.document_products SET 
    is_primary_product = NEW.is_primary_product,
    confidence_score = NEW.confidence_score,
    extraction_method = NEW.extraction_method,
    page_numbers = NEW.page_numbers,
    updated_at = NEW.updated_at
WHERE id = OLD.id
RETURNING *;

CREATE OR REPLACE RULE document_products_delete AS
ON DELETE TO public.document_products DO INSTEAD
DELETE FROM krai_core.document_products WHERE id = OLD.id
RETURNING *;

-- ============================================================================
-- PART 3: Create public.manufacturers VIEW
-- ============================================================================

CREATE OR REPLACE VIEW public.manufacturers AS
SELECT * FROM krai_core.manufacturers;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.manufacturers TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.manufacturers TO service_role;

-- Enable INSERT/UPDATE/DELETE on view
CREATE OR REPLACE RULE manufacturers_insert AS
ON INSERT TO public.manufacturers DO INSTEAD
INSERT INTO krai_core.manufacturers (
    id, name, website, support_email, support_phone, metadata,
    created_at, updated_at
) VALUES (
    NEW.id, NEW.name, NEW.website, NEW.support_email, NEW.support_phone, NEW.metadata,
    NEW.created_at, NEW.updated_at
) RETURNING *;

CREATE OR REPLACE RULE manufacturers_update AS
ON UPDATE TO public.manufacturers DO INSTEAD
UPDATE krai_core.manufacturers SET 
    name = NEW.name,
    website = NEW.website,
    support_email = NEW.support_email,
    support_phone = NEW.support_phone,
    metadata = NEW.metadata,
    updated_at = NEW.updated_at
WHERE id = OLD.id
RETURNING *;

CREATE OR REPLACE RULE manufacturers_delete AS
ON DELETE TO public.manufacturers DO INSTEAD
DELETE FROM krai_core.manufacturers WHERE id = OLD.id
RETURNING *;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check views exist:
-- SELECT schemaname, viewname 
-- FROM pg_views 
-- WHERE schemaname = 'public' 
--   AND viewname IN ('products', 'document_products', 'manufacturers');

-- Test insert via view:
-- SELECT * FROM public.products LIMIT 1;
