-- ============================================================================
-- Migration 30: Grant Service Role Permissions on krai_content Schema
-- ============================================================================
-- Purpose: Allow service_role to access krai_content schema tables
--          Required for Python scripts (video enricher, link checker, etc.)
-- ============================================================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA krai_content TO service_role;
GRANT USAGE ON SCHEMA krai_intelligence TO service_role;
GRANT USAGE ON SCHEMA krai_core TO service_role;

-- Grant all privileges on all existing tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA krai_content TO service_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA krai_intelligence TO service_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA krai_core TO service_role;

-- Grant all privileges on all sequences
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA krai_content TO service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA krai_intelligence TO service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA krai_core TO service_role;

-- Make it default for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA krai_content 
GRANT ALL PRIVILEGES ON TABLES TO service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA krai_intelligence 
GRANT ALL PRIVILEGES ON TABLES TO service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA krai_core 
GRANT ALL PRIVILEGES ON TABLES TO service_role;

-- Same for sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA krai_content 
GRANT ALL PRIVILEGES ON SEQUENCES TO service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA krai_intelligence 
GRANT ALL PRIVILEGES ON SEQUENCES TO service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA krai_core 
GRANT ALL PRIVILEGES ON SEQUENCES TO service_role;

-- Also grant to anon role (for RLS policies)
GRANT USAGE ON SCHEMA krai_content TO anon;
GRANT USAGE ON SCHEMA krai_intelligence TO anon;
GRANT USAGE ON SCHEMA krai_core TO anon;

-- Anon gets SELECT only (RLS will control access)
GRANT SELECT ON ALL TABLES IN SCHEMA krai_content TO anon;
GRANT SELECT ON ALL TABLES IN SCHEMA krai_intelligence TO anon;
GRANT SELECT ON ALL TABLES IN SCHEMA krai_core TO anon;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 30: Service role permissions granted successfully!';
    RAISE NOTICE '   - service_role: Full access to krai_content, krai_intelligence, krai_core';
    RAISE NOTICE '   - anon: SELECT access (RLS controlled)';
END $$;
