# Archived n8n Workflows - Supabase Legacy

## Status: DEPRECATED & ARCHIVED

Diese Workflows sind **nicht kompatibel** mit der aktuellen PostgreSQL-only Architektur.

## Warum archiviert?

1. **Vector Store Nodes**: Verwenden `@n8n/n8n-nodes-langchain.vectorStoreSupabase` 
2. **PostgREST Abhängigkeiten**: Workflows erwarten PostgREST Views
3. **Supabase-spezifische Nodes**: `n8n-nodes-base.supabase` existiert nicht mehr
4. **Veraltete Authentifizierung**: Supabase API Keys statt JWT

## Was ist hier?

### v1/ - Original Workflows (19 Dateien)
**11 JSON Workflows:**
- KRAI-Agent.json, KRAI-Agent-Fixed.json, KRAI-Agent-V2.1-Complete.json
- TOOL_Error_Code_Search.json (6 Versionen: v1-v6, plus duplicate V6)
- TOOL_System_Status.json, TOOL_Document_Type_Filter.json
- TOOL_Video_Enrichment.json, TOOL_Link_Validation.json
- KRAI-Analytics-Logger.json

**8 Supporting Files:**
- ERROR_CODE_TOOL_NODE.json (JavaScript code)
- format_response_code.js, format_video_response.js
- README_V2.1.md

### v2/ - Modernisierte Workflows (15 Dateien, auch deprecated)
**10 JSON Workflows:**
- Technician-Agent V2.1.json
- KRAI-Master-Agent-V2.json, KRAI_Agent_Hybrid_Main.json
- Error-Agent-V2.json
- KRAI_Vector_Store_Test.json
- Tool-*.json (ErrorCodeSearch, DocumentationSearch, PartsSearch, ProductInfo, VideoSearch)

**5 Documentation Files:**
- README.md, README-V2-ARCHITECTURE.md
- README_HYBRID_SETUP.md, README_V2.1_ARCHITECTURE.md
- n8n-nodes.json

**Status**: Alle Workflows bleiben Supabase-basiert - keine PostgreSQL-Credential-Updates durchgeführt

## Migration Status

**Keine PostgreSQL-Migration durchgeführt:**
- Alle 21 JSON workflow files bleiben Supabase-basiert
- Credentials wurden nicht auf PostgreSQL aktualisiert
- Node-Namen und IDs unverändert
- Workflows sind vollständig deprecated und dienen nur als historische Referenz

## Neue n8n-Integration entwickeln

Für neue n8n-Integration mit PostgreSQL-only Setup:

### Erforderliche Änderungen

1. **Vector Store ersetzen**
   - Entferne `vectorStoreSupabase` Nodes
   - Implementiere HTTP Request Nodes zu FastAPI `/search/semantic` Endpoint
   - Nutze `backend/api/routes/search.py` Endpoints

2. **Database Queries aktualisieren**
   - Ersetze Supabase Nodes mit PostgreSQL Nodes
   - Credential: "PostgreSQL KRAI" (nicht "Postgres Supabase")
   - Connection String: `postgresql://postgres:password@localhost:5432/krai` 

3. **API Endpoints verwenden**
   - Error Codes: `GET /api/v1/error-codes/search` 
   - Documents: `GET /api/v1/documents` 
   - Videos: `GET /api/v1/videos/search` 
   - Images: `GET /api/v1/images/search` 
   - Siehe `docs/api/STAGE_BASED_PROCESSING.md` 

4. **Authentifizierung**
   - JWT Token statt Supabase API Key
   - Header: `Authorization: Bearer <token>` 
   - Token-Endpoint: `POST /api/v1/auth/token` 

### Empfohlene Alternative

**Laravel Dashboard** (empfohlen statt n8n):
- Visual Document Management
- Stage-based Processing Control
- Real-time Status Tracking
- Siehe `docs/LARAVEL_DASHBOARD_INTEGRATION.md` 

## Historischer Kontext

Diese Workflows wurden entwickelt für:
- Supabase Database mit Vector Store
- PostgREST Views für Datenzugriff
- MinIO Object Storage
- Legacy API Endpoints

Die Migration zu PostgreSQL-only (KRAI-002) und Stage-based Pipeline (KRAI-003) machte diese Workflows inkompatibel.

## Support

Für moderne Integration:
- **API Dokumentation**: `docs/processor/QUICK_START.md` 
- **Pipeline Architektur**: `docs/processor/PIPELINE_ARCHITECTURE.md` 
- **Laravel Dashboard**: `docs/LARAVEL_DASHBOARD_INTEGRATION.md` 

