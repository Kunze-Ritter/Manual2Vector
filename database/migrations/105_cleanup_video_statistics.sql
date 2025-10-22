-- Cleanup video statistics columns
-- Remove view_count, like_count, comment_count (not needed for service manuals)

-- Step 1: Drop view that depends on these columns
DROP VIEW IF EXISTS public.vw_videos CASCADE;

-- Step 2: Remove statistics columns
ALTER TABLE krai_content.videos 
DROP COLUMN IF EXISTS view_count,
DROP COLUMN IF EXISTS like_count,
DROP COLUMN IF EXISTS comment_count;

-- Step 3: Recreate view without the removed columns
CREATE OR REPLACE VIEW public.vw_videos AS
SELECT 
    id,
    link_id,
    youtube_id,
    platform,
    video_url,
    title,
    description,
    thumbnail_url,
    duration,
    channel_id,
    channel_title,
    published_at,
    manufacturer_id,
    series_id,
    document_id,
    metadata,
    created_at,
    updated_at,
    enriched_at
FROM krai_content.videos;

-- Grant permissions
GRANT SELECT ON public.vw_videos TO anon, authenticated;

-- Add comments
COMMENT ON VIEW public.vw_videos IS 
'Videos view - cleaned up (view_count, like_count, comment_count removed)';

COMMENT ON TABLE krai_content.videos IS 
'Videos table - statistics removed (focus on technical content)';

-- Success message
SELECT '✅ Cleaned up video statistics columns and recreated vw_videos!' as status;
