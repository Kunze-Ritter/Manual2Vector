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
    id, document_id, url, link_text, link_type, extraction_method,
    page_number, created_at, updated_at
) VALUES (
    NEW.id, NEW.document_id, NEW.url, NEW.link_text, NEW.link_type, NEW.extraction_method,
    NEW.page_number, NEW.created_at, NEW.updated_at
) RETURNING *;

CREATE OR REPLACE RULE links_update AS
ON UPDATE TO public.links DO INSTEAD
UPDATE krai_content.links SET 
    url = NEW.url,
    link_text = NEW.link_text,
    link_type = NEW.link_type,
    extraction_method = NEW.extraction_method,
    page_number = NEW.page_number,
    updated_at = NEW.updated_at
WHERE id = OLD.id
RETURNING *;

CREATE OR REPLACE RULE links_delete AS
ON DELETE TO public.links DO INSTEAD
DELETE FROM krai_content.links WHERE id = OLD.id
RETURNING *;

-- ============================================================================
-- PART 2: Create public.videos VIEW
-- ============================================================================

DROP VIEW IF EXISTS public.videos CASCADE;

CREATE VIEW public.videos AS
SELECT * FROM krai_content.videos;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.videos TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.videos TO service_role;

-- Enable INSERT/UPDATE/DELETE on view
CREATE OR REPLACE RULE videos_insert AS
ON INSERT TO public.videos DO INSTEAD
INSERT INTO krai_content.videos (
    id, document_id, url, title, platform, video_id, thumbnail_url,
    duration_seconds, extraction_method, page_number, created_at, updated_at
) VALUES (
    NEW.id, NEW.document_id, NEW.url, NEW.title, NEW.platform, NEW.video_id, 
    NEW.thumbnail_url, NEW.duration_seconds, NEW.extraction_method, 
    NEW.page_number, NEW.created_at, NEW.updated_at
) RETURNING *;

CREATE OR REPLACE RULE videos_update AS
ON UPDATE TO public.videos DO INSTEAD
UPDATE krai_content.videos SET 
    url = NEW.url,
    title = NEW.title,
    platform = NEW.platform,
    video_id = NEW.video_id,
    thumbnail_url = NEW.thumbnail_url,
    duration_seconds = NEW.duration_seconds,
    extraction_method = NEW.extraction_method,
    page_number = NEW.page_number,
    updated_at = NEW.updated_at
WHERE id = OLD.id
RETURNING *;

CREATE OR REPLACE RULE videos_delete AS
ON DELETE TO public.videos DO INSTEAD
DELETE FROM krai_content.videos WHERE id = OLD.id
RETURNING *;

-- ============================================================================
-- Verification
-- ============================================================================

-- Check views exist:
-- SELECT schemaname, viewname 
-- FROM pg_views 
-- WHERE schemaname = 'public' 
--   AND viewname IN ('links', 'videos')
-- ORDER BY viewname;

-- Should return 2 rows

-- Test access:
-- SELECT * FROM public.links LIMIT 1;
-- SELECT * FROM public.videos LIMIT 1;
