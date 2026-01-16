# ⚠️ DEPRECATED - Supabase Legacy Setup

**Diese Anleitung ist veraltet und funktioniert nicht mit der aktuellen PostgreSQL-only Architektur.**

**Für aktuelle Setup-Optionen siehe:**
- Laravel Dashboard: `docs/LARAVEL_DASHBOARD_INTEGRATION.md`
- FastAPI Endpoints: `docs/api/STAGE_BASED_PROCESSING.md`
- CLI Tools: `docs/processor/QUICK_START.md`

**Archivierte Workflows**: `workflows/archive/`

---

## Historische Dokumentation (Read-Only)

Die folgende Anleitung beschreibt das **veraltete** Supabase-basierte Setup.

---

# 🚀 N8N Agent V2.1 Upgrade Guide (Legacy)

---

## ⚠️ **DEPRECATION NOTICE - SUPABASE REFERENCES**

**This document contains historical Supabase references that are NO LONGER VALID.**

**Current Architecture (as of November 2024):**
- ✅ **PostgreSQL-only** (direct asyncpg connection pools)
- ❌ **Supabase** (deprecated and removed)
- ❌ **PostgREST** (deprecated and removed)

**For current setup instructions, see:**
- `docs/SUPABASE_TO_POSTGRESQL_MIGRATION.md` - Migration guide
- `DOCKER_SETUP.md` - Current PostgreSQL setup
- `DATABASE_SCHEMA.md` - Current schema reference

**This document is preserved for historical reference only.**

---

**Version:** V2.0 → V2.1 (Clean Refactoring)  
**Date:** 2025-10-06  
**Status:** DEPRECATED

---

## 🎯 **WAS IST NEU IN V2.1?**

### **✅ Backend Refactoring (KRITISCH!)**
```
✅ processors_v2/ → processors/
✅ Alle Imports aktualisiert
✅ Service Initialization Order gefixt
✅ Router Registration gefixt
✅ API Endpoints funktionieren jetzt!
```

### **🆕 NEUE FEATURES:**

#### **1. Content Management API**
```
POST /content/videos/enrich/sync
POST /content/links/check/sync
GET  /content/tasks
GET  /content/tasks/{task_id}
```

#### **2. Video Enrichment**
- ✅ YouTube API Integration
- ✅ Vimeo oEmbed
- ✅ Brightcove Support
- ✅ Automatic Deduplication
- ✅ Contextual Metadata

#### **3. Link Management**
- ✅ URL Validation
- ✅ Redirect Following (301/302/307/308)
- ✅ Auto-fixing (http→https)
- ✅ Trailing Punctuation Cleanup
- ✅ Batch Processing

---

## 📋 **N8N AGENT UPDATES NEEDED:**

### **STEP 1: API Endpoint Updates**

**OLD (V2.0):**
```
Base URL: http://localhost:8000
```

**NEW (V2.1):**
```
Base URL: http://localhost:8000
Health: /health ✅
Search: /search/health ✅
Features: /features/health ✅
Content: /content/tasks ✅ (NEW!)
```

### **STEP 2: New Tools to Add**

#### **Tool 1: Video Enrichment** 🎬
```json
{
  "name": "enrich_video",
  "description": "Enriches video metadata from YouTube, Vimeo, or Brightcove URLs. Extracts title, description, duration, thumbnails. Use when user asks about videos or provides video URLs.",
  "endpoint": "http://localhost:8000/content/videos/enrich/sync",
  "method": "POST",
  "body": {
    "url": "{{video_url}}",
    "document_id": null,
    "manufacturer_id": null
  }
}
```

**Example Usage:**
```
User: "Was ist in diesem Video? https://www.youtube.com/watch?v=abc123"
Agent: [Calls enrich_video tool]
Response: "Das Video 'HP Printer Maintenance' ist 12:34 Minuten lang und zeigt..."
```

#### **Tool 2: Link Validation** 🔗
```json
{
  "name": "validate_links",
  "description": "Validates and checks document links. Follows redirects, fixes broken links, cleans URLs. Use when user asks about link status or broken links.",
  "endpoint": "http://localhost:8000/content/links/check/sync",
  "method": "POST",
  "body": {
    "document_id": "{{document_id}}",
    "limit": 50
  }
}
```

