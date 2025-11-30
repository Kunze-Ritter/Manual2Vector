# Script Migration Status (Supabase → Database Factory)

This file tracks the migration of standalone scripts away from direct Supabase
clients towards the shared `DatabaseAdapter` and async PostgreSQL access.

## Phase 1 – Helpers & Infrastructure

- [x] `scripts/_env.py` – zentraler Env-Loader für alle Scripts
- [x] `scripts/migration_helpers.py` – Adapter/Async-Helper
- [x] `scripts/test_migration_helpers.py` – einfacher Verbindungs-Smoketest

## Phase 2 – Kritische Maintenance-Scripts

Ziel: Nur noch über den Adapter, keine direkten `supabase.create_client` Aufrufe.

- [x] `scripts/cleanup_database.py`
  - Status: DONE – nutzt jetzt `create_connected_adapter(database_type="postgresql")`
    und löscht Daten über direkte SQL-Statements gegen dokumentierte `krai_*` Tabellen.

- [x] `scripts/delete_document_data.py`
  - Status: DONE – löscht Dokumente über `krai_core.documents` (CASCADE) mit
    Adapter-Methoden (`get_document`) und direktem SQL, inkl. optionalem Dry-Run.

## Phase 3 – Diagnose- / Check-Scripts

- [x] `scripts/check_error_code.py`
  - Status: DONE – nutzt jetzt `create_connected_adapter(database_type="postgresql")`
    und read-only Abfragen über `public.vw_error_codes`/`public.vw_images` via
    `pg_fetch_all`, ohne direkten Supabase-Client.

- [x] `scripts/list_documents.py`
  - Status: DONE – nutzt `public.vw_documents` via Adapter; Zählqueries laufen
    direkt gegen `public.vw_error_codes`, `krai_intelligence.chunks` und
    `krai_core.document_products` (nur dokumentierte Tabellen/Spalten).

- [x] `scripts/check_manufacturers.py`
  - Status: DONE – Hersteller-Listing via Adapter (`public.vw_manufacturers`),
    inklusive Lexmark-Check, ohne Supabase-Client.

- [x] `scripts/enrich_video_metadata.py` (DB-Anteile)
  - Status: DONE – Alle Supabase-Aufrufe auf async PostgreSQL-Adapter migriert.
    Video-Insert/Dedupe via direktes SQL INSERT ON CONFLICT, Link-Updates via
    UPDATE-Statements, Hersteller-/Dokument-Lookups via `pg_fetch_all` gegen
    `public.vw_manufacturers`/`public.vw_documents`. HTTP/Video-API-Logik
    unverändert. Nutzt `krai_content.videos`, `krai_content.links` aus
    aktualisierter `DATABASE_SCHEMA.md`.

## Hinweise

- Scripts mit direktem SQL-Zugriff dürfen **nur** dokumentierte Tabellen und
  Spalten aus `DATABASE_SCHEMA.md` verwenden.
- Für komplexe Cross-Schema-Queries sollte `PostgreSQLAdapter` mit
  `execute_query`/`fetch_all` verwendet werden.
- Transitional ist `DATABASE_TYPE=postgresql` für alle Maintenance-Scripts
  empfohlen; Supabase bleibt über den Adapter weiter nutzbar, wo sinnvoll.
