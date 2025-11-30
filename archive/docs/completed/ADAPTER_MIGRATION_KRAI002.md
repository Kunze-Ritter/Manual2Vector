# Database Adapter Migration Guide

## Übersicht

Die KRAI-Backend-API wurde von direkten Supabase-Client-Abhängigkeiten auf das Database Adapter Pattern migriert. Dies ermöglicht die Nutzung verschiedener Datenbank-Backends (Supabase, PostgreSQL) ohne Code-Änderungen.

## Architektur

### Komponenten

1. **DatabaseAdapter (Interface)**: Abstrakte Basisklasse mit allen Datenbank-Operationen
2. **PostgreSQLAdapter**: Implementierung für direktes PostgreSQL
3. **SupabaseAdapter**: Implementierung für Supabase (PostgREST + optional direktes PostgreSQL)
4. **database_factory**: Factory-Funktion zur Adapter-Erstellung basierend auf Umgebungsvariablen

### Adapter-Auswahl

Die Adapter-Auswahl erfolgt über die Umgebungsvariable `DATABASE_TYPE`:

```bash
# PostgreSQL (lokal oder remote)
DATABASE_TYPE=postgresql

# Supabase
DATABASE_TYPE=supabase
```

## Migration von Supabase-Client zu Adapter

### Vorher (Direkter Supabase-Client)

```python
from supabase import create_client

supabase = create_client(url, key)
result = supabase.table('vw_documents').select('*').eq('id', doc_id).execute()
```

### Nachher (Database Adapter)

```python
from services.database_factory import create_database_adapter

adapter = create_database_adapter()
doc = await adapter.get_document(doc_id)
```

### Query-Migration

#### PostgREST zu SQL

**Vorher:**
```python
result = supabase.table('vw_error_codes') \
    .select('error_code, error_description') \
    .ilike('error_code', f'%{code}%') \
    .order('confidence_score', desc=True) \
    .limit(10) \
    .execute()
```

**Nachher:**
```python
query = """
    SELECT error_code, error_description 
    FROM krai.error_codes 
    WHERE error_code ILIKE %s 
    ORDER BY confidence_score DESC 
    LIMIT 10
"""
result = await adapter.execute_query(query, [f'%{code}%'])
```

#### RPC-Calls

**Vorher:**
```python
result = supabase.rpc('match_documents', {
    'query_embedding': embedding,
    'match_count': 10
}).execute()
```

**Nachher:**
```python
# Prüfe RPC-Unterstützung
if hasattr(adapter, 'rpc'):
    result = await adapter.rpc('match_documents', {
        'query_embedding': embedding,
        'match_count': 10
    })
else:
    # Fallback zu direkter Methode
    result = await adapter.search_embeddings(
        query_embedding=embedding,
        limit=10
    )
```

## Bekannte Einschränkungen

### StageTracker (Supabase RPC)

Der `StageTracker` nutzt Supabase RPC-Funktionen für Stage-Management:
- `start_stage()` 
- `complete_stage()` 
- `fail_stage()` 
- `update_stage_progress()` 

**Workaround:**
```python
# Hole Legacy-Supabase-Client für StageTracker
legacy_client = get_legacy_supabase_client()
if legacy_client:
    tracker = StageTracker(legacy_client)
else:
    # Stage-Tracking nicht verfügbar mit PostgreSQL-Adapter
    tracker = None
```

**Langfristige Lösung:**
- Migriere RPC-Funktionen zu PostgreSQL Stored Procedures
- Implementiere `rpc()`-Methode in PostgreSQLAdapter
- Oder: Ersetze Stage-Tracking durch direkte Datenbank-Updates

## Testing

### Mit PostgreSQL

```bash
export DATABASE_TYPE=postgresql
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=krai
export POSTGRES_USER=krai_user
export POSTGRES_PASSWORD=krai_password

python -m pytest tests/
```

### Mit Supabase

```bash
export DATABASE_TYPE=supabase
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_ANON_KEY=your-anon-key
export SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

python -m pytest tests/
```

## Best Practices

1. **Nutze Adapter-Methoden**: Bevorzuge `adapter.get_document()` statt roher SQL-Queries
2. **Schema-Präfix**: Nutze `krai.` Präfix für PostgreSQL-Tabellen
3. **Async/Await**: Alle Adapter-Methoden sind async
4. **Error Handling**: Fange Adapter-spezifische Fehler ab
5. **Logging**: Logge Adapter-Typ bei Initialisierung

## Troubleshooting

### "execute_query not implemented"

**Problem:** Adapter unterstützt keine rohen SQL-Queries

**Lösung:** Nutze Adapter-Methoden oder aktiviere direkte PostgreSQL-Verbindung:
```bash
export DATABASE_CONNECTION_URL=postgresql://user:pass@host:5432/db
```

### "RPC not supported"

**Problem:** PostgreSQL-Adapter unterstützt keine RPC-Calls

**Lösung:** 
- Implementiere Stored Procedures in PostgreSQL
- Oder: Nutze alternative Adapter-Methoden

### "Schema not found"

**Problem:** Schema-Präfix fehlt in SQL-Query

**Lösung:** Füge `krai.` Präfix hinzu:
```python
# Falsch
query = "SELECT * FROM documents"

# Richtig
query = "SELECT * FROM krai.documents"
```

## Weitere Informationen

- [Database Adapter Interface](../backend/services/database_adapter.py)
- [PostgreSQL Adapter](../backend/services/postgresql_adapter.py)
- [Supabase Adapter](../backend/services/supabase_adapter.py)
- [Database Factory](../backend/services/database_factory.py)
