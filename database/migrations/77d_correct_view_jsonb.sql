-- ============================================================================
-- Migration 77d: Correct VIEW with JSONB Message Format
-- ============================================================================
-- Purpose: Create VIEW that matches n8n's actual JSONB format
-- Date: 2025-10-11
--
-- Discovery: n8n stores messages as JSONB with structure:
-- {
--   "content": "message text",
--   "type": "human" | "ai" | "system",
--   "additional_kwargs": {},
--   "response_metadata": {}
-- }
-- ============================================================================

-- Drop old VIEW if exists
DROP VIEW IF EXISTS public.n8n_chat_histories CASCADE;

-- Create VIEW that maps krai_agent.memory to n8n's JSONB format
CREATE OR REPLACE VIEW public.n8n_chat_histories AS
SELECT 
    -- n8n uses SERIAL id
    ROW_NUMBER() OVER (ORDER BY created_at) as id,
    session_id,
    -- n8n stores the entire message as JSONB
    jsonb_build_object(
        'content', content,
        'type', CASE 
            WHEN role = 'assistant' THEN 'ai'
            WHEN role = 'system' THEN 'system'
            WHEN role = 'tool' THEN 'tool'
            ELSE 'human'
        END,
        'additional_kwargs', COALESCE(metadata, '{}'::jsonb),
        'response_metadata', '{}'::jsonb
    ) as message,
    created_at
FROM krai_agent.memory
WHERE content IS NOT NULL 
  AND content != ''
  AND TRIM(content) != '';

COMMENT ON VIEW public.n8n_chat_histories IS 
'n8n-compatible view with JSONB message format matching LangChain PostgresChatMessageHistory';

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.n8n_chat_histories TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.n8n_chat_histories TO anon;

-- ============================================================================
-- INSTEAD OF Triggers for INSERT/UPDATE/DELETE
-- ============================================================================

-- INSERT Trigger
CREATE OR REPLACE FUNCTION public.n8n_chat_histories_insert()
RETURNS TRIGGER AS $$
DECLARE
    v_content TEXT;
    v_type TEXT;
BEGIN
    -- Extract content and type from JSONB message
    v_content := NEW.message->>'content';
    v_type := NEW.message->>'type';
    
    -- Skip empty messages
    IF v_content IS NULL OR v_content = '' OR TRIM(v_content) = '' THEN
        RAISE NOTICE 'Skipping empty message for session %', NEW.session_id;
        RETURN NULL;
    END IF;
    
    INSERT INTO krai_agent.memory (session_id, role, content, metadata, created_at)
    VALUES (
        NEW.session_id,
        -- Map LangChain types back to our role
        CASE 
            WHEN v_type = 'ai' THEN 'assistant'
            WHEN v_type = 'human' THEN 'user'
            WHEN v_type = 'system' THEN 'system'
            WHEN v_type = 'tool' THEN 'tool'
            ELSE 'user'
        END,
        v_content,
        COALESCE(NEW.message->'additional_kwargs', '{}'::jsonb),
        COALESCE(NEW.created_at, NOW())
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER n8n_chat_histories_insert_trigger
    INSTEAD OF INSERT ON public.n8n_chat_histories
    FOR EACH ROW
    EXECUTE FUNCTION public.n8n_chat_histories_insert();

-- UPDATE Trigger
CREATE OR REPLACE FUNCTION public.n8n_chat_histories_update()
RETURNS TRIGGER AS $$
DECLARE
    v_content TEXT;
    v_type TEXT;
BEGIN
    v_content := NEW.message->>'content';
    v_type := NEW.message->>'type';
    
    UPDATE krai_agent.memory
    SET 
        session_id = NEW.session_id,
        role = CASE 
            WHEN v_type = 'ai' THEN 'assistant'
            WHEN v_type = 'human' THEN 'user'
            WHEN v_type = 'system' THEN 'system'
            WHEN v_type = 'tool' THEN 'tool'
            ELSE 'user'
        END,
        content = v_content,
        metadata = COALESCE(NEW.message->'additional_kwargs', '{}'::jsonb),
        updated_at = NOW()
    WHERE id = (
        SELECT id FROM krai_agent.memory
        WHERE session_id = OLD.session_id
          AND created_at = OLD.created_at
        LIMIT 1
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER n8n_chat_histories_update_trigger
    INSTEAD OF UPDATE ON public.n8n_chat_histories
    FOR EACH ROW
    EXECUTE FUNCTION public.n8n_chat_histories_update();

-- DELETE Trigger
CREATE OR REPLACE FUNCTION public.n8n_chat_histories_delete()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM krai_agent.memory
    WHERE session_id = OLD.session_id
      AND created_at = OLD.created_at;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER n8n_chat_histories_delete_trigger
    INSTEAD OF DELETE ON public.n8n_chat_histories
    FOR EACH ROW
    EXECUTE FUNCTION public.n8n_chat_histories_delete();

-- Done!
SELECT 'VIEW created with correct JSONB format!' as status;
