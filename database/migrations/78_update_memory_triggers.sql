-- ============================================================================
-- Migration 77b: Update n8n_chat_histories Triggers (Hotfix)
-- ============================================================================
-- Purpose: Fix NULL constraint violations in memory table
-- Date: 2025-10-11
-- ============================================================================

-- Drop existing triggers and functions
DROP TRIGGER IF EXISTS n8n_chat_histories_insert_trigger ON public.n8n_chat_histories CASCADE;
DROP TRIGGER IF EXISTS n8n_chat_histories_update_trigger ON public.n8n_chat_histories CASCADE;
DROP FUNCTION IF EXISTS public.n8n_chat_histories_insert() CASCADE;
DROP FUNCTION IF EXISTS public.n8n_chat_histories_update() CASCADE;

-- Recreate INSERT function with NULL handling
CREATE OR REPLACE FUNCTION public.n8n_chat_histories_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO krai_agent.memory (session_id, role, content, metadata, tokens_used, created_at)
    VALUES (
        NEW.session_id,
        COALESCE(NEW.type, 'user'),  -- Map 'type' back to 'role', default to 'user'
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

-- Recreate UPDATE function with NULL handling
CREATE OR REPLACE FUNCTION public.n8n_chat_histories_update()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE krai_agent.memory
    SET 
        session_id = NEW.session_id,
        role = COALESCE(NEW.type, 'user'),
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

-- Done!
SELECT 'Triggers updated successfully!' as status;
