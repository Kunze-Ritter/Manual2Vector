# N8N Database User Setup

## 📋 Overview

This document describes the dedicated database user (`n8n_user`) for n8n automation workflows.

## 🎯 Purpose

- **User**: `n8n_user`
- **Access**: Full CRUD operations on `krai_agent.memory` table
- **Security**: RLS enabled, but policies grant full access to this specific user
- **Use Case**: n8n workflows can read/write agent memory without service role key

## 🔐 Credentials

```
Username: n8n_user
Password: N8n_Kr4i_Ag3nt_2025!Secure#Mem
Database: postgres
Port: 5432
SSL Mode: require
```

**Connection String:**
```
postgresql://n8n_user:N8n_Kr4i_Ag3nt_2025!Secure#Mem@db.crujfdpqdjzcfqeyhang.supabase.co:5432/postgres?sslmode=require
```

> ⚠️ **Security Note**: Password is stored in `credentials.txt` (not in git)

## 🚀 Setup Instructions

### 1. Run Migration

Execute the SQL migration in Supabase:

**Via Supabase Dashboard:**
1. Go to SQL Editor
2. Open `database/migrations/create_n8n_user.sql`
3. Execute the entire script

**Via Supabase CLI:**
```bash
supabase db push --file database/migrations/create_n8n_user.sql
```

### 2. Verify Setup

Run these queries to verify:

```sql
-- Check if user exists
SELECT rolname FROM pg_roles WHERE rolname = 'n8n_user';

-- Check permissions
SELECT * FROM information_schema.role_table_grants 
WHERE grantee = 'n8n_user' AND table_schema = 'krai_agent';

-- Check RLS policies
SELECT * FROM pg_policies 
WHERE schemaname = 'krai_agent' AND tablename = 'memory';
```

### 3. Configure n8n

In your n8n instance, add a PostgreSQL credential:

- **Host**: `db.crujfdpqdjzcfqeyhang.supabase.co`
- **Port**: `5432`
- **Database**: `postgres`
- **User**: `n8n_user`
- **Password**: `N8n_Kr4i_Ag3nt_2025!Secure#Mem`
- **SSL**: `require`

## 🔒 Security Details

### Row Level Security (RLS)

RLS is **ENABLED** on `krai_agent.memory` with the following policies:

| Policy Name | Operation | Condition |
|-------------|-----------|-----------|
| `n8n_full_access_select` | SELECT | `USING (true)` - Always allow |
| `n8n_full_access_insert` | INSERT | `WITH CHECK (true)` - Always allow |
| `n8n_full_access_update` | UPDATE | `USING (true)` - Always allow |
| `n8n_full_access_delete` | DELETE | `USING (true)` - Always allow |

### Access Limitations

The `n8n_user` has access **ONLY** to:
- ✅ `krai_agent.memory` table (full CRUD)
- ❌ NO access to other schemas/tables
- ❌ NO access to `krai_content.*`
- ❌ NO access to `krai_intelligence.*`
- ❌ NO superuser privileges

### Why RLS + Policies (not bypass)?

Instead of `ALTER TABLE ... FORCE ROW LEVEL SECURITY`, we use policies because:
1. ✅ More granular control (can restrict by user later)
2. ✅ Auditable (policies visible in `pg_policies`)
3. ✅ Flexible (can add conditions like `created_by = current_user` later)
4. ✅ Best practice (explicit > implicit)

## 📊 Use Cases

### Reading Agent Memory
```sql
SELECT * FROM krai_agent.memory 
WHERE agent_id = 'cascade' 
ORDER BY created_at DESC 
LIMIT 10;
```

### Writing Agent Memory
```sql
INSERT INTO krai_agent.memory (agent_id, memory_type, content, metadata)
VALUES ('cascade', 'conversation', 'User asked about...', '{"importance": "high"}');
```

### Updating Memory
```sql
UPDATE krai_agent.memory 
SET importance_score = 0.9 
WHERE id = 'some-uuid';
```

## 🧪 Testing

### Test Connection
```bash
psql "postgresql://n8n_user:N8n_Kr4i_Ag3nt_2025!Secure#Mem@db.crujfdpqdjzcfqeyhang.supabase.co:5432/postgres?sslmode=require"
```

### Test Access
```sql
-- Should work ✅
SELECT * FROM krai_agent.memory LIMIT 1;

-- Should fail ❌ (no access)
SELECT * FROM krai_content.documents LIMIT 1;
```

## 🔄 Cleanup (if needed)

**⚠️ WARNING**: Only run in development/testing!

```sql
-- Remove policies
DROP POLICY IF EXISTS "n8n_full_access_select" ON krai_agent.memory;
DROP POLICY IF EXISTS "n8n_full_access_insert" ON krai_agent.memory;
DROP POLICY IF EXISTS "n8n_full_access_update" ON krai_agent.memory;
DROP POLICY IF EXISTS "n8n_full_access_delete" ON krai_agent.memory;

-- Remove user
DROP ROLE IF EXISTS n8n_user;
```

## 📝 Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-10-02 | Initial setup | Cascade AI |

## 🔗 Related Files

- `database/migrations/create_n8n_user.sql` - Migration script
- `credentials.txt` - Credentials storage (not in git)
- `.gitignore` - Ensures credentials.txt not committed

---

**Questions?** Check Supabase docs on RLS: https://supabase.com/docs/guides/auth/row-level-security
