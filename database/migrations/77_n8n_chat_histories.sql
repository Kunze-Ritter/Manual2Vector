-- ============================================================================
-- Migration 77: n8n Chat Histories View
-- ============================================================================
-- Purpose: Create VIEW that maps krai_agent.memory to n8n format
-- Date: 2025-10-11
-- Author: KRAI Development Team
--
-- Strategy: Instead of creating a separate table, we create a VIEW that
-- maps our existing krai_agent.memory table to the format n8n expects.
-- This way we have ONE source of truth and n8n can use it seamlessly.
-- ============================================================================

-- Drop existing table/view if it exists (in case it was created before)
DROP TABLE IF EXISTS public.n8n_chat_histories CASCADE;
DROP VIEW IF EXISTS public.n8n_chat_histories CASCADE;

-- Create VIEW that maps krai_agent.memory to n8n format
CREATE OR REPLACE VIEW public.n8n_chat_histories AS
SELECT 
    -- n8n expects integer ID, we use hash of UUID
    ('x' || substr(md5(id::text), 1, 8))::bit(32)::int as id,
    session_id,
    -- Map role to LangChain message types
    CASE 
        WHEN role = 'assistant' THEN 'ai'
        WHEN role = 'system' THEN 'system'
        WHEN role = 'tool' THEN 'tool'
        ELSE 'human'  -- user, function, or anything else → human
    END as type,
    content as message,  -- n8n Postgres Memory expects 'message' column
    jsonb_build_object(
        'content', content,
        'role', role,
        'metadata', metadata,
        'tokens_used', tokens_used
    ) as data,
    created_at
FROM krai_agent.memory;

COMMENT ON VIEW public.n8n_chat_histories IS 
'n8n-compatible view of krai_agent.memory - ONE source of truth!';

-- ============================================================================
-- INSTEAD OF Triggers: Allow n8n to INSERT/UPDATE/DELETE through the VIEW
-- ============================================================================

