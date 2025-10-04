-- Migration 15b: Create public views for document_products and manufacturers
-- PART 2 of 2: Additional table access via public schema
-- NOTE: Run this AFTER 15a_create_products_view.sql

-- ============================================================================
-- PART 1: Create public.document_products VIEW
-- ============================================================================

DROP VIEW IF EXISTS public.document_products CASCADE;

CREATE VIEW public.document_products AS
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
    COALESCE(NEW.id, uuid_generate_v4()), 
    NEW.document_id, NEW.product_id, NEW.is_primary_product, NEW.confidence_score,
    NEW.extraction_method, NEW.page_numbers, 
    COALESCE(NEW.created_at, NOW()), COALESCE(NEW.updated_at, NOW())
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
-- PART 2: Create public.manufacturers VIEW
-- ============================================================================

DROP VIEW IF EXISTS public.manufacturers CASCADE;

CREATE VIEW public.manufacturers AS
SELECT * FROM krai_core.manufacturers;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.manufacturers TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.manufacturers TO service_role;

-- Enable INSERT/UPDATE/DELETE on view
CREATE OR REPLACE RULE manufacturers_insert AS
ON INSERT TO public.manufacturers DO INSTEAD
INSERT INTO krai_core.manufacturers (
    id, name, short_name, country, founded_year, website, support_email, 
    support_phone, logo_url, is_competitor, market_share_percent, 
    annual_revenue_usd, employee_count, headquarters_address, stock_symbol, 
    primary_business_segment, created_at, updated_at
) VALUES (
    COALESCE(NEW.id, uuid_generate_v4()),
    NEW.name, NEW.short_name, NEW.country, NEW.founded_year, NEW.website, 
    NEW.support_email, NEW.support_phone, NEW.logo_url, NEW.is_competitor, 
    NEW.market_share_percent, NEW.annual_revenue_usd, NEW.employee_count, 
    NEW.headquarters_address, NEW.stock_symbol, NEW.primary_business_segment,
    COALESCE(NEW.created_at, NOW()), COALESCE(NEW.updated_at, NOW())
) RETURNING *;

CREATE OR REPLACE RULE manufacturers_update AS
ON UPDATE TO public.manufacturers DO INSTEAD
UPDATE krai_core.manufacturers SET 
    name = NEW.name,
    short_name = NEW.short_name,
    country = NEW.country,
    founded_year = NEW.founded_year,
    website = NEW.website,
    support_email = NEW.support_email,
    support_phone = NEW.support_phone,
    logo_url = NEW.logo_url,
    is_competitor = NEW.is_competitor,
    market_share_percent = NEW.market_share_percent,
    annual_revenue_usd = NEW.annual_revenue_usd,
    employee_count = NEW.employee_count,
    headquarters_address = NEW.headquarters_address,
    stock_symbol = NEW.stock_symbol,
    primary_business_segment = NEW.primary_business_segment,
    updated_at = NEW.updated_at
WHERE id = OLD.id
RETURNING *;

CREATE OR REPLACE RULE manufacturers_delete AS
ON DELETE TO public.manufacturers DO INSTEAD
DELETE FROM krai_core.manufacturers WHERE id = OLD.id
RETURNING *;

-- ============================================================================
-- Verification
-- ============================================================================

-- Check all views exist:
-- SELECT schemaname, viewname 
-- FROM pg_views 
-- WHERE schemaname = 'public' 
--   AND viewname IN ('products', 'document_products', 'manufacturers')
-- ORDER BY viewname;

-- Should return 3 rows
