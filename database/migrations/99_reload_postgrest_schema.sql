-- =====================================================
-- RELOAD POSTGREST SCHEMA CACHE
-- =====================================================
-- This forces PostgREST to reload its schema cache
-- Run this after adding/modifying columns

-- Notify PostgREST to reload schema
NOTIFY pgrst, 'reload schema';

-- Alternative: If NOTIFY doesn't work, you can also restart PostgREST
-- Or use: SELECT pg_notify('pgrst', 'reload schema');
