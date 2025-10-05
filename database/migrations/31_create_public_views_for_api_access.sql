-- ============================================================================
-- Migration 31: Create Public Views for API Access
-- ============================================================================
-- Purpose: Create views in public schema to expose krai_content tables
--          Supabase PostgREST only exposes tables in public schema by default
-- ============================================================================

-- ============================================================================
-- Clean up existing objects (for re-running migration)
-- ============================================================================
DROP TRIGGER IF EXISTS videos_insert_trigger ON public.videos;
DROP TRIGGER IF EXISTS videos_update_trigger ON public.videos;
DROP TRIGGER IF EXISTS videos_delete_trigger ON public.videos;
DROP TRIGGER IF EXISTS links_insert_trigger ON public.links;
DROP TRIGGER IF EXISTS links_update_trigger ON public.links;
DROP TRIGGER IF EXISTS links_delete_trigger ON public.links;

DROP FUNCTION IF EXISTS public.videos_insert();
DROP FUNCTION IF EXISTS public.videos_update();
DROP FUNCTION IF EXISTS public.videos_delete();
DROP FUNCTION IF EXISTS public.links_insert();
DROP FUNCTION IF EXISTS public.links_update();
DROP FUNCTION IF EXISTS public.links_delete();

DROP VIEW IF EXISTS public.videos;
DROP VIEW IF EXISTS public.links;

-- ============================================================================
-- Create Views
-- ============================================================================

-- Create view for videos (expose krai_content.videos as public.videos)
CREATE OR REPLACE VIEW public.videos AS
SELECT * FROM krai_content.videos;

-- Create view for links (expose krai_content.links as public.links)
CREATE OR REPLACE VIEW public.links AS
SELECT * FROM krai_content.links;

-- ============================================================================
-- INSTEAD OF Triggers to make views writable
-- ============================================================================

-- Trigger for INSERT on videos view
CREATE OR REPLACE FUNCTION public.videos_insert()
RETURNS TRIGGER AS $$
DECLARE
    new_id UUID;
BEGIN
    INSERT INTO krai_content.videos (
        link_id, youtube_id, title, description, thumbnail_url,
        duration, view_count, like_count, comment_count,
        channel_id, channel_title, published_at, metadata
    ) VALUES (
        NEW.link_id, NEW.youtube_id, NEW.title, NEW.description, NEW.thumbnail_url,
        NEW.duration, NEW.view_count, NEW.like_count, NEW.comment_count,
        NEW.channel_id, NEW.channel_title, NEW.published_at, NEW.metadata
    ) RETURNING id INTO new_id;
    
    NEW.id := new_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER videos_insert_trigger
INSTEAD OF INSERT ON public.videos
FOR EACH ROW EXECUTE FUNCTION public.videos_insert();

-- Trigger for UPDATE on videos view
CREATE OR REPLACE FUNCTION public.videos_update()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE krai_content.videos
    SET 
        link_id = NEW.link_id,
        youtube_id = NEW.youtube_id,
        title = NEW.title,
        description = NEW.description,
        thumbnail_url = NEW.thumbnail_url,
        duration = NEW.duration,
        view_count = NEW.view_count,
        like_count = NEW.like_count,
        comment_count = NEW.comment_count,
        channel_id = NEW.channel_id,
        channel_title = NEW.channel_title,
        published_at = NEW.published_at,
        metadata = NEW.metadata,
        updated_at = NEW.updated_at
    WHERE id = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER videos_update_trigger
INSTEAD OF UPDATE ON public.videos
FOR EACH ROW EXECUTE FUNCTION public.videos_update();

-- Trigger for DELETE on videos view
CREATE OR REPLACE FUNCTION public.videos_delete()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM krai_content.videos WHERE id = OLD.id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER videos_delete_trigger
INSTEAD OF DELETE ON public.videos
FOR EACH ROW EXECUTE FUNCTION public.videos_delete();

-- Trigger for INSERT on links view
CREATE OR REPLACE FUNCTION public.links_insert()
RETURNS TRIGGER AS $$
DECLARE
    new_id UUID;
BEGIN
    INSERT INTO krai_content.links (
        document_id, url, link_type, description, page_number,
        is_active, video_id, manufacturer_id, series_id,
        related_error_codes, metadata
    ) VALUES (
        NEW.document_id, NEW.url, NEW.link_type, NEW.description, NEW.page_number,
        NEW.is_active, NEW.video_id, NEW.manufacturer_id, NEW.series_id,
        NEW.related_error_codes, NEW.metadata
    ) RETURNING id INTO new_id;
    
    NEW.id := new_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER links_insert_trigger
INSTEAD OF INSERT ON public.links
FOR EACH ROW EXECUTE FUNCTION public.links_insert();

-- Trigger for UPDATE on links view
CREATE OR REPLACE FUNCTION public.links_update()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE krai_content.links
    SET 
        document_id = NEW.document_id,
        url = NEW.url,
        link_type = NEW.link_type,
        description = NEW.description,
        page_number = NEW.page_number,
        is_active = NEW.is_active,
        video_id = NEW.video_id,
        manufacturer_id = NEW.manufacturer_id,
        series_id = NEW.series_id,
        related_error_codes = NEW.related_error_codes,
        metadata = NEW.metadata,
        created_at = NEW.created_at,
        updated_at = NEW.updated_at
    WHERE id = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER links_update_trigger
INSTEAD OF UPDATE ON public.links
FOR EACH ROW EXECUTE FUNCTION public.links_update();

-- Trigger for DELETE on links view
CREATE OR REPLACE FUNCTION public.links_delete()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM krai_content.links WHERE id = OLD.id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER links_delete_trigger
INSTEAD OF DELETE ON public.links
FOR EACH ROW EXECUTE FUNCTION public.links_delete();

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.videos TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.links TO service_role;

GRANT SELECT ON public.videos TO anon;
GRANT SELECT ON public.links TO anon;

-- Enable RLS on views (inherit from base tables)
-- Note: Views inherit RLS policies from their base tables automatically

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 31: Public views created successfully!';
    RAISE NOTICE '   - public.videos → krai_content.videos';
    RAISE NOTICE '   - public.links → krai_content.links';
    RAISE NOTICE '   ℹ️  These views make tables accessible via Supabase PostgREST API';
END $$;
