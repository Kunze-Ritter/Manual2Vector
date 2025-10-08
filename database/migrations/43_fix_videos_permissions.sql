-- Migration: Fix videos table permissions
-- Date: 2025-10-07
-- Purpose: Grant permissions on videos table and related objects

-- Grant permissions on videos table
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_content.videos TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_content.videos TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_content.videos TO service_role;

-- Grant permissions on videos view
GRANT SELECT, INSERT, UPDATE, DELETE ON public.videos TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.videos TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.videos TO service_role;

-- Grant permissions on video_products junction table
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_content.video_products TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_content.video_products TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_content.video_products TO service_role;

-- Grant usage on schema
GRANT USAGE ON SCHEMA krai_content TO authenticated;
GRANT USAGE ON SCHEMA krai_content TO anon;
GRANT USAGE ON SCHEMA krai_content TO service_role;

-- Grant execute on search function
GRANT EXECUTE ON FUNCTION search_error_code_multi_source TO authenticated;
GRANT EXECUTE ON FUNCTION search_error_code_multi_source TO anon;
GRANT EXECUTE ON FUNCTION search_error_code_multi_source TO service_role;

-- Grant permissions on error_codes table (if not already granted)
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_intelligence.error_codes TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_intelligence.error_codes TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON krai_intelligence.error_codes TO service_role;

-- Grant usage on intelligence schema
GRANT USAGE ON SCHEMA krai_intelligence TO authenticated;
GRANT USAGE ON SCHEMA krai_intelligence TO anon;
GRANT USAGE ON SCHEMA krai_intelligence TO service_role;
