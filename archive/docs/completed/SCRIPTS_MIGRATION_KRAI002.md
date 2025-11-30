# Script Migration Guide: Supabase → Database Factory

Dieses Dokument beschreibt, wie Standalone-Scripts von direkten Supabase-
Aufrufen auf den gemeinsamen `DatabaseAdapter` umgestellt werden.

## Ziele

- Einheitliche Env-Initialisierung über `scripts/_env.load_env`.
- Kein `from supabase import create_client` mehr in Scripts.
- Gemeinsamer Zugang über `create_database_adapter()` und Async-API.
- Für Maintenance/Backfill-Scripts bevorzugt `DATABASE_TYPE=postgresql`.

## Zentrale Bausteine

- `scripts/_env.py`
  - Lädt alle relevanten `.env*` Dateien aus dem Projekt-Root
  - Optional: zusätzliche Dateien wie `.env.database` via `extra_files`.

- `scripts/migration_helpers.py`
  - `create_connected_adapter(database_type=None) -> DatabaseAdapter`
    - Lädt Env, erzeugt den Adapter über die Factory und ruft `connect()` auf.
  - `run_async(coro)`
    - Kleiner Helper, um Async-Einstiegspunkte in Scripts zu nutzen.
  - `pg_fetch_all(adapter, query, params=None)` / `pg_execute(...)`
    - Convenience für direkte PostgreSQL-Queries (nur wenn Adapter
      tatsächlich ein `PostgreSQLAdapter` ist).

## Typisches Migrationsmuster (konzeptionell)

Alt (vereinfacht):

- Direktes Laden von `.env.database` via `dotenv.load_dotenv`.
- Erzeugen eines Supabase-Clients mit `create_client(SUPABASE_URL, KEY)`.
- Direkte Nutzung von Views wie `vw_documents`, `vw_error_codes` etc.

Neu (konzeptionell):

1. Env nur noch über `load_env` / `create_connected_adapter` laden.
2. Adapter erstellen:
   - `adapter = await create_connected_adapter()`
   - Typ wird über `DATABASE_TYPE` gesteuert (`supabase` oder `postgresql`).
3. Für einfache Read-Only-Abfragen (Views):
   - Bei `SupabaseAdapter`: vorhandene Methoden im Adapter nutzen.
   - Bei `PostgreSQLAdapter`: SQL gegen dokumentierte `krai_*`-Tabellen umsetzen.
4. Für Maintenance-Scripts (DELETE/UPDATE):
   - Immer PostgreSQL (direktes SQL) nutzen, basierend auf
     `DATABASE_SCHEMA.md`.

## Sicherheit & Governance

- **Keine** SQL-Statements gegen nicht dokumentierte Tabellen/Spalten.
- Lösch-Scripts (z.B. `cleanup_database.py`) nur mit klarer Bestätigung &
  möglichst kleinem Scope verwenden.
- Fortschritt der Migration wird in `scripts/MIGRATION_STATUS.md` festgehalten.
- Zu jedem Migration-Schritt sollte ein Eintrag in `TODO.md` ergänzt werden
  (Task, Files, Result, Timestamp).
