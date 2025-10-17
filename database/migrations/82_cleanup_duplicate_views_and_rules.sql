-- Migration 82: Cleanup duplicate views and rules
-- ======================================================================
-- Description: Remove duplicate views and old RULES from deleted migrations
-- Date: 2025-10-17
-- Reason: Cleanup after deleting migrations 15a, 15b, 16a, 17, 20, 26
-- ======================================================================

-- ======================================================================
-- PART 1: Drop old RULES from migration 16a (replaced by triggers in migration 31)
-- ======================================================================

DROP RULE IF EXISTS links_insert ON public.links;
DROP RULE IF EXISTS links_update ON public.links;
DROP RULE IF EXISTS links_delete ON public.links;

-- ======================================================================
-- PART 2: Drop old RULES from migration 15a, 15b (replaced by migration 15)
-- ======================================================================

-- Products rules (from 15a)
DROP RULE IF EXISTS products_insert ON public.products;
DROP RULE IF EXISTS products_update ON public.products;
DROP RULE IF EXISTS products_delete ON public.products;

-- Document_products rules (from 15b)
DROP RULE IF EXISTS document_products_insert ON public.document_products;
DROP RULE IF EXISTS document_products_update ON public.document_products;
DROP RULE IF EXISTS document_products_delete ON public.document_products;

-- Manufacturers rules (from 15b)
DROP RULE IF EXISTS manufacturers_insert ON public.manufacturers;
DROP RULE IF EXISTS manufacturers_update ON public.manufacturers;
DROP RULE IF EXISTS manufacturers_delete ON public.manufacturers;

-- ======================================================================
-- PART 3: Drop deprecated views (from migrations 17, 20, 26)
-- ======================================================================

-- From migration 17 (DEPRECATED)
DROP VIEW IF EXISTS public.search_analytics CASCADE;

-- Note: Migration 20 chunks view was already replaced by 20c
-- Note: Migration 26 vw_embeddings was already replaced by 35
-- These should already be gone, but we drop them just in case

-- ======================================================================
-- Note: All current views are maintained by their respective migrations:
-- - Migration 15: products, document_products, manufacturers (with RULES)
-- - Migration 31: links, videos (with TRIGGERS)
-- - Migration 35: vw_embeddings (current version)
-- ======================================================================

-- ======================================================================
-- Verification
-- ======================================================================

-- Check that triggers exist (from migration 31):
-- SELECT trigger_name, event_manipulation, event_object_table
-- FROM information_schema.triggers
-- WHERE event_object_schema = 'public'
--   AND event_object_table IN ('links', 'videos');

-- Should show:
-- links_insert_trigger | INSERT | links
-- links_update_trigger | UPDATE | links
-- links_delete_trigger | DELETE | links
-- videos_insert_trigger | INSERT | videos
-- videos_update_trigger | UPDATE | videos
-- videos_delete_trigger | DELETE | videos

-- Check that old RULES are gone:
-- SELECT rulename, ev_class::regclass
-- FROM pg_rewrite
-- WHERE ev_class::regclass::text IN ('public.links', 'public.videos')
--   AND rulename != '_RETURN';

-- Should return 0 rows (only _RETURN rule exists for views)
