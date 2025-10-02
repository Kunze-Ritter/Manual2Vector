# 🤖 n8n AI Agent - Postgres Memory Integration

**Version:** 1.0.0  
**Letzte Aktualisierung:** Oktober 2025  
**Zweck:** Integration des n8n AI Agents mit KRAI Postgres Memory

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Memory Tabelle](#memory-tabelle)
3. [PostgREST Views](#postgrest-views)
4. [n8n Konfiguration](#n8n-konfiguration)
5. [Beispiel-Workflows](#beispiel-workflows)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Übersicht

Das KRAI-System nutzt **Postgres Memory** für die n8n AI Agent Integration. Da der Supabase-Server **IPv6-only** ist und asyncpg von IPv4-Clients nicht verbinden kann, werden **PostgREST Views** als Bridge verwendet.

### Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                       N8N AI AGENT                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐         ┌─────────────────┐            │
│  │  Postgres       │         │  PostgREST      │            │
│  │  Memory Node    │────────>│  Views          │            │
│  │                 │         │  (public.vw_*)  │            │
│  └─────────────────┘         └─────────────────┘            │
│           │                           │                      │
│           │    IPv4 Connection        │                      │
│           └───────────┬───────────────┘                      │
│                       │                                      │
│                       ▼                                      │
│           ┌──────────────────────┐                          │
│           │   SUPABASE POOLER    │                          │
│           │   (Port 6543)        │                          │
│           └──────────────────────┘                          │
│                       │                                      │
│                       │ IPv6                                 │
│                       ▼                                      │
│           ┌──────────────────────┐                          │
│           │  krai_agent.memory   │                          │
│           │  + public.vw_*       │                          │
│           └──────────────────────┘                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Memory Tabelle

### `krai_agent.memory`

Die zentrale Tabelle für Agent Conversation History, kompatibel mit **n8n Postgres Memory Module**.

**Schema:**

```sql
CREATE TABLE krai_agent.memory (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'function', 'tool')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Spalten:**

| Spalte | Typ | Beschreibung | Beispiel |
|--------|-----|--------------|----------|
| `id` | UUID | Eindeutige ID | `a1b2c3d4-...` |
| `session_id` | VARCHAR(255) | n8n Session Identifier | `"demo-session-001"` |
| `role` | VARCHAR(50) | Message Role | `"user"`, `"assistant"`, `"system"` |
| `content` | TEXT | Message Content | `"What is error code E001?"` |
| `metadata` | JSONB | Zusätzliche Daten | `{"model": "gpt-4", "temperature": 0.7}` |
| `tokens_used` | INTEGER | Token Count | `150` |
| `created_at` | TIMESTAMPTZ | Zeitstempel | `2025-10-02 09:00:00+00` |
| `updated_at` | TIMESTAMPTZ | Update Zeitstempel | `2025-10-02 09:00:00+00` |

**Indexes:**

```sql
CREATE INDEX idx_memory_session_id ON krai_agent.memory(session_id);
CREATE INDEX idx_memory_created_at ON krai_agent.memory(created_at DESC);
CREATE INDEX idx_memory_session_created ON krai_agent.memory(session_id, created_at DESC);
```

---

## 📊 PostgREST Views

Alle krai_* Schemas sind über **public Views** für PostgREST zugänglich (IPv4-kompatibel).

### Verfügbare Views

| View Name | Source Schema | Zweck | Rows (Stand 02.10.2025) |
|-----------|---------------|-------|-------------------------|
| `vw_agent_memory` | krai_agent | **AI Agent Memory** | 3 |
| `vw_audit_log` | krai_system | System Change Log | 0 |
| `vw_processing_queue` | krai_system | Task Status Monitoring | 0 |
| `vw_documents` | krai_core | Document Metadata | 34 |
| `vw_images` | krai_content | Image Data + Deduplication | 9,223 |
| `vw_chunks` | krai_content | Text Chunks | 58,614 |
| `vw_embeddings` | krai_intelligence | Vector Embeddings | 0 |
| `vw_error_codes` | krai_intelligence | Error Solutions | 0 |
| `vw_manufacturers` | krai_core | Manufacturer Info | 6 |
| `vw_products` | krai_core | Product Specifications | 0 |
| `vw_webhook_logs` | krai_integrations | Webhook History | 0 |

**Warum Views?**
- ✅ PostgREST kann nur auf `public` Schema zugreifen
- ✅ Supabase Server ist IPv6-only (asyncpg funktioniert nicht von IPv4)
- ✅ Views bieten nahtlosen Cross-Schema-Zugriff
- ✅ RLS Policies werden beibehalten

---

## ⚙️ n8n Konfiguration

### 1. Postgres Connection Setup

**Credentials in n8n erstellen:**

```
Name: KRAI Supabase Memory
Type: Postgres
Host: aws-0-eu-central-1.pooler.supabase.com
Port: 6543
Database: postgres
User: postgres.crujfdpqdjzcfqeyhang
Password: yoMHeJeFTle8LKL7
Schema: public
SSL: Enable
```

### 2. Memory Node Konfiguration

**In AI Agent Node:**

1. **Memory Type:** Postgres Chat Memory
2. **Connection:** KRAI Supabase Memory (aus Step 1)
3. **Table Name:** `vw_agent_memory`
4. **Session ID Key:** `session_id`
5. **Message Fields:**
   - **Role Field:** `role`
   - **Content Field:** `content`
   - **Metadata Field:** `metadata`

### 3. Beispiel Node Setup

```json
{
  "nodes": [
    {
      "parameters": {
        "model": "gpt-4",
        "options": {
          "systemMessage": "You are a helpful AI assistant for KRAI documentation."
        }
      },
      "type": "n8n-nodes-langchain.agent",
      "name": "KRAI AI Agent",
      "memory": {
        "type": "postgres",
        "table": "vw_agent_memory",
        "sessionIdKey": "session_id"
      }
    }
  ]
}
```

---

## 🔍 Beispiel-Workflows

### Workflow 1: Basic Memory Chat

```javascript
// n8n Workflow: Basic Chat with Memory

// Input Node (Webhook)
{
  "session_id": "user-123",
  "message": "What is error code E001?"
}

// Agent Node (with Memory)
{
  "model": "gpt-4",
  "memory": {
    "type": "postgres",
    "connection": "KRAI Supabase",
    "table": "vw_agent_memory"
  }
}

// Output: Agent Response mit gespeichertem Context
```

### Workflow 2: Multi-Turn Conversation

```javascript
// Turn 1
User: "What printers does HP make?"
Assistant: "HP manufactures various printer series including..."

// Turn 2 (with memory context)
User: "Which one is best for home office?"
Assistant: "Based on HP's lineup I mentioned, the HP LaserJet Pro series..."
```

### Workflow 3: Memory mit Document Lookup

```sql
-- Agent kann auf alle Views zugreifen:

-- Find Error Code
SELECT error_code, error_description, solution_text 
FROM vw_error_codes 
WHERE error_code = 'E001';

-- Get Document Info
SELECT filename, content_summary 
FROM vw_documents 
WHERE manufacturer = 'HP';

-- Check Images
SELECT filename, ai_description 
FROM vw_images 
WHERE document_id = '...';
```

---

## 📊 Memory Analytics

### Conversation Statistics

```sql
-- Memory Stats pro Session
SELECT 
    session_id,
    COUNT(*) as message_count,
    SUM(tokens_used) as total_tokens,
    MIN(created_at) as first_message,
    MAX(created_at) as last_message
FROM vw_agent_memory
GROUP BY session_id
ORDER BY last_message DESC;
```

### Role Distribution

```sql
-- Message Verteilung nach Role
SELECT 
    role,
    COUNT(*) as count,
    AVG(LENGTH(content)) as avg_content_length
FROM vw_agent_memory
GROUP BY role;
```

### Recent Activity

```sql
-- Letzte 20 Messages aller Sessions
SELECT 
    session_id,
    role,
    content,
    created_at
FROM vw_agent_memory
ORDER BY created_at DESC
LIMIT 20;
```

---

## 🛠️ Helper Functions

### Get Session Memory

```sql
-- Abrufen aller Messages für eine Session
SELECT * FROM krai_agent.get_session_memory('demo-session-001', 20);
```

### Clear Old Memory

```sql
-- Löschen von Memory älter als 30 Tage
SELECT krai_agent.clear_old_memory(30);
```

---

## 🔧 Troubleshooting

### Problem: "Connection timeout"

**Ursache:** IPv6 vs IPv4 Issue  
**Lösung:** Verwende **Pooler (Port 6543)** statt Direct Connection:

```
❌ FALSCH: db.crujfdpqdjzcfqeyhang.supabase.co:5432
✅ RICHTIG: aws-0-eu-central-1.pooler.supabase.com:6543
```

### Problem: "Schema must be public"

**Ursache:** PostgREST kann nur `public` Schema zugreifen  
**Lösung:** Verwende **Views** statt direkter Tabellen:

```
❌ FALSCH: krai_agent.memory
✅ RICHTIG: vw_agent_memory
```

### Problem: "Permission denied"

**Ursache:** RLS Policy blockiert Zugriff  
**Lösung:** Verwende **Service Role Key** für volle Permissions:

```javascript
const client = createClient(
  'https://crujfdpqdjzcfqeyhang.supabase.co',
  'SERVICE_ROLE_KEY'  // Nicht ANON_KEY!
)
```

### Problem: "Table not found"

**Ursache:** View existiert nicht  
**Lösung:** Führe Migration aus:

```bash
# Check if views exist
SELECT table_name FROM information_schema.views 
WHERE table_schema = 'public' AND table_name LIKE 'vw_%';

# If missing, run migration
# database_migrations/06_agent_views_complete.sql
# database_migrations/07_agent_memory_table.sql
```

---

## 📚 Weitere Ressourcen

- **Datenbank Schema:** `database_migrations/DATABASE_SCHEMA_DOCUMENTATION.md`
- **Migration Guide:** `database_migrations/MIGRATION_GUIDE.md`
- **n8n AI Agent Setup:** `N8N_AI_AGENT_MODERN_SETUP.md`
- **PostgREST Docs:** https://postgrest.org/en/stable/

---

## ✅ Checkliste für n8n Setup

- [ ] Supabase Connection in n8n erstellt
- [ ] Memory Node konfiguriert (`vw_agent_memory`)
- [ ] Test Session ID definiert
- [ ] Agent mit Memory getestet
- [ ] Multi-Turn Conversation funktioniert
- [ ] Context wird korrekt gespeichert
- [ ] Analytics Query funktioniert

---

**Stand:** Oktober 2025  
**Migrations:** 06_agent_views_complete.sql, 07_agent_memory_table.sql  
**Status:** ✅ Production Ready
