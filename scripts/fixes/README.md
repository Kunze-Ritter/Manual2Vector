# 🔧 Database Fixes

Dieser Ordner enthält alle Database Fix Scripts in der richtigen Reihenfolge.

## 📋 Ausführungsreihenfolge:

### 1. Supabase SQL Fixes (in SQL Editor ausführen)

**Achtung:** SQL Dateien sind in `database/migrations/` verschoben!

#### 1.1 RPC Function Update
```bash
Datei: database/migrations/100_update_rpc_function_add_chunk_id.sql
```
Fügt `chunk_id` Parameter zur `insert_error_code` Funktion hinzu.

#### 1.2 Links manufacturer_id
```bash
Datei: database/migrations/101_fix_links_manufacturer_id.sql
```
Setzt `manufacturer_id` für alle Links.

---

### 2. Python Fixes (bereits ausgeführt ✅)

#### 2.1 Video Platform Fix
```bash
python scripts/fixes/fix_unknown_platform_videos.py
```
Status: ✅ Erledigt (13/13 Videos)

#### 2.2 Video manufacturer_id
```bash
python scripts/fixes/update_video_manufacturers.py
```
Status: ✅ Erledigt (217/217 Videos)

---

### 3. Nach neuem Processing

#### 3.1 Video-Product Linking
```bash
python scripts/fixes/link_videos_to_products.py
```
Status: ⏳ Wartet auf Document-Product Links

---

## ⚠️ WICHTIG:

**Reihenfolge einhalten!**
1. Zuerst: SQL Fixes in Supabase
2. Python Scripts sind bereits gelaufen
3. Nach Processing: Video-Product Linking

Siehe `DB_FIXES_CHECKLIST.md` im Root für Details!
