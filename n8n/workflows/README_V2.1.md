# 🚀 KRAI AI Agent V2.1 - Complete Workflows

**Version:** 2.1.0  
**Date:** 2025-10-06  
**Status:** Production Ready

---

## 📁 **FILES IN THIS FOLDER:**

### **Main Workflow:**
```
KRAI-Agent-V2.1-Complete.json
```
**The complete AI Agent with ALL V2.1 features!**

### **Sub-Workflows (Tools):**
```
TOOL_System_Status.json          - System statistics
TOOL_Error_Code_Search.json      - Error code lookup with screenshots
TOOL_Document_Type_Filter.json   - Filter by document type (bulletins/manuals)
TOOL_Video_Enrichment.json       - YouTube/Vimeo/Brightcove analysis
TOOL_Link_Validation.json        - Link checker & fixer
```

---

## 🎯 **FEATURES:**

### **1. Vector Search (Semantic)**
- Durchsucht ALLE Dokumente semantisch
- Nutzt: `public.vw_embeddings` View
- Model: `nomic-embed-text:latest`
- Top K: 5 results

### **2. Error Code Search (SQL)**
- Findet Error Codes mit Screenshots
- Zeigt: Beschreibung, Lösung, Context, Screenshot
- Source: `krai_intelligence.error_codes`

### **3. Document Type Filter (SQL)**
- Filtert nach Typ:
  - `service_bulletin` - Updates, kurze Infos
  - `service_manual` - Vollständige Manuals
  - `parts_catalog` - Ersatzteil-Kataloge
  - `user_manual` - Bedienungsanleitungen

### **4. Video Enrichment (HTTP API)**
- Platforms: YouTube, Vimeo, Brightcove
- Extrahiert: Titel, Beschreibung, Dauer, Views, Thumbnails
- Speichert in Database mit Deduplication

### **5. Link Validation (HTTP API)**
- Überprüft Links (GET + HEAD requests)
- Folgt Redirects (301/302/307/308)
- Auto-Fixes: http→https, trailing punctuation
- Speichert Status in Database

### **6. System Status (SQL)**
- Vollständige Statistiken
- Zeigt: Docs, Chunks, Images, Videos, Links, Error Codes
- Mit Percentages und Health Checks

---

## 📋 **INSTALLATION:**

### **STEP 1: Import Main Workflow**

1. Open N8N: `http://localhost:5678`
2. Click **"Import from File"**
3. Select: `KRAI-Agent-V2.1-Complete.json`
4. Click **"Import"**

### **STEP 2: Import Sub-Workflows**

Import each tool separately:
- `TOOL_System_Status.json`
- `TOOL_Error_Code_Search.json`
- `TOOL_Document_Type_Filter.json`
- `TOOL_Video_Enrichment.json`
- `TOOL_Link_Validation.json`

### **STEP 3: Configure Credentials**

**Supabase Credentials:**
- URL: `https://YOUR-PROJECT.supabase.co`
- API Key: Your `service_role` key (from Supabase dashboard)

**Ollama Credentials:**
- URL: `http://localhost:11434`
- (No API key needed for local Ollama)

**PostgreSQL Credentials (for Memory):**
- Host: `db.YOUR-PROJECT.supabase.co`
- Database: `postgres`
- User: `postgres`
- Password: Your database password
- Port: `5432`
- SSL: `allow`

### **STEP 4: Link Sub-Workflows**

In the main workflow (`KRAI-Agent-V2.1-Complete`), each tool node needs to reference its sub-workflow:

1. Click on a Tool node (e.g., "Tool: System Status")
2. In **"Workflow ID"** dropdown, select the imported sub-workflow
3. Repeat for all tool nodes

### **STEP 5: Activate Workflow**

1. Toggle **"Active"** switch in top-right
2. Workflow is now live!

---

## 🧪 **TESTING:**

### **Test 1: Basic Conversation**
```
User: "Hallo! Zeige mir den System Status"
Expected: Full system statistics with all new features
```

### **Test 2: Vector Search**
```
User: "Wie wechsle ich den Toner bei einem HP LaserJet?"
Expected: Relevant manual sections
```

### **Test 3: Error Code (with Screenshot!)**
```
User: "Was ist Error Code C-2801?"
Expected: Description + Solution + Screenshot + Context
```

### **Test 4: Document Type Filter**
```
User: "Zeige alle Service Bulletins"
Expected: List of service bulletins with metadata
```

### **Test 5: Video Enrichment**
```
User: "Analysiere dieses Video: https://www.youtube.com/watch?v=dQw4w9WgXcQ"
Expected: Video metadata (title, duration, views, etc.)
```

### **Test 6: Link Validation**
```
User: "Überprüfe die Links im System"
Expected: Link statistics + broken links + fixes
```

---

## 🔧 **TROUBLESHOOTING:**

