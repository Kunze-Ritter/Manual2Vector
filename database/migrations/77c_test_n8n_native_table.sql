-- ============================================================================
-- Migration 77c: Test n8n Native Table Creation
-- ============================================================================
-- Purpose: Let n8n create its own table to see the expected structure
-- Date: 2025-10-11
-- ============================================================================

-- Drop our VIEW so n8n can create its own TABLE
DROP VIEW IF EXISTS public.n8n_chat_histories CASCADE;
DROP TRIGGER IF EXISTS n8n_chat_histories_insert_trigger ON public.n8n_chat_histories CASCADE;
DROP TRIGGER IF EXISTS n8n_chat_histories_update_trigger ON public.n8n_chat_histories CASCADE;
DROP TRIGGER IF EXISTS n8n_chat_histories_delete_trigger ON public.n8n_chat_histories CASCADE;
DROP FUNCTION IF EXISTS public.n8n_chat_histories_insert() CASCADE;
DROP FUNCTION IF EXISTS public.n8n_chat_histories_update() CASCADE;
DROP FUNCTION IF EXISTS public.n8n_chat_histories_delete() CASCADE;

-- Now n8n will create the table itself when you run the workflow!
-- After n8n creates it, run this to see the structure:

/*
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'n8n_chat_histories'
ORDER BY ordinal_position;

-- And see the actual data:
SELECT * FROM public.n8n_chat_histories LIMIT 5;
*/

SELECT 'VIEW dropped. Now let n8n create the table!' as status;