**Example Usage:**
```
User: "Überprüfe die Links im Dokument xyz"
Agent: [Calls validate_links tool]
Response: "Von 45 Links sind 42 aktiv, 3 wurden automatisch gefixt..."
```

#### **Tool 3: Error Code Search (UPDATED)** 🔍
```sql
-- Updated query for V2.1
SELECT 
  ec.error_code,
  ec.error_description,
  ec.solution_text,
  ec.severity_level,
  ec.requires_technician,
  c.text_chunk as context_text,
  c.metadata->>'page_number' as page,
  i.storage_url as screenshot_url,
  i.ai_description as screenshot_description,
  d.filename as document_name,
  d.manufacturer,
  ec.confidence_score,
  ec.metadata->>'image_match_method' as match_method
FROM krai_intelligence.error_codes ec
LEFT JOIN krai_intelligence.chunks c ON ec.chunk_id = c.id
LEFT JOIN krai_content.images i ON ec.image_id = i.id
LEFT JOIN krai_core.documents d ON ec.document_id = d.id
WHERE UPPER(ec.error_code) = UPPER('{{error_code}}')
LIMIT 1;
```

---

## 🔧 **IMPLEMENTATION GUIDE:**

### **Option A: Update Existing Agent (Recommended)**

1. **Open N8N UI:** `http://localhost:5678`

2. **Open KRAI-Agent-Fixed Workflow**

3. **Add New HTTP Request Nodes:**
   - Node 1: "Video Enrichment Tool"
   - Node 2: "Link Validation Tool"

4. **Update AI Agent Tool Configuration:**
```javascript
{
  "tools": [
    {
      "name": "search_documents",
      "description": "...",
      // ... existing tools
    },
    {
      "name": "enrich_video",
      "description": "Enriches video URLs (YouTube, Vimeo, Brightcove). Use when user provides video link or asks about video content.",
      "http": {
        "method": "POST",
        "url": "http://localhost:8000/content/videos/enrich/sync",
        "body": {
          "url": "{{video_url}}"
        }
      }
    },
    {
      "name": "validate_links",
      "description": "Validates document links, follows redirects, fixes broken URLs. Use when user asks about link status.",
      "http": {
        "method": "POST",
        "url": "http://localhost:8000/content/links/check/sync",
        "body": {
          "document_id": "{{document_id}}",
          "limit": 50
        }
      }
    }
  ]
}
```

5. **Update System Status Query:**
```sql
-- Add video and link statistics
SELECT 
  'Database' as component,
  json_build_object(
    'documents', (SELECT COUNT(*) FROM krai_core.documents),
    'chunks', (SELECT COUNT(*) FROM krai_intelligence.chunks),
    'images', (SELECT COUNT(*) FROM krai_content.images),
    'videos', (SELECT COUNT(*) FROM krai_content.videos),  -- NEW!
    'links', (SELECT COUNT(*) FROM krai_content.links WHERE is_active = true),  -- NEW!
    'error_codes', (SELECT COUNT(*) FROM krai_intelligence.error_codes)
  ) as stats;
```

6. **Test New Tools:**
```
User: "Was ist in diesem Video? https://www.youtube.com/watch?v=dQw4w9WgXcQ"
User: "Überprüfe die Links im Dokument"
User: "Zeige System Status"
```

---

### **Option B: Fresh Import (Clean Start)**

1. **Backup Current Workflow:**
   - Export "KRAI-Agent-Fixed" in N8N UI
   - Save as `KRAI-Agent-V2.0-backup.json`

2. **Import New Workflow:**
   - We'll create: `KRAI-Agent-V2.1.json`
   - Import in N8N UI
   - Configure credentials

3. **Configure PostgreSQL Credentials:**
   ```
   Host: localhost (or krai-postgres for Docker)
   Port: 5432
   Database: krai
   User: postgres
   Password: YOUR-PASSWORD
   SSL: Disabled (for local development)
   ```

4. **Test All Endpoints:**
   - `/health` ✅
   - `/search/health` ✅
   - `/content/tasks` ✅

---

## 🧪 **TESTING CHECKLIST:**

### **Test 1: Basic Agent Functions**
```
✅ User: "Was ist KRAI?"
✅ User: "Zeige System Status"
✅ User: "Suche nach Error Code C-2801"
```