### **Problem: Tools nicht verfügbar**
**Fix:** Stelle sicher dass alle Sub-Workflows importiert und mit dem Main Workflow verlinkt sind.

### **Problem: Vector Search funktioniert nicht**
**Fix:** 
1. Check `public.vw_embeddings` view exists in Supabase
2. Verify Migration 35 was applied
3. Check column name is `embedding` not `embedding_vector`

### **Problem: Video/Link APIs fehlen**
**Fix:**
1. Backend muss laufen: `python backend/main.py`
2. Check endpoints: `http://localhost:8000/health`
3. Check `http://localhost:8000/content/tasks`

### **Problem: Credentials Error**
**Fix:**
1. Re-enter Supabase credentials
2. Use `service_role` key, not `anon` key
3. Check PostgreSQL credentials for memory

---

## 📊 **CAPABILITIES:**

**The agent can:**
- ✅ Search technical documentation semantically
- ✅ Find error codes with screenshots
- ✅ Distinguish between bulletins and manuals
- ✅ Analyze YouTube/Vimeo/Brightcove videos
- ✅ Validate and fix links
- ✅ Show comprehensive system statistics
- ✅ Remember conversation context
- ✅ Provide structured, helpful answers in German

---

## 🎨 **RESPONSE FORMATS:**

The agent uses rich formatting:
- 🔴 Error codes
- 📄 Documents
- 🎬 Videos  
- 🔗 Links
- ⚠️ Warnings
- ✅ Success messages
- 📊 Statistics

---

## 📝 **EXAMPLE CONVERSATIONS:**

### **Example 1: Error Code with Screenshot**
```
User: "Was ist Error C-2801?"

Agent: 
🔴 ERROR CODE: C-2801

📝 BESCHREIBUNG:
Paper jam in duplex unit

🔧 LÖSUNG:
1. Open duplex unit cover
2. Remove jammed paper carefully
3. Close cover and restart

📄 CONTEXT AUS MANUAL:
When error C-2801 appears on the control panel, the printer 
has detected a paper jam in the duplex printing unit...

🖼️ SCREENSHOT:
https://r2.cloudflare.com/.../image_p278_002.png
   Control panel display showing error code C-2801
   ✨ Match-Methode: vision_ai_smart_match

ℹ️ DETAILS:
  📄 Dokument: KM_C3320i_SM.pdf
  🏭 Hersteller: Konica Minolta
  📖 Seite: 278
  ⚠️ Schweregrad: medium
  👨‍🔧 Techniker: Nicht erforderlich
  📊 Konfidenz: 95%
```

### **Example 2: Service Bulletins**
```
User: "Zeige Service Bulletins zu Firmware Updates"

Agent:
📋 GEFUNDENE DOKUMENTE
Filter: service_bulletin

1. SB-2024-015_Firmware_Update_4.2.1.pdf
   🏭 Konica Minolta - bizhub C360
   📅 Datum: 15.03.2024
   💾 Größe: 2.3 MB
   📊 Inhalt: 15 Chunks, 3 Bilder, 2 Error Codes

2. SB-2024-012_Security_Patch_4.1.9.pdf
   🏭 Konica Minolta - bizhub C360
   📅 Datum: 02.02.2024
   💾 Größe: 1.8 MB
   📊 Inhalt: 12 Chunks, 2 Bilder

✅ Gesamt: 2 service_bulletin Dokumente
```

### **Example 3: Video Analysis**
```
User: "https://www.youtube.com/watch?v=abc123"

Agent:
🎬 VIDEO ERFOLGREICH ANALYSIERT!

📌 Titel: HP LaserJet M607 Maintenance Guide
🌐 Platform: YouTube
⏱️ Dauer: 15:32
👤 Kanal: HP Support
👁️ Aufrufe: 12,543
👍 Likes: 456

📝 Beschreibung:
Complete maintenance guide for HP LaserJet M607 series 
including toner replacement, cleaning procedures, and 
troubleshooting common issues...

🖼️ Thumbnail: https://i.ytimg.com/vi/abc123/maxresdefault.jpg

🔗 Video-URL: https://www.youtube.com/watch?v=abc123

✅ Video wurde in der Datenbank gespeichert!
   ID: 123e4567-e89b-12d3-a456-426614174000
   🏭 Verknüpft mit Hersteller
```

---

## 🎯 **NEXT STEPS:**

1. **Import all workflows** ✅
2. **Configure credentials** ✅
3. **Link sub-workflows** ✅
4. **Test all features** ✅
5. **Go live!** 🚀

---

## 📞 **SUPPORT:**

**Documentation:**
- Main docs: `../docs/n8n/`
- Backend API: `../ENDPOINT_REFERENCE.md`
- Database schema: `../database/migrations/`

**Issues:**
- Check backend logs
- Check N8N execution logs
- Verify Supabase connection
- Test endpoints directly

---

**READY TO USE!** 🎉

**This is the COMPLETE V2.1 agent with ALL features!**
