# Database Adapter Pattern

## Overview

The KR-AI-Engine uses a database adapter pattern to support multiple database backends with minimal code changes. This allows you to switch between Supabase Cloud, local PostgreSQL, or Docker PostgreSQL without modifying application code.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Code                          │
│              (main.py, pipeline, processors)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Database Factory                             │
│            (database_factory.py)                             │
│  create_database_adapter(database_type, ...)                │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Supabase   │  │ PostgreSQL  │  │   Docker    │
│   Adapter   │  │   Adapter   │  │  PostgreSQL │
│             │  │             │  │   Adapter   │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│              DatabaseAdapter (Abstract Base)                 │
│  - connect()                                                 │
│  - create_document()                                         │
│  - create_chunk()                                            │
│  - search_embeddings()                                       │
│  - ... (all database operations)                             │
└─────────────────────────────────────────────────────────────┘
```

## Supported Adapters

### 1. Supabase Adapter (Default)

**Use Case:** Production deployment with Supabase Cloud

**Features:**
- PostgREST API for standard operations
- Direct asyncpg pool for cross-schema queries
- Service role key support for elevated permissions
- Automatic fallback between asyncpg and PostgREST

**Configuration:**
```bash
DATABASE_TYPE=supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key  # Optional
DATABASE_CONNECTION_URL=postgresql://...  # Optional, for asyncpg
```

**Pros:**
- ✅ Fully managed (no server maintenance)
- ✅ Built-in authentication & authorization
- ✅ Real-time subscriptions
- ✅ Automatic backups
- ✅ Global CDN

**Cons:**
- ❌ Requires internet connection
- ❌ Costs scale with usage
- ❌ PostgREST limitations (no JOINs across schemas)

### 2. PostgreSQL Adapter

**Use Case:** Self-hosted PostgreSQL database

**Features:**
- Pure asyncpg implementation
- Direct SQL queries (no PostgREST)
- Full control over database
- Schema prefix support (e.g., `krai_core`, `krai_content`)

**Configuration:**
```bash
DATABASE_TYPE=postgresql

# Option 1: Connection URL
POSTGRES_URL=postgresql://user:password@localhost:5432/krai

# Option 2: Individual parameters
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=krai
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Schema prefix (default: krai)
DATABASE_SCHEMA_PREFIX=krai
```

**Pros:**
- ✅ Full control over database
- ✅ No external dependencies
- ✅ Works offline
- ✅ No usage-based costs

**Cons:**
- ❌ Requires database setup & maintenance
- ❌ No built-in authentication
- ❌ Manual backups required

### 3. Docker PostgreSQL Adapter

**Use Case:** Local development with Docker Compose

**Features:**
- Extends PostgreSQL Adapter
- Docker-specific defaults (service name: `krai-postgres`)
- Automatic schema creation
- Pre-configured for docker-compose.simple.yml, docker-compose.with-firecrawl.yml, and docker-compose.production.yml

**Configuration:**
```bash
DATABASE_TYPE=docker_postgresql

# Docker defaults (can be overridden)
POSTGRES_HOST=krai-postgres  # Docker service name
POSTGRES_PORT=5432
POSTGRES_DB=krai
POSTGRES_USER=krai_user
POSTGRES_PASSWORD=krai_password
DATABASE_SCHEMA_PREFIX=krai
```

**Pros:**
- ✅ Easy local development
- ✅ Consistent environment
- ✅ Quick setup with docker-compose
- ✅ Isolated from host system

**Cons:**
- ❌ Requires Docker
- ❌ Not for production use
- ❌ Data lost when container removed (unless volumes configured)

## Usage

### Using the Factory (Recommended)

```python
from backend.services.database_factory import create_database_adapter

# Create adapter based on environment variables
adapter = create_database_adapter()

# Or specify explicitly
adapter = create_database_adapter(
    database_type="supabase",
    supabase_url="https://your-project.supabase.co",
    supabase_key="your_anon_key"
)

# Connect and use
await adapter.connect()
document_id = await adapter.create_document(document)
```

### Backward Compatibility

Existing code using `DatabaseService` continues to work without changes:

```python
from backend.services.database_service_production import DatabaseService

