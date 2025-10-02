-- ============================================
-- N8N USER SETUP WITH RLS BYPASS
-- ============================================
-- Purpose: Create dedicated database user for n8n automation
-- with full access to krai_agent.memory table (bypasses RLS)
--
-- Security: This user has LIMITED access - only krai_agent.memory table
-- RLS is enabled but policies allow full CRUD for this user
--
-- Password: N8n_Kr4i_Ag3nt_2025!Secure#Mem
-- (Stored in: credentials.txt)
-- ============================================

-- 1) Create dedicated n8n database role
-- Password: N8n_Kr4i_Ag3nt_2025!Secure#Mem
CREATE ROLE n8n_user WITH LOGIN PASSWORD 'N8n_Kr4i_Ag3nt_2025!Secure#Mem';

-- 2) Grant connection rights to database
-- Note: In Supabase, CONNECT is usually already granted
GRANT CONNECT ON DATABASE postgres TO n8n_user;

-- 3) Grant USAGE on krai_agent schema (required to see tables)
GRANT USAGE ON SCHEMA krai_agent TO n8n_user;

-- 4) Grant table-level permissions (required even with RLS bypass policies)
-- This allows the user to interact with the table structure
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE krai_agent.memory TO n8n_user;

-- 5) Grant USAGE on sequences (for auto-increment IDs if any)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA krai_agent TO n8n_user;

-- 6) Enable Row Level Security on memory table
ALTER TABLE krai_agent.memory ENABLE ROW LEVEL SECURITY;

-- 7) Create RLS policies that grant n8n_user full access
-- These policies use USING (true) which means "always allow"

-- Policy: SELECT (read all rows)
CREATE POLICY "n8n_full_access_select" ON krai_agent.memory
  FOR SELECT
  TO n8n_user
  USING (true);

-- Policy: INSERT (can insert any row)
CREATE POLICY "n8n_full_access_insert" ON krai_agent.memory
  FOR INSERT
  TO n8n_user
  WITH CHECK (true);

-- Policy: UPDATE (can update any row)
CREATE POLICY "n8n_full_access_update" ON krai_agent.memory
  FOR UPDATE
  TO n8n_user
  USING (true)
  WITH CHECK (true);

-- Policy: DELETE (can delete any row)
CREATE POLICY "n8n_full_access_delete" ON krai_agent.memory
  FOR DELETE
  TO n8n_user
  USING (true);

-- ============================================
-- VERIFICATION QUERIES (run separately to test)
-- ============================================

-- Check if role exists
-- SELECT rolname FROM pg_roles WHERE rolname = 'n8n_user';

-- Check schema permissions
-- SELECT * FROM information_schema.role_table_grants 
-- WHERE grantee = 'n8n_user' AND table_schema = 'krai_agent';

-- Check RLS policies
-- SELECT * FROM pg_policies 
-- WHERE schemaname = 'krai_agent' AND tablename = 'memory';

-- ============================================
-- CONNECTION STRING FOR N8N
-- ============================================
-- Host: Your Supabase host (from Supabase Dashboard → Settings → Database)
-- Port: 5432
-- Database: postgres
-- User: n8n_user
-- Password: N8n_Kr4i_Ag3nt_2025!Secure#Mem
-- SSL Mode: require
--
-- Full connection string:
-- postgresql://n8n_user:N8n_Kr4i_Ag3nt_2025!Secure#Mem@<supabase-host>:5432/postgres?sslmode=require
-- ============================================

-- ============================================
-- CLEANUP (if needed - DO NOT RUN IN PRODUCTION)
-- ============================================
-- DROP POLICY IF EXISTS "n8n_full_access_select" ON krai_agent.memory;
-- DROP POLICY IF EXISTS "n8n_full_access_insert" ON krai_agent.memory;
-- DROP POLICY IF EXISTS "n8n_full_access_update" ON krai_agent.memory;
-- DROP POLICY IF EXISTS "n8n_full_access_delete" ON krai_agent.memory;
-- DROP ROLE IF EXISTS n8n_user;
-- ============================================
