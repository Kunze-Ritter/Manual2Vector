-- ============================================================================
-- Migration 33: Add Indexes for Video Deduplication
-- ============================================================================
-- Purpose: Add indexes on youtube_id and metadata JSON fields for efficient
--          deduplication lookups in video enrichment script
-- ============================================================================

-- Index on youtube_id (most common, direct column)
CREATE INDEX IF NOT EXISTS idx_videos_youtube_id 
ON krai_content.videos(youtube_id) 
WHERE youtube_id IS NOT NULL;

-- Index on Vimeo ID (stored in metadata JSON)
CREATE INDEX IF NOT EXISTS idx_videos_vimeo_id 
ON krai_content.videos((metadata->>'vimeo_id')) 
WHERE metadata->>'vimeo_id' IS NOT NULL;

-- Index on Brightcove ID (stored in metadata JSON)
CREATE INDEX IF NOT EXISTS idx_videos_brightcove_id 
ON krai_content.videos((metadata->>'brightcove_id')) 
WHERE metadata->>'brightcove_id' IS NOT NULL;

-- Index on link_id (fallback lookup)
CREATE INDEX IF NOT EXISTS idx_videos_link_id 
ON krai_content.videos(link_id);

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 33: Video deduplication indexes created successfully!';
    RAISE NOTICE '   - idx_videos_youtube_id (direct column)';
    RAISE NOTICE '   - idx_videos_vimeo_id (JSON field)';
    RAISE NOTICE '   - idx_videos_brightcove_id (JSON field)';
    RAISE NOTICE '   - idx_videos_link_id (fallback)';
    RAISE NOTICE '   ℹ️  These indexes enable efficient video deduplication';
END $$;
