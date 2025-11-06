-- =====================================================
-- PostgreSQL Setup for KRAI Database
-- =====================================================
-- This migration sets up the PostgreSQL database with
-- pgvector extension for vector similarity search.
--
-- Run this FIRST before any other migrations.
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;              -- Vector similarity search
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";         -- UUID generation
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;  -- Query performance monitoring
CREATE EXTENSION IF NOT EXISTS pg_trgm;             -- Trigram similarity for text search

-- Create schemas
CREATE SCHEMA IF NOT EXISTS krai_core;
CREATE SCHEMA IF NOT EXISTS krai_content;
CREATE SCHEMA IF NOT EXISTS krai_intelligence;
CREATE SCHEMA IF NOT EXISTS krai_system;
CREATE SCHEMA IF NOT EXISTS krai_parts;

-- Grant permissions to krai_user (more secure than PUBLIC)
GRANT USAGE ON SCHEMA krai_core TO krai_user;
GRANT USAGE ON SCHEMA krai_content TO krai_user;
GRANT USAGE ON SCHEMA krai_intelligence TO krai_user;
GRANT USAGE ON SCHEMA krai_system TO krai_user;
GRANT USAGE ON SCHEMA krai_parts TO krai_user;

-- Grant table permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA krai_core TO krai_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA krai_content TO krai_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA krai_intelligence TO krai_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA krai_system TO krai_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA krai_parts TO krai_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA krai_core TO krai_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA krai_content TO krai_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA krai_intelligence TO krai_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA krai_system TO krai_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA krai_parts TO krai_user;

-- Grant function permissions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA krai_core TO krai_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA krai_content TO krai_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA krai_intelligence TO krai_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA krai_system TO krai_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA krai_parts TO krai_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA krai_core GRANT ALL ON TABLES TO krai_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA krai_content GRANT ALL ON TABLES TO krai_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA krai_intelligence GRANT ALL ON TABLES TO krai_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA krai_system GRANT ALL ON TABLES TO krai_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA krai_parts GRANT ALL ON TABLES TO krai_user;

-- Create migration tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS krai_system.migrations (
    migration_name VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT
);

-- Record this migration
INSERT INTO krai_system.migrations (migration_name, applied_at, description) 
VALUES ('000_setup_pgvector', NOW(), 'PostgreSQL setup with pgvector, uuid-ossp, pg_stat_statements, and pg_trgm extensions')
ON CONFLICT (migration_name) DO NOTHING;

-- Verification queries
DO $$
DECLARE
    vector_version TEXT;
    schema_count INTEGER;
BEGIN
    -- Check pgvector version
    SELECT extversion INTO vector_version FROM pg_extension WHERE extname = 'vector';
    
    -- Count krai schemas
    SELECT COUNT(*) INTO schema_count 
    FROM information_schema.schemata 
    WHERE schema_name LIKE 'krai_%';
    
    -- Log results
    RAISE NOTICE 'KRAI PostgreSQL setup completed successfully';
    RAISE NOTICE 'Extensions: vector (%), uuid-ossp, pg_stat_statements, pg_trgm', vector_version;
    RAISE NOTICE 'Schemas created: % schemas (krai_core, krai_content, krai_intelligence, krai_system, krai_parts)', schema_count;
    RAISE NOTICE 'User permissions: Configured for krai_user';
    RAISE NOTICE 'Migration tracking: Recorded in krai_system.migrations';
END $$;

-- Performance configuration notes (set in docker-compose.yml command):
-- shared_buffers=256MB - Memory for shared data buffers
-- effective_cache_size=1GB - Estimate of memory available for disk caching
-- maintenance_work_mem=128MB - Memory for maintenance operations (VACUUM, CREATE INDEX)
-- checkpoint_completion_target=0.9 - Spread out checkpoint I/O over more time
-- wal_buffers=16MB - Memory for WAL data that hasn't been written to disk
-- default_statistics_target=100 - Statistics accuracy for query planner
-- random_page_cost=1.1 - SSD-optimized cost model
-- effective_io_concurrency=200 - Concurrent I/O capacity for SSD
-- work_mem=4MB - Memory for internal sort operations and hash tables
-- min_wal_size=1GB - Minimum WAL size before recycling
-- max_wal_size=4GB - Maximum WAL size before checkpoint
