---
trigger: always_on
---

# KRAI Project Rules

**This document contains CRITICAL project rules that MUST be followed at all times.**

---

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

Die Datei `DATABASE_SCHEMA.md` im Root-Verzeichnis (`c:\Users\haast\Docker\KRAI-minimal\DATABASE_SCHEMA.md`) enthält die ECHTE, aktuelle Datenbankstruktur direkt aus PostgreSQL.

### Regeln

1. **IMMER** `DATABASE_SCHEMA.md` lesen bevor du Annahmen über Tabellen/Spalten machst
2. **NIEMALS** raten welche Spalten existieren - IMMER in der Doku nachsehen
3. **NIEMALS** annehmen dass Tabellen in bestimmten Schemas sind - IMMER prüfen

### Bei DB-Änderungen

1. Änderungen in PostgreSQL durchführen (via pgAdmin, DBeaver, oder SQL-Script)

2. Neue CSV exportieren:

   ```sql
   SELECT table_schema, table_name, column_name, data_type, 
          character_maximum_length, is_nullable, column_default, udt_name
   FROM information_schema.columns 
   WHERE table_schema LIKE 'krai_%'
   ORDER BY table_schema, table_name, ordinal_position;
   ```

3. CSV als "PostgreSQL_Columns.csv" im Root speichern

4. Script ausführen: `cd scripts && python generate_db_doc_from_csv.py`

5. Neue DATABASE_SCHEMA.md committen

### Wichtige Fakten

**Embeddings:**

- Embeddings sind IN `krai_intelligence.chunks` (Spalte: `embedding`, Typ: `vector(768)`)
- Es gibt KEIN separates `krai_embeddings` Schema
- View: `public.vw_embeddings` ist ein ALIAS für `public.vw_chunks`

**Schemas:**

- `krai_content` - Images, Links, Videos, Print Defects, Tables (5 Tabellen)
- `krai_core` - Documents, Products, Manufacturers, Series (11 Tabellen)
- `krai_intelligence` - Chunks, Error Codes, Solutions (13 Tabellen)
- `krai_parts` - Parts Catalog, Accessories (2 Tabellen)
- `krai_system` - System-Tabellen (5 Tabellen)
- `krai_users` - User-Tabellen (2 Tabellen)

**Views:**

- Alle Views nutzen `vw_` Prefix und sind im `public` Schema
- Views werden automatisch via Migration `002_views.sql` erstellt

**Wichtige Tabellen:**

- `krai_core.products` - Hat Spalten: `specifications`, `urls`, `metadata` (alle JSONB)
- `krai_core.manufacturers` - Hersteller (z.B. "Hewlett Packard", "Brother", "Canon")
- `krai_core.product_accessories` - Zubehör-Beziehungen
- `krai_core.oem_relationships` - OEM-Beziehungen zwischen Herstellern
- `krai_intelligence.chunks` - Text-Chunks mit `embedding` Spalte
- `krai_parts.parts_catalog` - Ersatzteile

**Datei-Pfad:** `c:\Users\haast\Docker\KRAI-minimal\DATABASE_SCHEMA.md`
**Update-Script:** `scripts/generate_db_doc_from_csv.py`

---

## 🏭 Manufacturer Name Mapping (CRITICAL!)

**Problem:** Verschiedene Namen für denselben Hersteller!

### Mapping Rules

**IMMER** diese Mappings verwenden:

- `HP Inc.` → `Hewlett Packard` (DB-Name)
- `HP` → `Hewlett Packard`
- `Hewlett-Packard` → `Hewlett Packard`
- `Brother Industries` → `Brother`
- `Konica Minolta Business Solutions` → `Konica Minolta`

### Implementation

1. **In `ManufacturerVerificationService`:**
   - `manufacturer_name_mapping` Dictionary nutzen
   - Mapping in `discover_product_page()` anwenden

2. **In `ClassificationProcessor`:**
   - Erkannten Manufacturer-Namen mappen bevor DB-Lookup

3. **Bei neuen Herstellern:**
   - Zuerst in `krai_core.manufacturers` checken welcher Name in DB ist
   - Mapping hinzufügen falls nötig

**Beispiel:**
```python
manufacturer_name_mapping = {
    'HP Inc.': 'Hewlett Packard',
    'HP': 'Hewlett Packard',
}

# Apply mapping
if manufacturer in manufacturer_name_mapping:
    manufacturer = manufacturer_name_mapping[manufacturer]
```

