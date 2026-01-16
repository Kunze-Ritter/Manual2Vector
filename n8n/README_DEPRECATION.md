# ⚠️ n8n Integration Deprecated

**Letzte Aktualisierung**: Januar 2025  
**Aktion**: Alle Workflows archiviert in `workflows/archive/`

## Aktuelle Situation

✅ **Archivierung abgeschlossen**:
- Alle v1 Workflows → `workflows/archive/v1/`
- Alle v2 Workflows → `workflows/archive/v2/`
- Supabase Credentials → `credentials/archive/`
- Dokumentation mit Deprecation Notices versehen

❌ **Nicht mehr verfügbar**:
- n8n Workflows (archiviert)
- Supabase Vector Store Integration
- PostgREST Views
- Legacy API Endpoints

✅ **Verfügbare Alternativen**:
- Laravel Dashboard (empfohlen)
- FastAPI REST Endpoints
- CLI Pipeline Processor

---

The n8n workflows in this directory reference the legacy Supabase architecture and are no longer maintained. They are kept for historical reference only.

## Current Status

- ❌ **Not compatible** with PostgreSQL-only architecture (KRAI-002)
- ❌ **References deprecated** Supabase Vector Store nodes
- ❌ **Uses PostgREST views** that no longer exist
- ❌ **Outdated authentication** and configuration patterns

## What's Available

### Historical Reference
- **Original n8n workflows**: `n8n/workflows/` 
- **Setup guides**: `n8n/SETUP_V2.1.md`, `n8n/N8N_*.md` 
- **Agent configurations**: `n8n/AGENT_*.md` 

### Current Alternatives

For modern, maintained integration options:

#### 1. Laravel Dashboard (Recommended)
- **Visual document management** with drag-and-drop upload
- **Stage-based processing control** via Filament UI
- **Real-time status tracking** with color-coded badges
- **Bulk operations** for multiple documents
- **Reference**: `docs/LARAVEL_DASHBOARD_INTEGRATION.md`

#### 2. FastAPI Endpoints
- **Stage-based API**: `/documents/{id}/process/stage/{stage}`
- **Multiple stages**: `/documents/{id}/process/stages`
- **Status monitoring**: `/documents/{id}/stages/status`
- **Search and content APIs**: `/search/*`, `/error-codes/*`, `/videos/*`, `/images/*`
- **Reference**: `docs/api/STAGE_BASED_PROCESSING.md`

#### 3. CLI Tools
- **Pipeline processor**: `scripts/pipeline_processor.py`
- **Stage selection**: `--stage <stage_name>` or `--stages <stage_list>`
- **Smart processing**: `--smart` (skip completed stages)
- **Batch operations**: `--batch --directory /path/to/pdfs/`
- **Reference**: `docs/processor/QUICK_START.md`

## Migration Requirements

If you need n8n integration with the current architecture, you would need to:

### 1. Database Migration
- **Replace Supabase Vector Store** with PostgreSQL pgvector queries
- **Update all database access** to use FastAPI endpoints instead of direct Supabase
- **Remove PostgREST view dependencies** - use direct PostgreSQL queries

### 2. Authentication Updates
- **Replace Supabase auth** with JWT token authentication
- **Update API endpoints** to use FastAPI instead of Supabase REST
- **Configure OAuth2** if needed for external service integration

### 3. Workflow Refactoring
- **Update all Supabase nodes** to HTTP Request nodes calling FastAPI
- **Replace Vector Store nodes** with custom pgvector query nodes
- **Update error handling** for new API response formats

### 4. Configuration Changes
- **Environment variables**: Remove `SUPABASE_*`, add `KRAI_ENGINE_*`
- **API endpoints**: Update from Supabase REST to FastAPI endpoints
- **Authentication**: Switch to JWT-based auth

## Historical Context

These n8n workflows were originally designed for:
- **Supabase database** with Vector Store integration
- **PostgREST views** for data access
- **Cloudflare R2** for object storage
- **Legacy API endpoints** that have been refactored

The migration to PostgreSQL-only architecture (KRAI-002) and stage-based pipeline (KRAI-003) made these workflows incompatible.

## For Reference Only

**Do not modify existing n8n docs** - they serve as historical reference for the Supabase-based architecture.

If you need to implement n8n integration with the current system:
1. **Study the current architecture**: `docs/ARCHITECTURE.md`
2. **Understand the API**: `docs/api/STAGE_BASED_PROCESSING.md`
3. **Review pipeline stages**: `docs/processor/PIPELINE_ARCHITECTURE.md`
4. **Create new workflows** based on current FastAPI endpoints

## Support

For questions about modern integration options:
- **Laravel Dashboard**: See `docs/LARAVEL_DASHBOARD_INTEGRATION.md`
- **API Usage**: See `docs/processor/QUICK_START.md`
- **Pipeline Architecture**: See `docs/processor/PIPELINE_ARCHITECTURE.md`

---

**Last Updated**: 2024-11-29  
**Status**: Deprecated  
**Alternative**: Use Laravel Dashboard or FastAPI endpoints
