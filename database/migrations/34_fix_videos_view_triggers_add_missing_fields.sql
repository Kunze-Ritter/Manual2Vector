-- ============================================================================
-- Migration 34: Fix Videos View Triggers - Add Missing Fields
-- ============================================================================
-- Purpose: Update public.videos view triggers to support manufacturer_id,
--          series_id, and related_error_codes fields
-- ============================================================================

-- Drop existing triggers and functions
DROP TRIGGER IF EXISTS videos_insert_trigger ON public.videos;
DROP TRIGGER IF EXISTS videos_update_trigger ON public.videos;
DROP FUNCTION IF EXISTS public.videos_insert();
DROP FUNCTION IF EXISTS public.videos_update();

-- ============================================================================
-- Trigger for INSERT on videos view (with ALL fields)
-- ============================================================================
CREATE OR REPLACE FUNCTION public.videos_insert()
RETURNS TRIGGER AS $$
DECLARE
    new_id UUID;
BEGIN
    INSERT INTO krai_content.videos (
        link_id, youtube_id, title, description, thumbnail_url,
        duration, view_count, like_count, comment_count,
        channel_id, channel_title, published_at, metadata,
        manufacturer_id, series_id, related_error_codes
    ) VALUES (
        NEW.link_id, NEW.youtube_id, NEW.title, NEW.description, NEW.thumbnail_url,
        NEW.duration, NEW.view_count, NEW.like_count, NEW.comment_count,
        NEW.channel_id, NEW.channel_title, NEW.published_at, NEW.metadata,
        NEW.manufacturer_id, NEW.series_id, NEW.related_error_codes
    ) RETURNING id INTO new_id;
    
    NEW.id := new_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER videos_insert_trigger
INSTEAD OF INSERT ON public.videos
FOR EACH ROW EXECUTE FUNCTION public.videos_insert();

-- ============================================================================
-- Trigger for UPDATE on videos view (with ALL fields)
-- ============================================================================
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
        manufacturer_id = NEW.manufacturer_id,
        series_id = NEW.series_id,
        related_error_codes = NEW.related_error_codes,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER videos_update_trigger
INSTEAD OF UPDATE ON public.videos
FOR EACH ROW EXECUTE FUNCTION public.videos_update();

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 34: Videos view triggers updated successfully!';
    RAISE NOTICE '   - Added manufacturer_id support';
    RAISE NOTICE '   - Added series_id support';
    RAISE NOTICE '   - Added related_error_codes support';
    RAISE NOTICE '   ℹ️  Now all video fields are accessible via public.videos view';
END $$;
