# n8n Workflow Compatibility Matrix

## Archive Contents

**v1 Archive** (19 files total):
- 11 JSON workflow files
- 3 JavaScript code files (format_response_code.js, format_video_response.js, ERROR_CODE_TOOL_NODE.json)
- 5 supporting files (README_V2.1.md, duplicate V6 variants)

**v2 Archive** (15 files total):
- 10 JSON workflow files
- 5 documentation files (README.md, README-V2-ARCHITECTURE.md, README_HYBRID_SETUP.md, README_V2.1_ARCHITECTURE.md, n8n-nodes.json)

**Status**: All workflows remain Supabase-based. No PostgreSQL credential updates were performed.

## Zusammenfassung

| Workflow | PostgreSQL-kompatibel? | Grund | Alternative |
|----------|------------------------|-------|-------------|
| **v1 Workflows** (11 JSON) | | | |
| KRAI-Agent.json | ❌ Nein | Vector Store Node | FastAPI `/search/semantic` |
| KRAI-Agent-Fixed.json | ❌ Nein | Vector Store Node | FastAPI `/search/semantic` |
| KRAI-Agent-V2.1-Complete.json | ❌ Nein | Vector Store Node | FastAPI `/search/semantic` |
| TOOL_Error_Code_Search.json | ❌ Nein | Supabase credentials | Not migrated |
| TOOL_Error_Code_Search_v2.json | ❌ Nein | Supabase credentials | Not migrated |
| TOOL_Error_Code_Search_v3_MultipleImages.json | ❌ Nein | Supabase credentials | Not migrated |
| TOOL_Error_Code_Search_v4_SmartInput.json | ❌ Nein | Supabase credentials | Not migrated |
| TOOL_Error_Code_Search_v5_FixedInput.json | ❌ Nein | Supabase credentials | Not migrated |
| TOOL_Error_Code_Search_V6_MultiSource.json | ❌ Nein | Supabase credentials | Not migrated |
| TOOL_ Error Code Search V6 (Multi-Source).json | ❌ Nein | Duplicate of V6 | Not migrated |
| TOOL_System_Status.json | ❌ Nein | Supabase credentials | Not migrated |
| TOOL_Document_Type_Filter.json | ❌ Nein | Supabase credentials | Not migrated |
| TOOL_Video_Enrichment.json | ❌ Nein | Backend API fehlt | Laravel Dashboard |
| TOOL_Link_Validation.json | ❌ Nein | Backend API fehlt | Laravel Dashboard |
| KRAI-Analytics-Logger.json | ❌ Nein | Supabase credentials | Not migrated |
| **v1 Supporting Files** (8) | | | |
| ERROR_CODE_TOOL_NODE.json | - | JavaScript code | - |
| format_response_code.js | - | JavaScript code | - |
| format_video_response.js | - | JavaScript code | - |
| README_V2.1.md | - | Documentation | - |
| **v2 Workflows** (10 JSON) | | | |
| Technician-Agent V2.1.json | ❌ Nein | Vector Store Node | FastAPI `/search/semantic` |
| KRAI-Master-Agent-V2.json | ❌ Nein | Vector Store Node | FastAPI `/search/semantic` |
| KRAI_Agent_Hybrid_Main.json | ❌ Nein | Vector Store Node | FastAPI `/search/semantic` |
| Error-Agent-V2.json | ❌ Nein | Supabase credentials | Not migrated |
| Tool-ErrorCodeSearch.json | ❌ Nein | Supabase credentials | Not migrated |
| Tool-DocumentationSearch.json | ❌ Nein | Supabase credentials | Not migrated |
| Tool-PartsSearch.json | ❌ Nein | Supabase credentials | Not migrated |
| Tool-ProductInfo.json | ❌ Nein | Supabase credentials | Not migrated |
| Tool-VideoSearch.json | ❌ Nein | Supabase credentials | Not migrated |
| KRAI_Vector_Store_Test.json | ❌ Nein | Vector Store Node | Not migrated |
| **v2 Supporting Files** (5) | | | |
| README.md | - | Documentation | - |
| README-V2-ARCHITECTURE.md | - | Documentation | - |
| README_HYBRID_SETUP.md | - | Documentation | - |
| README_V2.1_ARCHITECTURE.md | - | Documentation | - |
| n8n-nodes.json | - | Node configuration | - |

## Legende

- ❌ **Inkompatibel**: Alle Workflows bleiben Supabase-basiert und deprecated
- **Keine Migration durchgeführt**: Credentials wurden nicht auf PostgreSQL aktualisiert
- **Grund**: Aufwand zu hoch, moderne Alternativen verfügbar (Laravel Dashboard, FastAPI)

## Detaillierte Analyse

### ❌ Inkompatibel: Vector Store Workflows

**Problem**: Verwenden `@n8n/n8n-nodes-langchain.vectorStoreSupabase`

**Betroffene Workflows**:
- KRAI-Agent.json
- KRAI-Agent-Fixed.json
- KRAI-Agent-V2.1-Complete.json
- Technician-Agent V2.1.json
- KRAI-Master-Agent-V2.json
- KRAI_Agent_Hybrid_Main.json

**Lösung**: HTTP Request Node zu FastAPI
```
POST http://localhost:8000/api/v1/search/semantic
{
  "query": "Wie wechsle ich den Toner?",
  "limit": 5,
  "manufacturer": "HP",
  "model": "LaserJet M607"
}
```

### ❌ Tool Workflows - Nicht migriert

**Status**: Alle Tool-Workflows bleiben Supabase-basiert

**Betroffene Workflows**:
- Tool-ErrorCodeSearch.json
- Tool-DocumentationSearch.json
- Tool-PartsSearch.json
- Tool-ProductInfo.json
- Tool-VideoSearch.json
- Error-Agent-V2.json
- TOOL_Error_Code_Search*.json (alle 6 Versionen in v1)

**Grund**: Keine PostgreSQL-Credential-Updates durchgeführt
- Migration nicht sinnvoll (Aufwand vs. Nutzen)
- Moderne Alternativen verfügbar
- Workflows bleiben als historische Referenz archiviert

### ❌ Inkompatibel: Backend API Workflows

**Problem**: Erwarten Backend-Endpoints die nicht existieren

**Betroffene Workflows**:
- TOOL_Video_Enrichment.json
- TOOL_Link_Validation.json

**Lösung**: Laravel Dashboard verwenden
- Video Management: Laravel Filament UI
- Link Validation: Manuell oder via Laravel Commands

## Migration Status

**Keine PostgreSQL-Migration durchgeführt**:
- Alle 21 JSON workflow files bleiben Supabase-basiert
- Credentials wurden nicht aktualisiert
- Node-Namen und IDs unverändert
- Workflows sind vollständig deprecated

## Empfehlung

**Nicht migrieren** - Aufwand zu hoch für geringen Nutzen.

**Stattdessen**: Laravel Dashboard + FastAPI Endpoints verwenden.

**Für neue n8n-Integration**: Von Grund auf mit PostgreSQL-Nodes und FastAPI HTTP Requests entwickeln.