# Old code still works - delegates to SupabaseAdapter
db = DatabaseService(
    supabase_url="...",
    supabase_key="..."
)
await db.connect()
```

## Implementation Status

### ✅ Implemented

- `DatabaseAdapter` - Abstract base class
- `SupabaseAdapter` - Full implementation (PostgREST + asyncpg)
- `PostgreSQLAdapter` - Partial implementation (basic operations)
- `DockerPostgreSQLAdapter` - Extends PostgreSQL adapter
- `database_factory` - Factory pattern for adapter creation
- Backward compatibility wrappers

### 🚧 TODO

- Complete PostgreSQL adapter implementation
- Add connection pooling configuration
- Add retry logic for transient failures
- Add metrics and monitoring
- Add migration tools for switching adapters

## Migration Guide

### From DatabaseService to Adapter Pattern

**Before:**
```python
from backend.services.database_service_production import DatabaseService

db = DatabaseService(supabase_url, supabase_key)
await db.connect()
```

**After (Recommended):**
```python
from backend.services.database_factory import create_database_adapter

db = create_database_adapter()  # Reads from environment
await db.connect()
```

**After (Backward Compatible):**
```python
# No changes needed - existing code continues to work
from backend.services.database_service_production import DatabaseService

db = DatabaseService(supabase_url, supabase_key)
await db.connect()
```

### Switching Adapters

Change the `DATABASE_TYPE` environment variable:

```bash
# Use Supabase (default)
DATABASE_TYPE=supabase

# Use local PostgreSQL
DATABASE_TYPE=postgresql

# Use Docker PostgreSQL
DATABASE_TYPE=docker_postgresql
```

No code changes required!

## Best Practices

### 1. Use the Factory

Always use `create_database_adapter()` for new code:

```python
from backend.services.database_factory import create_database_adapter

adapter = create_database_adapter()
```

### 2. Don't Hardcode Adapter Types

Let the factory decide based on environment:

```python
# ❌ Bad
from backend.services.supabase_adapter import SupabaseAdapter
adapter = SupabaseAdapter(...)

# ✅ Good
from backend.services.database_factory import create_database_adapter
adapter = create_database_adapter()
```

### 3. Handle Adapter-Specific Features

Some features are adapter-specific:

```python
# Check if adapter supports a feature
if hasattr(adapter, 'client'):
    # Supabase-specific: access PostgREST client
    result = adapter.client.table('...').select('*').execute()

if hasattr(adapter, 'pg_pool'):
    # PostgreSQL-specific: direct SQL
    async with adapter.pg_pool.acquire() as conn:
        result = await conn.fetch('SELECT ...')
```

### 4. Test with Multiple Adapters

Test your code with different adapters:

```python
import pytest
from backend.services.database_factory import create_database_adapter

@pytest.mark.parametrize("db_type", ["supabase", "postgresql"])
async def test_create_document(db_type):
    adapter = create_database_adapter(database_type=db_type)
    await adapter.connect()
    # ... test code
```

## Troubleshooting

### "Module not found" errors

Install required dependencies:

```bash
# For Supabase adapter
pip install supabase

# For PostgreSQL adapters
pip install asyncpg

# For all adapters
pip install -r backend/requirements.txt
```

### Connection failures

Check your configuration:

```bash
# Verify environment variables
echo $DATABASE_TYPE
echo $SUPABASE_URL
echo $POSTGRES_URL

# Test connection
python -c "from backend.services.database_factory import create_database_adapter; import asyncio; adapter = create_database_adapter(); asyncio.run(adapter.connect())"
```

### Cross-schema queries fail

Supabase adapter needs either:
- `SUPABASE_SERVICE_ROLE_KEY` for PostgREST cross-schema access, OR
- `DATABASE_CONNECTION_URL` for direct asyncpg connections

```bash
# Add one of these to .env
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
DATABASE_CONNECTION_URL=postgresql://...
```

## Performance Considerations

### Supabase Adapter

- **PostgREST**: Fast for single-table queries, limited for JOINs
- **asyncpg**: Faster for complex queries, requires direct connection
- **Recommendation**: Use both (adapter handles fallback automatically)

### PostgreSQL Adapter

- **Direct SQL**: Full control, optimal performance
- **Connection pooling**: Configure pool size based on load
- **Recommendation**: Tune pool settings for your workload

### Docker PostgreSQL Adapter

- **Development only**: Not optimized for production
- **Volume mounts**: Use volumes for data persistence
- **Recommendation**: Don't use in production

## Related Documentation

- [Database Schema](DATABASE_SCHEMA.md) - Complete schema reference
- [Migration Guide](../development/MIGRATION_GUIDE.md) - Database migrations
- [Deployment Guide](../deployment/DEPLOYMENT.md) - Production setup

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [Best Practices](#best-practices)
3. Open an issue on GitHub