---

## 🔍 Product Discovery Integration

**Automatische Product Page Discovery nach Classification**

### Wann wird Product Discovery ausgeführt

1. **Automatisch nach Classification:**
   - Wenn `manufacturer_verification_service` vorhanden
   - Wenn Manufacturer erkannt wurde
   - Wenn Models extrahiert werden konnten

2. **Model-Extraktion:**
   - Aus Context (wenn vorhanden)
   - Aus Filename via Regex-Patterns
   - Patterns: `E877`, `M454dn`, `HL-L8360CDW`, etc.

### save_to_db Parameter

**IMMER `save_to_db=True` in Production:**

- In `ClassificationProcessor.process()`
- In Pipeline-Integration

**`save_to_db=False` nur für:**

- Unit Tests
- Debugging
- Lokale Entwicklung mit Schema-Mismatch

### Discovery Strategies (in Reihenfolge)

1. **URL Patterns** - Schnell, zuverlässig
2. **Perplexity AI** - KI-basiert mit Citations (95% Confidence)
3. **Google Custom Search API** - Falls konfiguriert
4. **Web Scraping** - Fallback

### Logging

```python
self.logger.info(f"🔍 Starting product discovery for {len(models)} model(s)")
self.logger.info(f"   Discovering: {manufacturer} {model}")
self.logger.success(f"   ✅ Found: {result['url']}")
self.logger.warning(f"   ⚠️  No product page found for {model}")
```

### Return Format

```python
{
    'model': 'E877',
    'url': 'https://support.hp.com/...',
    'confidence': 0.95,
    'product_id': 'uuid'  # Wenn saved to DB
}
```

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
- Bei Web Apps: Laravel/Filament (existing dashboard)

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

## 🧪 Testing & Quality Assurance

### 1. Test-Typen

**Unit Tests:**
- Einzelne Funktionen/Methoden testen
- Mocks für externe Dependencies
- Schnell und isoliert

**Integration Tests:**
- Mehrere Komponenten zusammen testen
- Echte DB-Verbindung (Test-DB)
- Pipeline-Stages testen

**End-to-End Tests:**
- Komplette Pipeline mit echten Dokumenten
- Alle Services integriert
- Längere Laufzeit

### 2. Test-Dateien Naming

- `test_*.py` - Unit/Integration Tests
- `test_*_integration.py` - Explizite Integration Tests
- `test_*_e2e.py` - End-to-End Tests
- `check_*.py` - Verification Scripts (keine echten Tests)

### 3. Test-Daten

**Kleine Test-Dokumente:**

- `Brother_HL-L8360CDW_UM_ENG.pdf` (~50 Seiten)
- Schnelle Tests

**Große Test-Dokumente:**

- `HP_E877_CPMD.pdf` (1116 Seiten)
- Performance Tests
- Vollständige Pipeline-Tests

### 4. Assertions

```python
# Good
assert result.success, f"Expected success but got: {result.message}"
assert len(products) > 0, "No products found"

# Bad
assert result.success  # Keine Info bei Fehler
```

### 5. Test-Isolation

- Jeder Test muss unabhängig laufen
- Setup/Teardown für DB-Änderungen
- Keine Abhängigkeiten zwischen Tests

---

## 🚀 Deployment & Production

### 1. Environment Variables

**IMMER** `.env` Datei nutzen:
```bash
POSTGRES_URL=postgresql://...
PERPLEXITY_API_KEY=...
GOOGLE_API_KEY=...
OLLAMA_HOST=http://localhost:11434
```

### 2. Database Migrations

**Reihenfolge:**

1. `001_schema.sql` - Schemas und Tabellen
2. `002_views.sql` - Views erstellen
3. `003_indexes.sql` - Indexes und Performance

**Location:** `database/migrations_postgresql/`

### 3. Production Checklist

- [ ] Alle Environment Variables gesetzt
- [ ] PostgreSQL 15+ mit pgvector Extension
- [ ] Ollama mit Embedding Models
- [ ] MinIO/R2 für Object Storage
- [ ] Redis für Caching
- [ ] Backup Strategy aktiv

---

## 🔄 Error Handling & Retry Architecture (FUTURE WORK)

**⚠️ IMPORTANT: The features documented in this section are PLANNED but NOT YET IMPLEMENTED!**