### **Test 2: Video Enrichment (NEW!)**
```
✅ User: "Was ist in diesem Video? https://www.youtube.com/watch?v=dQw4w9WgXcQ"
✅ Expected: Video title, description, duration
```

### **Test 3: Link Validation (NEW!)**
```
✅ User: "Überprüfe die Links"
✅ Expected: Link status, broken links, fixes applied
```

### **Test 4: Error Code Search (UPDATED)**
```
✅ User: "Was bedeutet Error Code C-2801?"
✅ Expected: Error description + context + screenshot
```

---

## 📊 **NEW AGENT CAPABILITIES:**

### **Before V2.1:**
```
✅ Search documents
✅ Error code lookup
✅ System status
```

### **After V2.1:**
```
✅ Search documents
✅ Error code lookup (with screenshots!)
✅ System status (with video/link stats!)
✅ Video enrichment (YouTube, Vimeo, Brightcove, Self-hosted) 🆕
✅ Link validation & fixing 🆕
✅ Content management 🆕
```

---

## 🎯 **EXAMPLE CONVERSATIONS:**

### **Example 1: Video Help**
```
User: "Ich habe ein Video zur Wartung gefunden: 
       https://www.youtube.com/watch?v=abc123"

Agent: [Calls enrich_video tool]
       
Response: "🎬 Video: 'HP LaserJet M607 Maintenance Guide'
          ⏱️ Dauer: 15:32 Minuten
          👁️ 12,543 Aufrufe
          
          📝 Beschreibung:
          Complete maintenance guide for HP LaserJet M607 series...
          
          🔗 Link: https://www.youtube.com/watch?v=abc123
          
          Ich habe das Video in der Datenbank gespeichert und 
          mit dem Dokument verknüpft."
```

### **Example 2: Link Check**
```
User: "Überprüfe alle Links im Konica Minolta Service Manual"

Agent: [Calls validate_links tool]

Response: "🔗 Link Überprüfung abgeschlossen!
          
          ✅ Aktiv: 42 Links
          ⚠️ Weitergeleitet: 3 Links (automatisch gefixt)
          ❌ Defekt: 2 Links
          
          Details:
          - 3 http→https Konvertierungen
          - 2 broken HP support links gefunden
          - Alle validen Links aktualisiert
          
          Möchtest du die defekten Links sehen?"
```

### **Example 3: Error Code with Everything**
```
User: "Was ist Error C-2801?"

Agent: [Calls error_code_search tool]

Response: "🔴 Error Code: C-2801
          
          📝 Paper jam in duplex unit
          
          🔧 Lösung:
          1. Open duplex unit cover
          2. Remove jammed paper
          3. Close cover and restart
          
          📄 Context (Seite 278):
          When C-2801 appears, the printer has detected...
          
          🖼️ Screenshot:
          [Image showing control panel with C-2801]
          https://r2.../image_p278_002.png
          
          ⚠️ Techniker erforderlich: Nein
          📊 Konfidenz: 95%
          
          Quelle: KM_C3320i_SM.pdf (Konica Minolta)"
```

---

## ⚠️ **BREAKING CHANGES:**

### **None! V2.1 is backwards compatible!**

All existing queries and tools still work. We only:
- ✅ Fixed internal imports
- ✅ Added new endpoints
- ✅ Improved service initialization

---

## 🚀 **DEPLOYMENT STEPS:**

1. **Update Backend:**
   ```bash
   git checkout refactor/v2.1-cleanup
   cd backend
   python main.py
   ```

2. **Verify Endpoints:**
   ```powershell
   Invoke-RestMethod "http://localhost:8000/health"
   Invoke-RestMethod "http://localhost:8000/content/tasks"
   ```

3. **Update N8N Agent:**
   - Add new tools (Video, Links)
   - Update system status query
   - Test all functions

4. **Go Live! 🎉**

---

## 📝 **COMMIT & RELEASE:**

```bash
# After testing
git add n8n/
git commit -m "feat: Update N8N agent for V2.1 (video enrichment + link validation)"
git checkout master
git merge refactor/v2.1-cleanup
git tag v2.1.0
git push --all
git push --tags
```

---

## 🎊 **RESULT:**

**Your N8N Agent is now:**
- ✅ 100% Compatible with V2.1
- ✅ Can enrich videos
- ✅ Can validate links
- ✅ Better error code search
- ✅ Production ready!

**TIME TO TEST!!!** 🚀
