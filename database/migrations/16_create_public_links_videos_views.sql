-- Migration 16: Create public views for links and videos
-- Allows Supabase PostgREST to access krai_content tables via public schema

-- ============================================================================
-- PART 1: Create public.links VIEW
-- ============================================================================

DROP VIEW IF EXISTS public.links CASCADE;

CREATE VIEW public.links AS
SELECT * FROM krai_content.links;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.links TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.links TO service_role;

-- Enable INSERT/UPDATE/DELETE on view
CREATE OR REPLACE RULE links_insert AS
ON INSERT TO public.links DO INSTEAD
INSERT INTO krai_content.links (
    id, document_id, url, link_type, page_number, description,
    position_data, is_active, created_at, updated_at
) VALUES (
    NEW.id, NEW.document_id, NEW.url, NEW.link_type, NEW.page_number, NEW.description,
    NEW.position_data, NEW.is_active, NEW.created_at, NEW.updated_at
) RETURNING *;

CREATE OR REPLACE RULE links_update AS
ON UPDATE TO public.links DO INSTEAD
UPDATE krai_content.links SET 
    url = NEW.url,
    link_type = NEW.link_type,
    page_number = NEW.page_number,
    description = NEW.description,
    position_data = NEW.position_data,
    is_active = NEW.is_active,
    updated_at = NEW.updated_at
WHERE id = OLD.id
RETURNING *;

CREATE OR REPLACE RULE links_delete AS
ON DELETE TO public.links DO INSTEAD
DELETE FROM krai_content.links WHERE id = OLD.id
RETURNING *;

-- ============================================================================
-- NOTE: videos table does not exist in krai_content schema!
-- Only krai_content.instructional_videos exists.
-- If you need a videos table for extracted video links from documents,
-- you need to create it first before running this migration.
-- ============================================================================

-- ============================================================================
-- Verification
-- ============================================================================

-- Check view exists:
-- SELECT schemaname, viewname 
-- FROM pg_views 
-- WHERE schemaname = 'public' 
--   AND viewname = 'links';

-- Should return 1 row

-- Test access:
-- SELECT * FROM public.links LIMIT 1;
