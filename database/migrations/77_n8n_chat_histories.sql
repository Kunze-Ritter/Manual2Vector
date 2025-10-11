-- ============================================================================
-- Migration 77: n8n Chat Histories Table
-- ============================================================================
-- Purpose: Create the default table that n8n Postgres Memory expects
-- Date: 2025-10-11
-- Author: KRAI Development Team
-- ============================================================================

-- Create n8n_chat_histories table (n8n default)
CREATE TABLE IF NOT EXISTS public.n8n_chat_histories (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_n8n_chat_histories_session 
ON public.n8n_chat_histories(session_id);

CREATE INDEX IF NOT EXISTS idx_n8n_chat_histories_created 
ON public.n8n_chat_histories(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_n8n_chat_histories_session_created 
ON public.n8n_chat_histories(session_id, created_at DESC);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.n8n_chat_histories TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.n8n_chat_histories TO anon;
GRANT USAGE, SELECT ON SEQUENCE n8n_chat_histories_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE n8n_chat_histories_id_seq TO anon;

COMMENT ON TABLE public.n8n_chat_histories IS 
'Default n8n Postgres Memory table for chat history storage';

-- ============================================================================
-- Optional: Sync function to copy from krai_agent.memory to n8n format
-- ============================================================================
CREATE OR REPLACE FUNCTION public.sync_krai_to_n8n_memory()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert into n8n format when new message is added to krai_agent.memory
    INSERT INTO public.n8n_chat_histories (session_id, type, data, created_at)
    VALUES (
        NEW.session_id,
        NEW.role,
        jsonb_build_object(
            'content', NEW.content,
            'role', NEW.role,
            'metadata', NEW.metadata,
            'tokens_used', NEW.tokens_used
        ),
        NEW.created_at
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Optional trigger (commented out by default)
-- Uncomment if you want automatic sync from krai_agent.memory to n8n_chat_histories
-- CREATE TRIGGER sync_memory_to_n8n
--     AFTER INSERT ON krai_agent.memory
--     FOR EACH ROW
--     EXECUTE FUNCTION public.sync_krai_to_n8n_memory();

-- ============================================================================
-- Helper function: Get chat history for n8n
-- ============================================================================
CREATE OR REPLACE FUNCTION public.get_n8n_chat_history(
    p_session_id VARCHAR,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    session_id VARCHAR,
    type VARCHAR,
    data JSONB,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.id,
        h.session_id,
        h.type,
        h.data,
        h.created_at
    FROM public.n8n_chat_histories h
    WHERE h.session_id = p_session_id
    ORDER BY h.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION public.get_n8n_chat_history TO authenticated, anon;

-- ============================================================================
-- Helper function: Clear old chat histories
-- ============================================================================
CREATE OR REPLACE FUNCTION public.clear_old_n8n_histories(
    p_days_to_keep INTEGER DEFAULT 30
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.n8n_chat_histories
    WHERE created_at < NOW() - (p_days_to_keep || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION public.clear_old_n8n_histories TO authenticated;

-- ============================================================================
-- Test data (optional, comment out for production)
-- ============================================================================
-- INSERT INTO public.n8n_chat_histories (session_id, type, data) VALUES
--     ('test-session-001', 'human', '{"content": "Hello, I need help with error code C-9402"}'),
--     ('test-session-001', 'ai', '{"content": "C-9402 is a Fuser Unit error. Let me help you with that..."}');

COMMENT ON FUNCTION public.get_n8n_chat_history IS 
'Get chat history for a session (n8n compatible)';

COMMENT ON FUNCTION public.clear_old_n8n_histories IS 
'Clear chat histories older than specified days';
