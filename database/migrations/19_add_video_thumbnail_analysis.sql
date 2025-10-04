-- ======================================================================
-- Migration 19: Add Video Thumbnail Analysis Fields
-- ======================================================================
-- Description: Adds OCR and Vision AI analysis fields for video thumbnails
-- Date: 2025-10-05
-- Purpose: Enable thumbnail analysis for better video content understanding
-- ======================================================================

-- Add thumbnail analysis columns to instructional_videos
ALTER TABLE krai_content.instructional_videos
ADD COLUMN IF NOT EXISTS thumbnail_ocr_text TEXT,
ADD COLUMN IF NOT EXISTS thumbnail_ai_description TEXT,
ADD COLUMN IF NOT EXISTS thumbnail_analysis_date TIMESTAMP WITH TIME ZONE;

-- Add comments
COMMENT ON COLUMN krai_content.instructional_videos.thumbnail_ocr_text IS 
'Text extracted from video thumbnail using OCR (Tesseract)';

COMMENT ON COLUMN krai_content.instructional_videos.thumbnail_ai_description IS 
'AI-generated description of video thumbnail content (LLaVA)';

COMMENT ON COLUMN krai_content.instructional_videos.thumbnail_analysis_date IS 
'Timestamp when thumbnail was last analyzed';

-- ======================================================================
-- Verification
-- ======================================================================

-- Check columns were added:
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_schema = 'krai_content'
--   AND table_name = 'instructional_videos'
--   AND column_name IN ('thumbnail_ocr_text', 'thumbnail_ai_description', 'thumbnail_analysis_date');
