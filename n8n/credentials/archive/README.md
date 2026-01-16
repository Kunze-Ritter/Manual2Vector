# Archived Supabase Credentials

Diese Credential-Dateien sind **deprecated** und funktionieren nicht mit der aktuellen Architektur.

## Archivierte Dateien

- `supabase-auth.json` - HTTP Header Auth für Supabase API
- `supabase-modern.json` - Supabase API Credentials
- `supabase-langchain.json` - LangChain Supabase Integration

## Aktuelle Credentials

Für die aktuelle PostgreSQL-only Architektur:

### PostgreSQL Connection
```json
{
  "host": "localhost",
  "port": 5432,
  "database": "krai",
  "user": "postgres",
  "password": "your_password",
  "ssl": false
}
```

### FastAPI JWT Token
```bash
# Token abrufen
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Token verwenden
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/documents
```

Siehe: `docs/api/AUTHENTICATION.md`
