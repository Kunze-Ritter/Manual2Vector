# KRAI PostgreSQL Migrations

**Version:** 1.0 (PostgreSQL-only, consolidated)  
**Created:** 2025-12-20  
**Status:** ✅ Production Ready

## ⚠️ WICHTIGER HINWEIS

**Diese Migrationen sind NUR für NEUE/FRISCHE Installationen gedacht!**

Falls deine Datenbank bereits läuft und die Pipeline ohne Fehler funktioniert:
- ❌ **NICHT** diese Migrationen ausführen!
- ✅ **Behalte** deine bestehende Datenbank-Struktur
- ✅ **Nutze** die alten Migrationen in `database/migrations/` für Updates

Diese konsolidierten Migrationen sind für:
- ✅ Neue Installationen (frische PostgreSQL Datenbank)
- ✅ Zukünftige Deployments
- ✅ Dokumentation und Referenz

---

## 📋 Migration Files

Diese 4 konsolidierten Migrationen ersetzen die alten 130+ fragmentierten Migrationen:

### 1. `001_core_schema.sql`
**Erstellt:**
- Extensions (uuid-ossp, vector, pg_trgm, unaccent, pg_stat_statements)
- 7 Schemas (krai_core, krai_intelligence, krai_content, krai_system, krai_parts, krai_users, krai_analytics)
- ~25 Tabellen mit Foreign Keys
- Performance Indexes (B-Tree, HNSW, GIN)
- Migration Tracking Table

**Dauer:** ~30 Sekunden

### 2. `002_views.sql`
**Erstellt:**
- 16 Public Views (vw_documents, vw_chunks, vw_embeddings, etc.)
- Permissions für PUBLIC
- **Wichtig:** vw_embeddings ist ALIAS für vw_chunks!

**Dauer:** ~5 Sekunden

### 3. `003_functions.sql`
**Erstellt:**
- Stage Tracking Functions (start_stage, complete_stage, etc.)
- Vector Search Functions (match_chunks, match_multimodal, etc.)
- Utility Functions (get_embedding_stats, etc.)
- Updated_at Triggers

**Dauer:** ~10 Sekunden

### 4. `004_stage_tracking.sql`
**Erstellt:**
- Tabelle `krai_system.stage_tracking` inklusive `stage_number`
- Unique Constraint auf `(document_id, stage_number)`
- Indizes auf `document_id` und `status`
- Migration Tracking Eintrag in `krai_system.migrations`

**Dauer:** ~5 Sekunden

### 5. `009_add_stage_metrics_table.sql` (optional)
**Erstellt:**
- Tabelle `krai_system.stage_metrics` für Echtzeit-Metriken pro Dokument/Stage
- Indizes auf document_id, stage_name, created_at

**Anwenden (wenn gewünscht):**
```bash
# Mit Python (POSTGRES_URL aus .env muss gesetzt sein)
python scripts/apply_migration_009_stage_metrics.py
```
Oder mit psql:
```bash
psql "$POSTGRES_URL" -f database/migrations_postgresql/009_add_stage_metrics_table.sql
```

### 6. `017_video_enrichment_columns.sql` (optional)
**Erstellt:**
- `krai_content.videos.tags` (`text[]`)
- `krai_content.videos.enrichment_error` (`text`)
- Index `idx_videos_needs_enrichment` für `metadata->>'needs_enrichment'`

**Anwenden (wenn Brightcove Stage 16 genutzt wird):**
```bash
psql "$POSTGRES_URL" -f database/migrations_postgresql/017_video_enrichment_columns.sql
```

---

## 🚀 Installation

### Voraussetzungen
- PostgreSQL 15+
- Docker & Docker Compose
- Laufender PostgreSQL Container

### Quick Start

```bash
# Im KRAI-minimal Root-Verzeichnis

# 1. Container starten
docker-compose up -d krai-postgres-prod

# 2. Migrationen anwenden (in Reihenfolge!)
docker exec -i krai-postgres-prod psql -U postgres -d krai_db < database/migrations_postgresql/001_core_schema.sql
docker exec -i krai-postgres-prod psql -U postgres -d krai_db < database/migrations_postgresql/002_views.sql
docker exec -i krai-postgres-prod psql -U postgres -d krai_db < database/migrations_postgresql/003_functions.sql
docker exec -i krai-postgres-prod psql -U postgres -d krai_db < database/migrations_postgresql/004_stage_tracking.sql

# 3. Verifizierung
docker exec -it krai-postgres-prod psql -U postgres -d krai_db -c "SELECT * FROM krai_system.migrations;"
```

