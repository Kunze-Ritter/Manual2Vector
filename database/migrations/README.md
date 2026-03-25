# KRAI Historical Migration Notes

Dieses Verzeichnis enthaelt im aktuellen Repo keine ausfuehrbaren SQL-Migrationen.

## Aktiver Pfad

Der aktive SQL-Migrationssatz liegt unter `../migrations_postgresql/`.

- Aktueller Repo-Stand: Dateien von `001` bis `029`
- Basis-Bootstrap: `001_core_schema.sql`, `002_views.sql`, `003_functions.sql`
- Spaetere Dateien sind additive Feature-/Fix-Migrationen

## Wichtiger Hinweis

Es gibt im aktuellen Repo kein `archive/`-Unterverzeichnis unter `database/migrations/`.
Aeltere alternative Migrationskonzepte existieren nur noch als historische Dokumentation
oder in alten Branches, nicht als aktiver Deploy-Pfad.

## Weitere Doku

- `../README.md`
- `../migrations_postgresql/README.md`
- `../../DATABASE_SCHEMA.md`
