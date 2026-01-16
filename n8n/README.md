# ⚠️ n8n Integration - DEPRECATED

**Status**: Alle Workflows archiviert (Stand: Januar 2025)

## Schnellübersicht

- ❌ **n8n Workflows**: Archiviert in `workflows/archive/`
- ✅ **Laravel Dashboard**: Empfohlene Alternative
- ✅ **FastAPI Endpoints**: Für programmatischen Zugriff
- ✅ **CLI Tools**: Für Batch-Processing

Siehe `workflows/README.md` für Details und Alternativen.

---

## Historische Dokumentation (Deprecated)

Die folgende Dokumentation beschreibt die **veraltete** Supabase-basierte n8n Integration.
Für aktuelle Integration siehe oben genannte Alternativen.

---

# N8N Integration (Legacy)

> **⚠️ DEPRECATED - Legacy Supabase Architecture**  
> **Migration Status:** All n8n workflows are deprecated as of November 2024 (KRAI-002).  
> **Reason:** These workflows rely on legacy Supabase architecture which has been replaced with PostgreSQL-only.  
> **Alternative:** Use Laravel Dashboard or FastAPI directly for automation.  
> **Reference:** See `README_DEPRECATION.md` for migration details.

This folder contains all n8n automation workflows and credentials for KRAI.

## 📁 Structure

```
n8n/
├─ workflows/           # n8n workflow JSON files
├─ credentials/         # Credential templates (no secrets!)
├─ start-n8n-chat-agent.ps1  # Startup script
└─ README.md           # This file
```

## 📚 Documentation

See `docs/n8n/` for detailed setup guides:

- **N8N_AI_AGENT_MODERN_SETUP.md** - Modern AI agent setup
- **N8N_CHAT_AGENT_SETUP.md** - Chat agent configuration
- **N8N_LANGCHAIN_AI_AGENT_SETUP.md** - LangChain integration
- **N8N_POSTGRES_MEMORY_INTEGRATION.md** - Database memory integration

## 🔐 Database Access (Legacy)

> **Note:** This section describes legacy Supabase access. Current PostgreSQL-only architecture uses direct database connections.

Legacy n8n workflows accessed the database via Supabase:

```
View: public.vw_agent_memory
Table: krai_agent.memory
Connection: Supabase URL + service_role_key (DEPRECATED)
```

## 🚀 Quick Start (Legacy - Not Recommended)

> **⚠️ DEPRECATED:** These workflows require Supabase credentials which are no longer supported.  
> **Recommended Alternative:** Use Laravel Dashboard (`laravel-admin/`) or FastAPI endpoints (`backend/api/`) for automation.  
> **Migration Guide:** See `README_DEPRECATION.md` for PostgreSQL-only alternatives.

### Legacy Workflow Usage (For Reference Only)

1. **Install n8n**: `npm install -g n8n`
2. **Start n8n**: `n8n start`
3. **Import workflows**: Import JSON files from `workflows/`
4. **⚠️ Note:** Workflows require legacy Supabase credentials (no longer configured by default)

## 🔗 Related

- Main docs: `../docs/n8n/`
- Database schema: `../database/migrations/07_agent_memory_table.sql`
- View migration: `../database/migrations/10_agent_memory_content_to_message.sql`
- Credentials: `../credentials.txt` (not in git)
