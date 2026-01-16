# n8n Workflows - DEPRECATED

⚠️ **Alle n8n Workflows wurden archiviert**

## Status

- ❌ **Nicht kompatibel** mit PostgreSQL-only Architektur
- 📦 **Archiviert** in `archive/`
- 🔒 **Read-only** - Keine Updates geplant

## Archivierte Workflows

Alle Workflows (v1 und v2) wurden nach `archive/` verschoben:
- `archive/v1/` - Original Workflows (19 Dateien: 11 JSON workflows, 5 supporting files, 3 JS code files)
- `archive/v2/` - Modernisierte Workflows (15 Dateien: 10 JSON workflows, 5 documentation files)
- **Status**: Alle Workflows bleiben Supabase-basiert - keine PostgreSQL-Credential-Updates durchgeführt

Siehe `archive/README.md` für Details.

## Moderne Alternativen

### 1. Laravel Dashboard (Empfohlen)
- **Visual Document Management** mit Drag-and-Drop
- **Stage-based Processing** via Filament UI
- **Real-time Status Tracking**
- **Dokumentation**: `docs/LARAVEL_DASHBOARD_INTEGRATION.md`

### 2. FastAPI Endpoints
- **Stage Processing**: `/documents/{id}/process/stage/{stage}`
- **Search APIs**: `/search/semantic`, `/search/error-codes`
- **Content APIs**: `/videos/search`, `/images/search`
- **Dokumentation**: `docs/api/STAGE_BASED_PROCESSING.md`

### 3. CLI Tools
- **Pipeline Processor**: `scripts/pipeline_processor.py`
- **Stage Selection**: `--stage <name>` oder `--stages <list>`
- **Smart Processing**: `--smart` (skip completed)
- **Batch Operations**: `--batch --directory /path/`
- **Dokumentation**: `docs/processor/QUICK_START.md`

## Warum deprecated?

Die n8n Workflows basieren auf:
- Supabase Vector Store Nodes (nicht mehr verwendet)
- PostgREST Views (entfernt)
- Legacy API Endpoints (refactored)
- Supabase Authentication (ersetzt durch JWT)

Die aktuelle Architektur verwendet:
- PostgreSQL mit pgvector (direkte Verbindung)
- FastAPI REST Endpoints
- JWT Authentication
- Stage-based Pipeline Processing

## Neue n8n Integration entwickeln?

Falls n8n-Integration gewünscht:

1. **Studiere aktuelle Architektur**: `docs/ARCHITECTURE.md`
2. **Verstehe FastAPI Endpoints**: `docs/api/STAGE_BASED_PROCESSING.md`
3. **Prüfe Pipeline Stages**: `docs/processor/PIPELINE_ARCHITECTURE.md`
4. **Erstelle neue Workflows** basierend auf HTTP Request Nodes zu FastAPI

**Aufwand**: Komplett neue Workflows erforderlich (keine Migration möglich)

## Support

- **Laravel Dashboard**: `docs/LARAVEL_DASHBOARD_INTEGRATION.md`
- **API Usage**: `docs/processor/QUICK_START.md`
- **Pipeline Architektur**: `docs/processor/PIPELINE_ARCHITECTURE.md`
