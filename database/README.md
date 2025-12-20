# KRAI PostgreSQL Database Setup

**Version:** 1.0 (PostgreSQL-only)  
**Last Updated:** 2025-12-20  
**Database:** PostgreSQL 15+ with pgvector extension

---

## 📋 Overview

KRAI Engine verwendet eine **PostgreSQL-Datenbank** mit der **pgvector-Extension** für semantische Suche und Embeddings. Die Datenbank ist in mehrere Schemas organisiert für bessere Wartbarkeit und Sicherheit.

## 🏗️ Database Architecture

### Schemas

- **`krai_core`** - Kern-Entitäten: Hersteller, Produkte, Dokumente
- **`krai_intelligence`** - KI/ML: Chunks, Embeddings, Error Codes
- **`krai_content`** - Medien: Bilder, Videos, Links
- **`krai_system`** - System: Audit, Queue, Metrics
- **`krai_parts`** - Ersatzteile-Katalog
- **`krai_users`** - Benutzerverwaltung
- **`krai_analytics`** - Analytics und Search Tracking

### Public Views

Alle Tabellen sind über `public.vw_*` Views zugänglich:
- `vw_documents`, `vw_chunks`, `vw_embeddings`, `vw_images`, etc.

**Wichtig:** `vw_embeddings` ist ein **Alias** für `vw_chunks` - Embeddings sind als Spalte `embedding` in `krai_intelligence.chunks` gespeichert!

---

## 🚀 Quick Start

### 1. Voraussetzungen

- Docker & Docker Compose
- PostgreSQL 15+ Container mit pgvector
- Mindestens 2GB RAM für PostgreSQL

### 2. Datenbank initialisieren

```bash
# Im KRAI-minimal Root-Verzeichnis

# 1. PostgreSQL Container starten (via docker-compose)
docker-compose up -d krai-postgres-prod

# 2. Migrationen anwenden (in Reihenfolge!)
docker exec -i krai-postgres-prod psql -U postgres -d krai_db < database/migrations_postgresql/001_core_schema.sql
docker exec -i krai-postgres-prod psql -U postgres -d krai_db < database/migrations_postgresql/002_views.sql
docker exec -i krai-postgres-prod psql -U postgres -d krai_db < database/migrations_postgresql/003_functions.sql
```

### 3. Verifizierung

```bash
# Verbindung zur Datenbank
docker exec -it krai-postgres-prod psql -U postgres -d krai_db

# Schemas prüfen
\dn krai_*

# Tabellen prüfen
\dt krai_core.*

# Views prüfen
\dv public.vw_*

# Extensions prüfen
\dx

# Migrationen prüfen
SELECT * FROM krai_system.migrations ORDER BY applied_at;
```

Erwartete Ausgabe:
- **7 Schemas** (krai_core, krai_intelligence, krai_content, krai_system, krai_parts, krai_users, krai_analytics)
- **~25 Tabellen** über alle Schemas
- **~16 Public Views** (vw_documents, vw_chunks, vw_embeddings, etc.)
- **5 Extensions** (uuid-ossp, vector, pg_trgm, unaccent, pg_stat_statements)

---

## 📁 Migration Files

### Konsolidierte Migrationen (PostgreSQL-only)

Alle Migrationen sind im Verzeichnis `database/migrations_postgresql/`:

1. **`001_core_schema.sql`** - Schemas, Tabellen, Extensions, Indexes
2. **`002_views.sql`** - Alle public vw_* Views
3. **`003_functions.sql`** - RPC Functions, Triggers, Stage Tracking

### Alte Migrationen (Archiv)

Die alten 130+ Migrationen (inkl. Supabase-spezifische) wurden nach `database/migrations/archive/` verschoben. Sie sind **nicht mehr notwendig** für neue Installationen.

---

## 🔧 Wichtige Konzepte

### Embeddings Storage

**Embeddings sind IN `krai_intelligence.chunks` gespeichert!**

- Spalte: `embedding` (Typ: `vector(768)`)
- Es gibt **KEIN** separates `krai_embeddings` Schema
- `vw_embeddings` ist nur ein Alias für `vw_chunks`

```sql
-- Embeddings abfragen
SELECT id, chunk_text, embedding 
FROM krai_intelligence.chunks 
WHERE embedding IS NOT NULL 
LIMIT 10;

-- Oder via View
SELECT id, chunk_text, embedding 
FROM public.vw_embeddings 
LIMIT 10;
```

### Stage Tracking

Dokumente haben ein `stage_status` JSONB-Feld für Pipeline-Tracking:

```sql
-- Stage-Status prüfen
SELECT id, filename, stage_status->'embedding'->>'status' as embedding_status
FROM krai_core.documents;
```

