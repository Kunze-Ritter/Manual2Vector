-- Migration 87: Create ONLY the 2 missing views (vw_chunks, vw_videos)
-- ======================================================================
-- Description: Create the last 2 missing views based on REAL table structure
-- Date: 2025-10-17
-- Reason: vw_chunks and vw_videos were missing
-- ======================================================================

-- IMPORTANT NOTES:
-- - embeddings are stored IN krai_intelligence.chunks (as a column!)
-- - There is NO separate krai_embeddings schema
-- - vw_chunks includes the embedding column
-- - vw_embeddings is just an ALIAS for vw_chunks

-- ======================================================================
-- Create missing views
-- ======================================================================

-- vw_videos (from krai_content.videos)
CREATE OR REPLACE VIEW public.vw_videos AS 
SELECT * FROM krai_content.videos;

-- vw_chunks (from krai_intelligence.chunks - includes embedding column!)
CREATE OR REPLACE VIEW public.vw_chunks AS 
SELECT * FROM krai_intelligence.chunks;

-- ======================================================================
-- Grant permissions
-- ======================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_videos TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_chunks TO anon, authenticated, service_role;

-- ======================================================================
-- RESULT:
-- Now ALL views exist:
-- - vw_videos → krai_content.videos
-- - vw_chunks → krai_intelligence.chunks (includes embeddings!)
-- ======================================================================
