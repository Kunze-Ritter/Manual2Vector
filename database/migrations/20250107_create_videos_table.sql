-- Migration: Create videos table for enriched video metadata
-- Date: 2025-01-07
-- Purpose: Store enriched metadata for video links (YouTube, Vimeo, Brightcove)

-- Drop existing videos table if it exists (clean slate)
DROP TABLE IF EXISTS krai_content.videos CASCADE;

-- Create videos table
CREATE TABLE krai_content.videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    link_id UUID REFERENCES krai_content.links(id) ON DELETE CASCADE,
    
    -- Platform & IDs
    youtube_id VARCHAR(20),  -- YouTube video ID (11 chars but allow extra)
    platform VARCHAR(20),    -- youtube, vimeo, brightcove
    
    -- Basic Info
    title VARCHAR(500) NOT NULL,
    description TEXT,
    
    -- Media Info
    thumbnail_url TEXT,
    duration INTEGER,  -- Duration in seconds
    
    -- YouTube specific
    view_count BIGINT,
    like_count INTEGER,
    comment_count INTEGER,
    channel_id VARCHAR(50),
    channel_title VARCHAR(200),
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Relationships
    manufacturer_id UUID REFERENCES krai_core.manufacturers(id),
    series_id UUID REFERENCES krai_core.product_series(id),
    document_id UUID REFERENCES krai_core.documents(id),
    
    -- Metadata
    metadata JSONB,  -- Platform-specific extra data (vimeo_id, brightcove_id, etc.)
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    enriched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_videos_link_id ON krai_content.videos(link_id);
CREATE INDEX idx_videos_youtube_id ON krai_content.videos(youtube_id);
CREATE INDEX idx_videos_platform ON krai_content.videos(platform);
CREATE INDEX idx_videos_manufacturer_id ON krai_content.videos(manufacturer_id);
CREATE INDEX idx_videos_document_id ON krai_content.videos(document_id);

-- Comments
COMMENT ON TABLE krai_content.videos IS 'Enriched video metadata for links (YouTube, Vimeo, Brightcove)';
COMMENT ON COLUMN krai_content.videos.link_id IS 'Reference to link in links table (can be NULL for direct API enrichment)';
COMMENT ON COLUMN krai_content.videos.youtube_id IS 'YouTube video ID for deduplication';
COMMENT ON COLUMN krai_content.videos.duration IS 'Video duration in seconds';
COMMENT ON COLUMN krai_content.videos.metadata IS 'Platform-specific extra data (vimeo_id, brightcove_id, etc.)';

-- Add video_id column to links table if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'krai_content' 
        AND table_name = 'links' 
        AND column_name = 'video_id'
    ) THEN
        ALTER TABLE krai_content.links 
        ADD COLUMN video_id UUID REFERENCES krai_content.videos(id);
        
        CREATE INDEX idx_links_video_id ON krai_content.links(video_id);
        
        COMMENT ON COLUMN krai_content.links.video_id IS 'Reference to enriched video metadata';
    END IF;
END $$;

-- Drop instructional_videos table (replaced by videos table)
DROP TABLE IF EXISTS krai_content.instructional_videos CASCADE;

COMMENT ON TABLE krai_content.videos IS 'Replaced instructional_videos with unified videos table for better link integration';
