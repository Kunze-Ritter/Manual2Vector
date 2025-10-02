-- ===========================================
-- LINK & VIDEO ENHANCEMENT
-- ===========================================
-- Adds video_id to links table for intelligent linking
-- Adds metadata fields for AI-powered categorization

-- Add video_id foreign key to links table
ALTER TABLE krai_content.links
ADD COLUMN video_id UUID REFERENCES krai_content.instructional_videos(id) ON DELETE SET NULL;

-- Add metadata field for AI-categorization results
ALTER TABLE krai_content.links
ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;

-- Add link_category for better categorization
ALTER TABLE krai_content.links
ADD COLUMN link_category VARCHAR(50);

-- Add confidence_score for AI extraction quality
ALTER TABLE krai_content.links
ADD COLUMN confidence_score DECIMAL(3,2) DEFAULT 0.0;

-- Update link_type to support more types
ALTER TABLE krai_content.links
ALTER COLUMN link_type DROP DEFAULT;

ALTER TABLE krai_content.links
ADD CONSTRAINT link_type_check 
CHECK (link_type IN ('video', 'external', 'tutorial', 'support', 'download', 'email', 'phone'));

ALTER TABLE krai_content.links
ALTER COLUMN link_type SET DEFAULT 'external';

-- Index for video_id lookups
CREATE INDEX idx_links_video_id ON krai_content.links(video_id) WHERE video_id IS NOT NULL;

-- Index for link_type categorization
CREATE INDEX idx_links_type_category ON krai_content.links(link_type, link_category);

-- Index for URL matching (for deduplication)
CREATE INDEX idx_links_url_hash ON krai_content.links(MD5(url));

-- Comments
COMMENT ON COLUMN krai_content.links.video_id IS 'Reference to instructional_videos if link is a video';
COMMENT ON COLUMN krai_content.links.metadata IS 'AI categorization metadata (platform, video_id, title, etc.)';
COMMENT ON COLUMN krai_content.links.link_category IS 'Detailed category (youtube, vimeo, support_hp, download_driver, etc.)';
COMMENT ON COLUMN krai_content.links.confidence_score IS 'AI extraction confidence (0.0-1.0)';

-- Add metadata to instructional_videos for better tracking
ALTER TABLE krai_content.instructional_videos
ADD COLUMN IF NOT EXISTS source_document_id UUID REFERENCES krai_core.documents(id) ON DELETE SET NULL;

ALTER TABLE krai_content.instructional_videos
ADD COLUMN IF NOT EXISTS auto_created BOOLEAN DEFAULT false;

ALTER TABLE krai_content.instructional_videos
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

COMMENT ON COLUMN krai_content.instructional_videos.source_document_id IS 'Document where this video was first discovered';
COMMENT ON COLUMN krai_content.instructional_videos.auto_created IS 'True if created automatically from link extraction';
COMMENT ON COLUMN krai_content.instructional_videos.metadata IS 'YouTube/Vimeo metadata (channel, views, likes, etc.)';

-- Helper function to find or create instructional video from link
CREATE OR REPLACE FUNCTION krai_content.find_or_create_video_from_link(
    p_url TEXT,
    p_manufacturer_id UUID,
    p_title TEXT DEFAULT NULL,
    p_description TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID AS $$
DECLARE
    v_video_id UUID;
BEGIN
    -- Try to find existing video by URL
    SELECT id INTO v_video_id
    FROM krai_content.instructional_videos
    WHERE video_url = p_url
    LIMIT 1;
    
    -- If not found, create new video
    IF v_video_id IS NULL THEN
        INSERT INTO krai_content.instructional_videos (
            manufacturer_id,
            title,
            description,
            video_url,
            auto_created,
            metadata
        ) VALUES (
            p_manufacturer_id,
            COALESCE(p_title, 'Auto-extracted: ' || p_url),
            COALESCE(p_description, 'Automatically extracted from document'),
            p_url,
            true,
            p_metadata
        )
        RETURNING id INTO v_video_id;
    END IF;
    
    RETURN v_video_id;
END;
$$ LANGUAGE plpgsql;

-- Helper function to get link statistics
CREATE OR REPLACE FUNCTION krai_content.get_link_statistics()
RETURNS TABLE (
    total_links BIGINT,
    video_links BIGINT,
    support_links BIGINT,
    download_links BIGINT,
    linked_to_videos BIGINT,
    avg_confidence DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_links,
        COUNT(*) FILTER (WHERE link_type = 'video')::BIGINT as video_links,
        COUNT(*) FILTER (WHERE link_type = 'support')::BIGINT as support_links,
        COUNT(*) FILTER (WHERE link_type = 'download')::BIGINT as download_links,
        COUNT(*) FILTER (WHERE video_id IS NOT NULL)::BIGINT as linked_to_videos,
        AVG(confidence_score) as avg_confidence
    FROM krai_content.links;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT EXECUTE ON FUNCTION krai_content.find_or_create_video_from_link TO service_role, authenticated;
GRANT EXECUTE ON FUNCTION krai_content.get_link_statistics TO service_role, authenticated;
