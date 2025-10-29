# 🚀 Quick Start - KRAI System

**Letzte Updates:** 21.10.2025

---

## 📋 SOFORT AUSFÜHREN (Supabase SQL):

### 1. RPC Function Update
```sql
-- Datei: database/migrations/100_update_rpc_function_add_chunk_id.sql
-- Öffne in Supabase SQL Editor und führe aus
```

### 2. Links manufacturer_id Fix
```sql
-- Datei: database/migrations/101_fix_links_manufacturer_id.sql
-- Öffne in Supabase SQL Editor und führe aus
```

**Status:** ⏳ Diese 2 SQL Scripts müssen noch ausgeführt werden!

---

## ✅ BEREITS ERLEDIGT:

- [x] Video Platform Fix (13/13 Videos)
- [x] Video manufacturer_id (217/217 Videos)
- [x] Chunk Linking Code (in Processor integriert)
- [x] Parts Linking Code (in Processor integriert)
- [x] Document-Product Linking Code (in Processor integriert)
- [x] Video Enrichment Fixes (Description, Title)

---

## 🎯 BEIM NÄCHSTEN PROCESSING:

Alle Code-Fixes sind implementiert! Beim nächsten Document Processing:

1. ✅ Error Codes → chunk_id (für Bilder)
2. ✅ Products → document_products (Verknüpfung)
3. ✅ Parts → related_error_codes (Verknüpfung)
4. ✅ Videos → korrekte Descriptions

**Dann ausführen:**
```bash
python scripts/fixes/link_videos_to_products.py
```

---

## 📚 WICHTIGE DOKUMENTE:

- `DB_FIXES_CHECKLIST.md` - Detaillierte Fix-Liste
- `MASTER_TODO_LIST.md` - Alle offenen Aufgaben
- `PROCESSING_CHECKLIST.md` - Processing Qualitätsprüfung
- `VIDEO_ENRICHMENT_STATUS.md` - Video Enrichment Status
- `scripts/fixes/README.md` - Fix Scripts Dokumentation

---

## 🔧 ENTWICKLUNG:

### API starten:
```bash
cd C:\Users\haast\Docker\KRAI-minimal
python -m backend.main
```
API läuft auf: http://localhost:8000

### Progressive Search testen:
```
OpenWebUI → krai-assistant → "HP Fehler 66.60.32"
```

### Video Enrichment:
```bash
python scripts/enrich_video_metadata.py --limit 10
```

---

## 📊 SYSTEM STATUS:

### ✅ Funktioniert:
- Progressive Streaming API
- Error Code Extraction
- Video Enrichment (99.7%)
- Manufacturer Linking (100%)

### ⏳ In Arbeit:
- Product Extraction (Code fertig, wartet auf Processing)
- Parts Linking (Code fertig, wartet auf Processing)
- Bilder-Verknüpfung (Code fertig, wartet auf Processing)

### ❌ Noch zu tun:
- 2 SQL Scripts in Supabase ausführen
- Neues Processing durchführen
- Video-Product Linking ausführen

---

**Nächster Schritt:** SQL Scripts in Supabase ausführen! 🎯
