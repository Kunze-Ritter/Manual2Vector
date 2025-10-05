# N8N Unified Error Code Search Tool

## 🎯 Purpose

Enable technicians to find **ALL available resources** for an error code in a single search:
- Service Manual entries
- Service Bulletins (highest priority - latest fixes!)
- Video Tutorials
- External Links
- Related Spare Parts

## 🔧 Tool Configuration

### Tool Name
`Search Error Code Resources`

### Tool Type
Supabase RPC Function Call

### Configuration

**Supabase Connection:**
- Use existing Supabase credential
- Schema: `public`
- Function: `search_error_code_resources`

**Parameters:**
```json
{
  "p_error_code": "{{$json.error_code}}",
  "p_manufacturer_id": "{{$json.manufacturer_id}}",
  "p_series_id": "{{$json.series_id}}",
  "p_limit": 20
}
```

## 📋 Tool Description (for Agent)

```
Search for ALL resources related to an error code across the entire knowledge base.

Use this tool when:
- Technician asks about a specific error code (e.g., "What is error C-2801?")
- Looking for troubleshooting information
- Finding related documentation, videos, or parts

Input:
- error_code (required): The error code to search for (e.g., "C-2801", "E045")
- manufacturer_id (optional): Filter by specific manufacturer
- series_id (optional): Filter by specific product series

Output:
Returns multiple resource types ranked by priority:
1. Service Bulletins (newest fixes - ALWAYS CHECK THESE FIRST!)
2. Service Manual entries (detailed technical info)
3. Video Tutorials (step-by-step visual guides)
4. External Links (additional resources)
5. Related Spare Parts (commonly needed for this error)

Each result includes:
- Title and description
- URL (for videos/links)
- Page number (for manual entries)
- Document type and priority
- Relevant metadata

IMPORTANT: Always present Service Bulletins FIRST if found - they contain the most up-to-date fixes!
```

## 🤖 Updated Agent System Prompt

Add to your agent's system message:

```
Du hast Zugriff auf das "Search Error Code Resources" Tool für umfassende Fehlercode-Suche.

WICHTIG - Priorisierung der Ergebnisse:
1. 🔴 SERVICE BULLETINS (Priority 1) - IMMER ZUERST ERWÄHNEN!
   - Enthalten die NEUESTEN Fixes und Updates
   - Überschreiben oft ältere Service Manual Einträge
   
2. 📘 SERVICE MANUAL (Priority 2)
   - Detaillierte technische Beschreibungen
   - Standard-Lösungsschritte
   
3. 🎥 VIDEO TUTORIALS (Priority 3)
   - Schritt-für-Schritt Anleitungen
   - Visuelle Hilfe für Techniker
   
4. 🔗 EXTERNE LINKS (Priority 4)
   - Zusätzliche Ressourcen
   - Hersteller Support-Seiten
   
5. 🔧 ERSATZTEILE (Priority 5)
   - Häufig benötigte Teile für diesen Fehler
   - Mit Teilenummern und Preis

Format deine Antwort strukturiert:

Beispiel für Fehlercode C-2801:

🔴 **AKTUELLSTE INFORMATION - Service Bulletin**
- Titel: "Updated Fix for C-2801 Fusing Unit Error"
- Datum: 15.12.2024
- Lösung: [Kurze Zusammenfassung]
- Dokument: [Service Bulletin Name] Seite XX

📘 **Service Manual**
- Beschreibung: [Error Description]
- Lösung: [Solution Steps]
- Seite: XX
- Screenshot verfügbar: Ja/Nein

🎥 **Video Tutorial verfügbar**
- Titel: "How to fix C-2801 step by step"
- Dauer: 5:30
- Link: [URL]

🔧 **Häufig benötigtes Ersatzteil**
- Fusing Unit (P/N: XYZ-123)
- Preis: €XXX
- Lagerbestand: Verfügbar

Wenn KEIN Service Bulletin gefunden wird, erwähne das explizit:
"ℹ️ Hinweis: Für diesen Fehlercode gibt es aktuell kein Service Bulletin. Die Informationen stammen aus dem Service Manual."
```

