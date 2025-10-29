-- =====================================================
-- PostgreSQL Setup for KRAI Database
-- =====================================================
-- This migration sets up the PostgreSQL database with
-- pgvector extension for vector similarity search.
--
-- Run this FIRST before any other migrations.
-- =====================================================

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable uuid-ossp for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS krai_core;
CREATE SCHEMA IF NOT EXISTS krai_content;
CREATE SCHEMA IF NOT EXISTS krai_intelligence;
CREATE SCHEMA IF NOT EXISTS krai_system;
CREATE SCHEMA IF NOT EXISTS krai_parts;

-- Grant permissions (adjust user as needed)
GRANT USAGE ON SCHEMA krai_core TO PUBLIC;
GRANT USAGE ON SCHEMA krai_content TO PUBLIC;
GRANT USAGE ON SCHEMA krai_intelligence TO PUBLIC;
GRANT USAGE ON SCHEMA krai_system TO PUBLIC;
GRANT USAGE ON SCHEMA krai_parts TO PUBLIC;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA krai_core TO PUBLIC;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA krai_content TO PUBLIC;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA krai_intelligence TO PUBLIC;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA krai_system TO PUBLIC;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA krai_parts TO PUBLIC;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA krai_core GRANT ALL ON TABLES TO PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA krai_content GRANT ALL ON TABLES TO PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA krai_intelligence GRANT ALL ON TABLES TO PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA krai_system GRANT ALL ON TABLES TO PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA krai_parts GRANT ALL ON TABLES TO PUBLIC;

-- Log setup completion
DO $$
BEGIN
    RAISE NOTICE 'KRAI PostgreSQL setup completed successfully';
    RAISE NOTICE 'Extensions: vector, uuid-ossp';
    RAISE NOTICE 'Schemas: krai_core, krai_content, krai_intelligence, krai_system, krai_parts';
END $$;