**Current State:**
- `BaseProcessor.safe_process()` provides basic error handling and logging
- No automatic retry logic implemented
- No idempotency checks via completion markers
- No advisory lock management
- No correlation ID propagation
- No alert service integration

**Future Implementation Required:**

### Components to Build:

1. **ErrorClassifier** - Classify errors as transient/permanent
2. **RetryOrchestrator** - Hybrid retry scheduling (sync first, then async)
3. **IdempotencyChecker** - Check/set completion markers with data hashing
4. **AlertService** - Queue-based alert aggregation
5. **Advisory Lock Manager** - PostgreSQL lock wrapper

### Database Tables to Create:

- `krai_system.stage_completion_markers` - Idempotency tracking
- `krai_system.pipeline_errors` - Error tracking
- `krai_system.alert_queue` - Alert aggregation
- `krai_system.alert_configurations` - Alert rules
- `krai_system.retry_policies` - Retry configuration
- `krai_system.performance_baselines` - Performance tracking

### Current BaseProcessor Behavior:

**What `safe_process()` DOES:**
- ✅ Validates inputs via `validate_inputs()`
- ✅ Logs processing start/end
- ✅ Catches `ProcessingError` and generic exceptions
- ✅ Returns `ProcessingResult` with success/failure status
- ✅ Calculates processing time

**What `safe_process()` DOES NOT DO:**
- ❌ No automatic retry on transient errors
- ❌ No correlation ID generation
- ❌ No idempotency checks
- ❌ No advisory lock acquisition
- ❌ No alert queueing
- ❌ No error classification

### Implementation Guidelines (When Building):

**Rule 1: Use BaseProcessor.safe_process()**
- All processors should call `safe_process()` which wraps `process()`
- Processors implement `process()` with business logic
- Error handling is centralized in `safe_process()`

**Rule 2: Error Classification**
- Classify errors as transient (retry) or permanent (fail)
- Transient: HTTP 5xx, timeouts, connection errors
- Permanent: HTTP 4xx, validation errors, auth errors

**Rule 3: Hybrid Retry Approach**
- First retry: Synchronous with 1s delay
- Subsequent retries: Asynchronous background tasks with exponential backoff

**Rule 4: Idempotency Pattern**
- Check completion markers before processing
- Compute data hash to detect changes
- Cleanup old data if hash changed
- Set completion marker after success

**Rule 5: Advisory Locks**
- Use `pg_try_advisory_lock()` (non-blocking)
- Always release in finally block
- Lock ID from document_id + stage_name

**Rule 6: Correlation IDs**
- Format: `req_{uuid}.stage_{name}.retry_{n}`
- Include in all log entries
- Pass through entire pipeline

**Rule 7: Alert Service**
- Queue alerts, don't send directly
- Background worker aggregates by time window
- Threshold-based sending to reduce noise

### Anti-Patterns to Avoid:

1. ❌ Custom retry loops in processors
2. ❌ `time.sleep()` for retry delays
3. ❌ Processing without idempotency checks
4. ❌ Acquiring locks without try-finally
5. ❌ Sending emails/Slack directly
6. ❌ Hardcoded retry policies
7. ❌ Missing correlation IDs in logs
8. ❌ Catching generic exceptions without re-raising

### Reference Implementation Plan:

See `docs/IDE_RULES_ENHANCEMENT_T0.md` for detailed implementation specifications of:
- Error classification logic
- Retry orchestration
- Idempotency checking
- Advisory lock patterns
- Alert service architecture
- Performance measurement

**Status:** 📋 PLANNED - Not yet implemented
**Priority:** 🔍 MEDIUM - Important for production resilience
**Effort:** ~40-60 hours - Significant architectural work required

---

## 📚 Key Files Reference

**Core Architecture:**
- `backend/core/base_processor.py` - Base processor with safe_process()
- `backend/core/data_models.py` - ProcessingContext, ProcessingResult
- `backend/processors/exceptions.py` - ProcessingError class
- `backend/processors/logger.py` - ProcessorLogger implementation

**Database:**
- `DATABASE_SCHEMA.md` - Complete database schema documentation
- `database/migrations_postgresql/` - PostgreSQL migrations

**Configuration:**
- `.env` - Environment variables
- `backend/config/` - Application configuration

**Testing:**
- `tests/processors/` - Processor tests
- `tests/api/` - API tests
- `pytest.ini` - Test configuration

---

**Last Updated:** 2026-01-12 (15:03)
**Version:** 2.0 - Merged original rules with future error-handling architecture
