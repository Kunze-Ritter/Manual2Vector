---
trigger: always_on
---

# KRAI Project Rules

## 📋 TODO Management (CRITICAL!)

**Bei JEDER Änderung am Code oder System MUSS TODO.md aktualisiert werden!**

### 1. Erledigte Tasks markieren

Format:
```markdown
- [x] **Task Name** ✅ (HH:MM)
  - Details was gemacht wurde
  - **File:** path/to/file.py
  - **Result:** Was wurde erreicht
```

Beispiel:
```markdown
- [x] **OEM Sync Reactivated** ✅ (08:37)
  - Fixed: OEM sync was disabled (TEMPORARY WORKAROUND comment)
  - Changed: Use `schema('krai_core').table('products')` instead of vw_products
  - **File:** `backend/utils/oem_sync.py`
  - **Result:** OEM info will now be saved!
```

### 2. Neue TODOs hinzufügen

Format:
```markdown
- [ ] **Task Name** 🔥 HIGH PRIORITY
  - **Task:** Was muss gemacht werden
  - **Example:** Konkretes Beispiel
  - **Implementation:** Code-Snippet oder Pseudo-Code
  - **Files to modify:** Liste der Dateien
  - **Priority:** HIGH/MEDIUM/LOW
  - **Effort:** X hours
  - **Status:** TODO
```

Beispiel:
```markdown
- [ ] **Agent Search with OEM Integration** 🔥 HIGH PRIORITY
  - **Task:** Expand search to include OEM manufacturers
  - **Example:** User searches "Lexmark CS920 error 900.01"
    - Also search: Konica Minolta (CS920 = Konica Engine!)
  - **Files to modify:**
    - `backend/api/agent_api.py`
    - `backend/api/search_api.py`
  - **Priority:** HIGH
  - **Effort:** 2-3 hours
  - **Status:** TODO
```

### 3. Priority Emojis

- 🔥 **HIGH PRIORITY** - Kritisch, muss bald gemacht werden
- 🔍 **MEDIUM PRIORITY** - Wichtig, aber nicht dringend
- 📌 **LOW PRIORITY** - Nice to have

### 4. Session Statistics aktualisieren

Am Ende jeder Session:
```markdown
### 📊 Session Statistics (YYYY-MM-DD)

**Time:** HH:MM-HH:MM (X minutes/hours)
**Commits:** X+ commits
**Files Changed:** X+ files
**Migrations Created:** X (numbers)
**Bugs Fixed:** X (list)
**Features Added:** X (list)

**Key Achievements:**
1. ✅ Achievement 1
2. ✅ Achievement 2
3. ✅ Achievement 3

**Next Focus:** What to do next 🎯
```

### 5. Mehrere TODO-Dateien

Checke und synchronisiere:
- `TODO.md` - Haupt-TODO (IMMER aktualisieren!)
- `TODO_PRODUCT_ACCESSORIES.md` - Accessory System
- `AGENT_TODO.md` - Agent Features
- `DB_FIXES_CHECKLIST.md` - Database Fixes

Bei größeren Features: Wichtigste TODOs in TODO.md zusammenfassen mit Referenz!

### 6. Last Updated Timestamp

IMMER am Ende von TODO.md aktualisieren:
```markdown
**Last Updated:** YYYY-MM-DD (HH:MM)
**Current Focus:** Was gerade gemacht wird
**Next Session:** Was als nächstes kommt
```

---

## 🗄️ Database Schema (CRITICAL!)

**IMMER DATABASE_SCHEMA.md als Referenz nutzen!**

Die Datei `DATABASE_SCHEMA.md` im /docs/database Verzeichnis enthält die ECHTE, aktuelle Datenbankstruktur direkt aus Supabase.

### Regeln:

1. **IMMER** `DATABASE_SCHEMA.md` lesen bevor du Annahmen über Tabellen/Spalten machst
2. **NIEMALS** raten welche Spalten existieren - IMMER in der Doku nachsehen
3. **NIEMALS** annehmen dass Tabellen in bestimmten Schemas sind - IMMER prüfen

### Bei DB-Änderungen:

1. Änderungen in Supabase durchführen
2. Neue CSV exportieren:
   ```sql
   SELECT table_schema, table_name, column_name, data_type, 
          character_maximum_length, is_nullable, column_default, udt_name
   FROM information_schema.columns 
   WHERE table_schema LIKE 'krai_%'
   ORDER BY table_schema, table_name, ordinal_position;
   ```
3. CSV als "Supabase...Columns.csv" im Root speichern
4. Script ausführen: `cd scripts && python generate_db_doc_from_csv.py`
5. Neue DATABASE_SCHEMA.md committen

### Wichtige Fakten:

- Embeddings sind IN `krai_intelligence.chunks` (Spalte: `embedding`)
- Es gibt KEIN `krai_embeddings` Schema
- Es gibt KEIN `krai_content.chunks` - nur `krai_intelligence.chunks`
- `parts_catalog` ist in `krai_parts` Schema (nicht `krai_content`)
- Alle Views nutzen `vw_` Prefix und sind im `public` Schema

**Datei-Pfad:** `c:\Users\haast\Docker\KRAI-minimal\DATABASE_SCHEMA.md`
**Update-Script:** `scripts/generate_db_doc_from_csv.py`

---

## 🔧 Code Style & Best Practices

### 1. Immer minimal & focused edits

- Nutze `edit` oder `multi_edit` tools
- Halte Änderungen klein und fokussiert
- Folge existierendem Code-Style

### 2. Keine Code-Ausgabe an User

- **NIEMALS** Code im Chat ausgeben (außer explizit angefragt)
- Stattdessen: Code-Edit-Tools nutzen
- User sieht Änderungen direkt in IDE

### 3. Imports immer am Anfang

- Imports MÜSSEN am Anfang der Datei sein
- Bei Edits: Separater Edit für Imports
- Niemals Imports in der Mitte des Codes

### 4. Runnable Code

- Code MUSS sofort lauffähig sein
- Alle Dependencies hinzufügen
- Alle Imports hinzufügen
- Bei Web Apps: Moderne UI (React, TailwindCSS, shadcn/ui)

---

## 🐛 Debugging Discipline

### 1. Root Cause First

- Adressiere die Ursache, nicht die Symptome
- Verstehe das Problem bevor du fixst

### 2. Logging hinzufügen

- Descriptive logging statements
- Error messages mit Context
- Track variable states

### 3. Tests hinzufügen

- Test functions um Problem zu isolieren
- Reproduzierbare Test Cases

### 4. Nur fixen wenn sicher

- Nur Code ändern wenn du die Lösung kennst
- Sonst: Debug-Logging hinzufügen und testen

---

## 📝 Documentation

### 1. Code Comments

- Erkläre WARUM, nicht WAS
- Komplexe Logik dokumentieren
- TODOs mit Context

### 2. Commit Messages

- Beschreibend und präzise
- Format: `[Component] What was changed`
- Beispiel: `[OEM] Reactivate OEM sync - fix PostgREST cache issue`

### 3. Migration Comments

- Jede Migration braucht klaren Comment
- Erkläre WARUM die Änderung nötig ist
- Beispiel: `-- Remove content_text (1.17 MB per document - wasteful!)`

---

## ⚠️ NEVER DO

1. ❌ Code im Chat ausgeben (außer explizit angefragt)
2. ❌ Raten welche DB-Spalten existieren
3. ❌ TODO.md nicht aktualisieren
4. ❌ Imports in der Mitte des Codes
5. ❌ Ungetesteten Code als "funktioniert" markieren
6. ❌ Große Edits (>300 lines) - aufteilen!
7. ❌ Tests löschen oder schwächen ohne Erlaubnis

---

## ✅ ALWAYS DO

1. ✅ TODO.md nach jeder Änderung aktualisieren inkl. timestamp
2. ✅ DATABASE_SCHEMA.md checken vor DB-Queries
3. ✅ Code-Edit-Tools nutzen statt Output
4. ✅ Minimal & focused edits
5. ✅ Tests hinzufügen für neue Features
6. ✅ Logging für Debugging
7. ✅ Session Statistics aktualisieren

---

**Diese Rules sind KRITISCH für den Projekterfolg!**
**Bei Unsicherheit: Lieber fragen als raten!**