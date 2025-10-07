-- Migration: Create public view for videos table
-- Date: 2025-01-07
-- Purpose: Allow Supabase PostgREST to access krai_content.videos via public schema

-- Create view in public schema pointing to krai_content.videos
CREATE OR REPLACE VIEW public.videos AS
SELECT * FROM krai_content.videos;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.videos TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.videos TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.videos TO service_role;

-- Comment
COMMENT ON VIEW public.videos IS 'View to access krai_content.videos via public schema for Supabase PostgREST';