**Erwartete Ausgabe:**
```
 migration_name  |         applied_at         |                    description                    
-----------------+----------------------------+---------------------------------------------------
 001_core_schema | 2025-12-20 17:00:00+00     | PostgreSQL core schema setup - extensions, ...
 002_views       | 2025-12-20 17:00:05+00     | PostgreSQL public views - all vw_ views ...
 003_functions   | 2025-12-20 17:00:10+00     | PostgreSQL functions and triggers - stage ...
```

---

## ✅ Verifizierung

Nach erfolgreicher Migration:

```sql
-- Schemas prüfen (sollte 7 sein)
SELECT nspname FROM pg_namespace WHERE nspname LIKE 'krai_%' ORDER BY nspname;

-- Tabellen zählen (sollte ~25 sein)
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema LIKE 'krai_%';

-- Views prüfen (sollte 16 sein)
SELECT viewname FROM pg_views WHERE schemaname = 'public' AND viewname LIKE 'vw_%' ORDER BY viewname;

-- Extensions prüfen
\dx

-- Embedding Stats
SELECT * FROM krai_intelligence.get_embedding_stats();
```

---

## 🔄 Migration von alter Installation

Falls du die alten Migrationen bereits angewendet hast:

### Option 1: Kompletter Reset (empfohlen)

```bash
# 1. Backup erstellen
docker exec krai-postgres-prod pg_dump -U postgres -d krai_db -F c -f /tmp/backup.dump

# 2. Alle krai_* Schemas löschen
docker exec -it krai-postgres-prod psql -U postgres -d krai_db << 'EOF'
DROP SCHEMA IF EXISTS krai_core CASCADE;
DROP SCHEMA IF EXISTS krai_intelligence CASCADE;
DROP SCHEMA IF EXISTS krai_content CASCADE;
DROP SCHEMA IF EXISTS krai_system CASCADE;
DROP SCHEMA IF EXISTS krai_parts CASCADE;
DROP SCHEMA IF EXISTS krai_users CASCADE;
DROP SCHEMA IF EXISTS krai_analytics CASCADE;
EOF

# 3. Neue Migrationen anwenden
docker exec -i krai-postgres-prod psql -U postgres -d krai_db < database/migrations_postgresql/001_core_schema.sql
docker exec -i krai-postgres-prod psql -U postgres -d krai_db < database/migrations_postgresql/002_views.sql
docker exec -i krai-postgres-prod psql -U postgres -d krai_db < database/migrations_postgresql/003_functions.sql
```

### Option 2: Inkrementell (nur fehlende Teile)

Falls du nur bestimmte Migrationen nachholen möchtest:

```bash
# Nur Views aktualisieren
docker exec -i krai-postgres-prod psql -U postgres -d krai_db < database/migrations_postgresql/002_views.sql

# Nur Functions aktualisieren
docker exec -i krai-postgres-prod psql -U postgres -d krai_db < database/migrations_postgresql/003_functions.sql
```

---

## 📚 Weitere Dokumentation

- **`database/README.md`** - Vollständige PostgreSQL Setup-Anleitung
- **`DATABASE_SCHEMA.md`** - Detaillierte Schema-Dokumentation
- **`database/migrations/archive/`** - Alte Migrationen (nur Referenz)

---

## 🐛 Troubleshooting

### Problem: "relation already exists"

**Ursache:** Migration wurde bereits teilweise angewendet

**Lösung:** Entweder kompletter Reset (Option 1) oder einzelne CREATE-Statements überspringen

### Problem: "extension vector does not exist"

**Ursache:** pgvector Extension nicht installiert

**Lösung:**
```bash
docker exec -it krai-postgres-prod psql -U postgres -d krai_db -c "CREATE EXTENSION vector;"
```

### Problem: "permission denied for schema krai_core"

**Ursache:** Fehlende Berechtigungen

**Lösung:**
```sql
GRANT ALL ON SCHEMA krai_core TO krai_user;
GRANT ALL ON ALL TABLES IN SCHEMA krai_core TO krai_user;
```

---

## ✨ Vorteile der Konsolidierung

### Vorher (130+ Dateien)
- ❌ Fragmentiert und schwer zu überblicken
- ❌ Supabase-spezifische Annahmen
- ❌ Inkonsistente Reihenfolge
- ❌ Hohe Fehlerrate bei partieller Ausführung
- ❌ Schwierige Wartung

### Nachher (3 Dateien)
- ✅ Klar strukturiert und wartbar
- ✅ PostgreSQL-only (keine Supabase-Abhängigkeiten)
- ✅ Logische Gruppierung
- ✅ Atomic Execution
- ✅ Einfache Wartung und Updates

---

**Bei Fragen:** Siehe `database/README.md` oder `TODO.md`