## 🔄 Example N8N Workflow

### Node 1: Agent (with Tool)
```json
{
  "name": "KRAI AI Agent",
  "type": "@n8n/n8n-nodes-langchain.agent",
  "parameters": {
    "options": {
      "systemMessage": "[Use updated prompt above]"
    }
  }
}
```

### Node 2: Supabase Tool - Search Error Code
```json
{
  "name": "Search Error Code Resources",
  "type": "@n8n/n8n-nodes-langchain.toolSupabase",
  "parameters": {
    "operation": "rpc",
    "functionName": "search_error_code_resources",
    "toolDescription": "Search for ALL resources related to an error code. Returns service manuals, bulletins, videos, links, and parts ranked by priority.",
    "parameters": {
      "p_error_code": "={{$json.error_code}}",
      "p_manufacturer_id": "={{$json.manufacturer_id || null}}",
      "p_series_id": "={{$json.series_id || null}}",
      "p_limit": 20
    }
  }
}
```

## 📊 Result Structure

The function returns a table with these columns:

| Column | Type | Description |
|--------|------|-------------|
| `resource_type` | TEXT | Type: `error_code`, `chunk`, `video`, `link`, `spare_part` |
| `resource_id` | UUID | Unique ID of the resource |
| `title` | TEXT | Resource title/summary |
| `description` | TEXT | Full description/solution text |
| `url` | TEXT | URL for videos/links (NULL for others) |
| `page_number` | INTEGER | Page number in document (NULL for external resources) |
| `priority` | INTEGER | 1=highest (bulletins), 5=lowest (parts) |
| `relevance_score` | NUMERIC | Confidence/relevance score (0.0-1.0) |
| `document_type` | TEXT | Document type (e.g., `service_bulletin`, `service_manual`) |
| `document_title` | TEXT | Title of the source document |
| `metadata` | JSONB | Additional context (varies by resource type) |

## 🧪 Testing

### Test 1: Simple Search
```sql
-- Find all resources for error C-2801
SELECT * FROM search_error_code('C-2801');
```

### Test 2: With Manufacturer Filter
```sql
-- Find resources for C-2801 from HP
SELECT * FROM search_error_code_resources(
    'C-2801',
    (SELECT id FROM krai_core.manufacturers WHERE name ILIKE '%HP%' LIMIT 1),
    NULL,
    20
);
```

### Test 3: Get Summary
```sql
-- Get quick summary of available resources
SELECT get_error_code_summary('C-2801');
```

**Expected Output:**
```json
{
  "error_code": "C-2801",
  "total_resources": 12,
  "by_type": {
    "error_code": 3,
    "video": 2,
    "link": 4,
    "spare_part": 3
  },
  "highest_priority": 1,
  "has_bulletin": true
}
```

## 📝 Migration Requirements

**Before using this tool, ensure these migrations are applied:**

1. ✅ Migration 28: `28_denormalize_links_videos_for_unified_search.sql`
   - Adds `manufacturer_id`, `series_id` to links/videos
   - Adds `priority_level` to documents
   - Backfills existing data

2. ✅ Migration 29: `29_unified_error_code_search_function.sql`
   - Creates `search_error_code_resources()` function
   - Creates simplified `search_error_code()` function
   - Creates `get_error_code_summary()` helper

3. ✅ Code Update: `document_processor.py`
   - Auto-links manufacturer/series when saving links/videos
   - Uses Migration 28's `auto_link_resource_to_document()` function

## 🎉 Benefits for Technicians

**Before:**
- Search only finds Service Manual entries
- Videos and bulletins are missed
- Multiple separate searches needed
- No awareness of latest updates

**After:**
- One search finds EVERYTHING
- Service Bulletins highlighted (critical!)
- Videos for visual learners
- Related parts instantly available
- Prioritized by importance

**Result:** Faster repairs, fewer callbacks, happier customers! 🚀
