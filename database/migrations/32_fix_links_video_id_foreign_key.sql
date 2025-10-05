-- ============================================================================
-- Migration 32: Fix links.video_id Foreign Key
-- ============================================================================
-- Purpose: Update foreign key constraint to point to krai_content.videos
--          instead of the old instructional_videos table
-- ============================================================================

-- Drop old foreign key constraint (if exists)
ALTER TABLE krai_content.links 
DROP CONSTRAINT IF EXISTS links_video_id_fkey;

-- Drop old constraint with different name (if exists)
ALTER TABLE krai_content.links 
DROP CONSTRAINT IF EXISTS fk_links_video_id;

-- Add new foreign key constraint pointing to krai_content.videos
ALTER TABLE krai_content.links
ADD CONSTRAINT links_video_id_fkey 
FOREIGN KEY (video_id) 
REFERENCES krai_content.videos(id) 
ON DELETE SET NULL;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 32: Foreign key constraint updated successfully!';
    RAISE NOTICE '   - links.video_id now references krai_content.videos(id)';
    RAISE NOTICE '   - ON DELETE SET NULL (video deleted → link.video_id set to null)';
END $$;
