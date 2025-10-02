-- ============================================
-- Migration: Add 'message' alias for n8n compatibility
-- Date: 2025-10-02
-- Purpose: n8n Postgres Memory Node expects 'message' field
--          Table keeps 'content', view exposes it as 'message'
-- ============================================

-- Update the view to expose content AS message
DROP VIEW IF EXISTS public.vw_agent_memory CASCADE;

CREATE OR REPLACE VIEW public.vw_agent_memory AS
SELECT 
    id, 
    session_id, 
    role, 
    content AS message,  -- Alias: n8n expects 'message', table has 'content'
    content,             -- Keep original for compatibility
    metadata, 
    tokens_used, 
    created_at, 
    updated_at
FROM krai_agent.memory;

-- Grant access (same as before)
GRANT SELECT, INSERT, UPDATE, DELETE ON public.vw_agent_memory TO service_role;
GRANT SELECT ON public.vw_agent_memory TO authenticated, anon;

-- Update comment
COMMENT ON VIEW public.vw_agent_memory IS 'Agent Memory: Exposes content as message for n8n compatibility';

-- ============================================
-- EXPLANATION
-- ============================================
-- Table krai_agent.memory has 'content' column (actual chat content)
-- View exposes it BOTH as 'content' AND 'message' (alias)
-- n8n Postgres Memory Node can use 'message' field
-- Other code can still use 'content' field
-- ============================================

-- VERIFICATION
-- SELECT id, session_id, role, message, content FROM public.vw_agent_memory LIMIT 5;
-- Both 'message' and 'content' should show the same data
-- ============================================
