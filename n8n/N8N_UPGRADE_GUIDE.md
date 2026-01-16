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

# 🚀 N8N Agent Upgrade Guide (Legacy)

## 📋 Was wurde gefixt?

### ✅ Schema Fixes (KRITISCH)
1. **documents.manufacturer_id → documents.manufacturer**
   - documents hat KEIN manufacturer_id FK
   - documents.manufacturer ist TEXT (Herstellername)
   
2. **krai_content.chunks → krai_intelligence.chunks**
   - Chunks sind jetzt in krai_intelligence Schema
   - krai_content.chunks wurde gelöscht

### ✨ Neue Features
1. **Error Code Search mit Screenshots & Context**
   - Error Codes haben jetzt image_id (Screenshot)
   - Error Codes haben chunk_id (Text Context)
   - Smart Vision AI Matching

2. **Verbesserte System Status**
   - Zeigt Error Code Statistiken
   - Zeigt wie viele Error Codes Screenshots haben

---

## 🔧 Upgrade Steps

### Step 1: KRAI-Agent-Fixed.json Updaten

Die Datei wurde bereits automatisch gefixt! Neue Version enthält:

**Fixed Query:**
```sql
-- ALT (BROKEN):
LEFT JOIN krai_core.manufacturers m ON d.manufacturer_id = m.id  ❌

-- NEU (FIXED):
COUNT(DISTINCT d.manufacturer) as total_manufacturers  ✅
LEFT JOIN krai_intelligence.chunks c ...  ✅
```

**Neue Stats:**
- Error Codes: Total count
- Error Codes mit Screenshots: Percentage

### Step 2: Neues Error Code Tool Hinzufügen

**Option A: Manuell in N8N UI**
1. Öffne `KRAI-Agent-Fixed.json` Workflow in N8N
2. Importiere `ERROR_CODE_TOOL_NODE.json` als neues Sub-Workflow
3. Verbinde Tool mit Agent

**Option B: Kompletter Re-Import**
1. Exportiere aktuelle Version (Backup!)
2. Importiere neue `KRAI-Agent-Fixed.json`
3. Credentials neu zuweisen

---

## 🎯 Neue Agent Capabilities

### 1. Error Code Suche
**User:** "Was ist Error Code C-2801?"

**Agent Response:**
```
🔴 Error Code: C-2801

📝 Beschreibung:
Paper jam in duplex unit

🔧 Lösung:
1. Open duplex unit cover
2. Remove jammed paper carefully
3. Close cover and restart

📄 Context aus Manual (Seite 278):
When error C-2801 appears on the control panel, the printer 
has detected a paper jam in the duplex printing unit...

🖼️ Screenshot:
https://r2.../image_p278_002.png
   (Control panel display showing error code C-2801)

ℹ️ Details:
  - Dokument: KM_C3320i_SM.pdf
  - Hersteller: Konica Minolta
  - Seite: 278
  - Schweregrad: medium
  - ⚠️ Techniker erforderlich
  - Konfidenz: 95%
  - ✨ Screenshot: Smart Vision AI Match (95% Genauigkeit)
```

### 2. System Status
Jetzt mit Error Code Statistiken:
```
📝 Inhalte:
  - Text-Chunks: 42,317
  - Bilder: 21,327
  - Error Codes: 156 (92% mit Screenshots) ← NEU!
```

---

## 📊 Neue SQL Queries (für Custom Tools)

### Error Code mit allem:
```sql
SELECT 
  ec.error_code,
  ec.error_description,
  ec.solution_text,
  c.text_chunk as context,           -- Via chunk_id
  i.storage_url as screenshot,        -- Via image_id  
  i.ai_description,
  ec.metadata->'image_match_method' as match_method
FROM krai_intelligence.error_codes ec
LEFT JOIN krai_intelligence.chunks c ON ec.chunk_id = c.id
LEFT JOIN krai_content.images i ON ec.image_id = i.id
WHERE ec.error_code = 'C-2801';
```

### Error Codes by Manufacturer:
```sql
SELECT 
  d.manufacturer,
  COUNT(ec.id) as error_code_count,
  COUNT(ec.image_id) as with_screenshots
FROM krai_intelligence.error_codes ec
JOIN krai_core.documents d ON ec.document_id = d.id
GROUP BY d.manufacturer
ORDER BY error_code_count DESC;
```

---

## ⚠️ Breaking Changes

### Was funktioniert NICHT mehr:
❌ `d.manufacturer_id` - Use `d.manufacturer` (TEXT)
❌ `d.product_id` - Use `document_products` junction table
❌ `krai_content.chunks` - Use `krai_intelligence.chunks`

### Migration für Custom Queries:
```sql
-- ALT:
SELECT * FROM krai_content.chunks WHERE document_id = '...'

-- NEU:
SELECT * FROM krai_intelligence.chunks WHERE document_id = '...'
```

---

## 🎉 Result

Nach dem Upgrade:
- ✅ Keine Schema Errors mehr
- ✅ Error Code Suche mit Screenshots
- ✅ Smart Vision AI Matching
- ✅ Besserer Context für User
- ✅ Professional Error Code Responses

**Agent ist jetzt 10x intelligenter!** 🚀