RPC Functions für Stage Tracking:
- `krai_core.start_stage(document_id, stage_name)`
- `krai_core.update_stage_progress(document_id, stage_name, progress, metadata)`
- `krai_core.complete_stage(document_id, stage_name, metadata)`
- `krai_core.fail_stage(document_id, stage_name, error, metadata)`

### Vector Search

Semantische Suche via pgvector:

```sql
-- Chunks suchen
SELECT * FROM krai_intelligence.match_chunks(
    query_embedding := '[0.1, 0.2, ...]'::vector(768),
    match_threshold := 0.7,
    match_count := 10
);

-- Multimodale Suche (Chunks, Images, Videos, Links, Tables)
SELECT * FROM krai_intelligence.match_multimodal(
    query_embedding := '[0.1, 0.2, ...]'::vector(768),
    match_threshold := 0.6,
    match_count := 20
);
```

---

## 🔒 Sicherheit & Permissions

### Benutzer

Die Datenbank nutzt folgende Benutzer:
- **`postgres`** - Superuser (nur für Migrationen)
- **`krai_user`** - Application User (Runtime)

### Permissions

Alle `krai_*` Schemas und `public.vw_*` Views haben Permissions für `PUBLIC` (oder `krai_user` je nach Setup).

---

## 📊 Performance

### Indexes

Die Datenbank nutzt optimierte Indexes:
- **HNSW Indexes** für Vector Similarity Search (pgvector)
- **GIN Indexes** für Full-Text Search
- **B-Tree Indexes** für Foreign Keys und häufige Queries

### Monitoring

```sql
-- Embedding Coverage prüfen
SELECT * FROM krai_intelligence.get_embedding_stats();

-- Index Usage prüfen
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE schemaname LIKE 'krai_%'
ORDER BY idx_scan DESC;

-- Cache Hit Ratio
SELECT 
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;
```

---

## 🛠️ Wartung

### Vacuum & Analyze

```sql
-- Regelmäßig ausführen für Performance
VACUUM ANALYZE krai_intelligence.chunks;
VACUUM ANALYZE krai_content.images;
```

### Backup

```bash
# Backup erstellen
docker exec krai-postgres-prod pg_dump -U postgres -d krai_db -F c -f /tmp/krai_backup.dump

# Backup kopieren
docker cp krai-postgres-prod:/tmp/krai_backup.dump ./backups/

# Restore
docker exec -i krai-postgres-prod pg_restore -U postgres -d krai_db -c /tmp/krai_backup.dump
```

---

## 🐛 Troubleshooting

### Problem: "relation vw_chunks does not exist"

**Lösung:** Migration 002_views.sql anwenden

```bash
docker exec -i krai-postgres-prod psql -U postgres -d krai_db < database/migrations_postgresql/002_views.sql
```

### Problem: "function krai_core.start_stage does not exist"

**Lösung:** Migration 003_functions.sql anwenden

```bash
docker exec -i krai-postgres-prod psql -U postgres -d krai_db < database/migrations_postgresql/003_functions.sql
```

### Problem: "extension vector does not exist"

**Lösung:** pgvector Extension installieren

```bash
docker exec -it krai-postgres-prod psql -U postgres -d krai_db -c "CREATE EXTENSION vector;"
```

### Problem: Langsame Vector Search

**Lösung:** HNSW Index neu erstellen mit höheren Parametern

```sql
DROP INDEX IF EXISTS idx_chunks_embedding;
CREATE INDEX idx_chunks_embedding ON krai_intelligence.chunks 
    USING hnsw (embedding vector_cosine_ops) 
    WITH (m = 32, ef_construction = 128);
```

---

## 📚 Weitere Dokumentation

- **`DATABASE_SCHEMA.md`** - Vollständige Schema-Dokumentation (auto-generiert)
- **`migrations_postgresql/`** - Konsolidierte PostgreSQL Migrationen
- **`migrations/archive/`** - Alte Migrationen (nur für Referenz)

---

## ✅ Checkliste für neue Installation

- [ ] PostgreSQL Container läuft
- [ ] pgvector Extension verfügbar
- [ ] Migration 001_core_schema.sql angewendet
- [ ] Migration 002_views.sql angewendet
- [ ] Migration 003_functions.sql angewendet
- [ ] Alle Schemas existieren (`\dn krai_*`)
- [ ] Alle Views existieren (`\dv public.vw_*`)
- [ ] Embedding Stats funktionieren (`SELECT * FROM krai_intelligence.get_embedding_stats();`)

---

**Bei Fragen oder Problemen:** Siehe `TODO.md` oder kontaktiere das Dev-Team.