-- INSERT Trigger: When n8n inserts into view, insert into krai_agent.memory
CREATE OR REPLACE FUNCTION public.n8n_chat_histories_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO krai_agent.memory (session_id, role, content, metadata, tokens_used, created_at)
    VALUES (
        NEW.session_id,
        -- Map LangChain types back to our role
        CASE 
            WHEN NEW.type = 'ai' THEN 'assistant'
            WHEN NEW.type = 'human' THEN 'user'
            WHEN NEW.type = 'system' THEN 'system'
            WHEN NEW.type = 'tool' THEN 'tool'
            ELSE COALESCE(NEW.type, 'user')
        END,
        COALESCE(NEW.message, NEW.data->>'content', ''),  -- Support both 'message' and 'data.content'
        COALESCE(NEW.data->'metadata', '{}'::jsonb),
        COALESCE((NEW.data->>'tokens_used')::integer, 0),
        COALESCE(NEW.created_at, NOW())
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER n8n_chat_histories_insert_trigger
    INSTEAD OF INSERT ON public.n8n_chat_histories
    FOR EACH ROW
    EXECUTE FUNCTION public.n8n_chat_histories_insert();

-- UPDATE Trigger: When n8n updates view, update krai_agent.memory
CREATE OR REPLACE FUNCTION public.n8n_chat_histories_update()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE krai_agent.memory
    SET 
        session_id = NEW.session_id,
        role = CASE 
            WHEN NEW.type = 'ai' THEN 'assistant'
            WHEN NEW.type = 'human' THEN 'user'
            WHEN NEW.type = 'system' THEN 'system'
            WHEN NEW.type = 'tool' THEN 'tool'
            ELSE COALESCE(NEW.type, 'user')
        END,
        content = COALESCE(NEW.message, NEW.data->>'content', ''),  -- Support both 'message' and 'data.content'
        metadata = COALESCE(NEW.data->'metadata', '{}'::jsonb),
        tokens_used = COALESCE((NEW.data->>'tokens_used')::integer, 0),
        updated_at = NOW()
    WHERE id = (
        SELECT id FROM krai_agent.memory 
        WHERE ('x' || substr(md5(id::text), 1, 8))::bit(32)::int = OLD.id
        LIMIT 1
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER n8n_chat_histories_update_trigger
    INSTEAD OF UPDATE ON public.n8n_chat_histories
    FOR EACH ROW
    EXECUTE FUNCTION public.n8n_chat_histories_update();

-- DELETE Trigger: When n8n deletes from view, delete from krai_agent.memory
CREATE OR REPLACE FUNCTION public.n8n_chat_histories_delete()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM krai_agent.memory
    WHERE id = (
        SELECT id FROM krai_agent.memory 
        WHERE ('x' || substr(md5(id::text), 1, 8))::bit(32)::int = OLD.id
        LIMIT 1
    );
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER n8n_chat_histories_delete_trigger
    INSTEAD OF DELETE ON public.n8n_chat_histories
    FOR EACH ROW
    EXECUTE FUNCTION public.n8n_chat_histories_delete();

-- ============================================================================
-- Grant permissions on VIEW
-- ============================================================================
GRANT SELECT, INSERT, UPDATE, DELETE ON public.n8n_chat_histories TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.n8n_chat_histories TO anon;

-- ============================================================================
-- Helper function: Get chat history for n8n
-- ============================================================================

-- Drop existing function first (signature might have changed)
DROP FUNCTION IF EXISTS public.get_n8n_chat_history(VARCHAR, INTEGER);
DROP FUNCTION IF EXISTS public.get_n8n_chat_history(TEXT, INTEGER);

CREATE OR REPLACE FUNCTION public.get_n8n_chat_history(
    p_session_id VARCHAR,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    session_id VARCHAR,
    type VARCHAR,
    message TEXT,
    data JSONB,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ('x' || substr(md5(m.id::text), 1, 8))::bit(32)::int as id,
        m.session_id,
        m.role as type,
        m.content as message,
        jsonb_build_object(
            'content', m.content,
            'role', m.role,
            'metadata', m.metadata,
            'tokens_used', m.tokens_used
        ) as data,
        m.created_at
    FROM krai_agent.memory m
    WHERE m.session_id = p_session_id
    ORDER BY m.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION public.get_n8n_chat_history TO authenticated, anon;

-- ============================================================================
-- Helper function: Clear old chat histories
-- ============================================================================

-- Drop existing function first
DROP FUNCTION IF EXISTS public.clear_old_n8n_histories(INTEGER);

CREATE OR REPLACE FUNCTION public.clear_old_n8n_histories(
    p_days_to_keep INTEGER DEFAULT 30
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete from underlying krai_agent.memory table
    DELETE FROM krai_agent.memory
    WHERE created_at < NOW() - (p_days_to_keep || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION public.clear_old_n8n_histories TO authenticated;

-- ============================================================================
-- Test data (optional, comment out for production)
-- ============================================================================
-- Test by inserting through the VIEW - it will automatically go to krai_agent.memory!
-- INSERT INTO public.n8n_chat_histories (session_id, type, data) VALUES
--     ('test-session-001', 'user', '{"content": "Hello, I need help with error code C-9402"}'),
--     ('test-session-001', 'assistant', '{"content": "C-9402 is a Fuser Unit error. Let me help you with that..."}');

-- Verify it's in krai_agent.memory:
-- SELECT * FROM krai_agent.memory WHERE session_id = 'test-session-001';

-- ============================================================================
-- Comments
-- ============================================================================
COMMENT ON FUNCTION public.get_n8n_chat_history IS 
'Get chat history for a session (n8n compatible) - reads from krai_agent.memory';

COMMENT ON FUNCTION public.clear_old_n8n_histories IS 
'Clear chat histories older than specified days - deletes from krai_agent.memory';

-- ============================================================================
-- Summary
-- ============================================================================
-- This migration creates a VIEW that makes krai_agent.memory look like
-- n8n_chat_histories. Benefits:
--
-- ✅ ONE source of truth (krai_agent.memory)
-- ✅ n8n can read/write through the view
-- ✅ All data is in our schema
-- ✅ Easy to query and analyze
-- ✅ No data duplication
--
-- n8n will use: public.n8n_chat_histories (VIEW)
-- Data is stored in: krai_agent.memory (TABLE)
-- ============================================================================
