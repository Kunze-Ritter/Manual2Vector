# Database Seeds

This directory contains SQL seed files for initializing local PostgreSQL development databases.

## Files

- `01_schema.sql` - Database schema (DDL) for all `krai_*` schemas
- `02_minimal_seed.sql` - Minimal reference data (manufacturers, products, etc.)

## Usage

### Automatic Loading (Docker)

Seeds are automatically loaded when starting a fresh `krai-postgres` container:

```bash
# Remove old container and volume
docker-compose down -v

# Start fresh container (seeds auto-load)
docker-compose up -d krai-postgres

# Wait for healthy status
docker ps --filter name=krai-postgres

# Test connection
python scripts/test_adapter_quick.py
```

**Important:** Seeds only load on **first container start** with a fresh volume. If you need to reload:
1. Stop container: `docker-compose down`
2. Remove volume: `docker volume rm krai-minimal_krai_postgres_data`
3. Start again: `docker-compose up -d krai-postgres`

### Manual Loading

To manually load seeds into an existing database:

```bash
# Load schema
docker exec -i krai-postgres psql -U krai_user -d krai < database/seeds/01_schema.sql

# Load seed data
docker exec -i krai-postgres psql -U krai_user -d krai < database/seeds/02_minimal_seed.sql
```

## Exporting from Supabase

To update seeds from the production Supabase database:

```bash
# 1. Ensure SUPABASE_DB_PASSWORD is set in .env.database
#    Get it from: Supabase Dashboard > Settings > Database > Connection string

# 2. Run export script
python scripts/export_supabase_schema.py

# 3. Review changes
git diff database/seeds/

# 4. Commit if appropriate
git add database/seeds/
git commit -m "Update database seeds from Supabase"
```

## What to Include

### ✅ Include in Seeds

- Database schema (tables, indexes, constraints)
- Reference data (manufacturers, product series)
- Sample products (5-10 per manufacturer)
- Essential configuration data

### ❌ Exclude from Seeds

- User data (PII, credentials)
- Production documents
- Large binary data (PDFs, images)
- Embeddings (regenerate locally)
- Temporary/cache data
- API keys or secrets

## File Size Guidelines

- Keep total seed size < 5 MB
- Schema file should be < 500 KB
- Seed data should be < 1 MB
- If larger, consider splitting or reducing sample data

## Security Notes

⚠️ **Never commit sensitive data:**
- No user credentials
- No API keys
- No production customer data
- No PII (personally identifiable information)

Review all seed files before committing to ensure they contain only public/test data.

## Troubleshooting

### Seeds not loading

**Problem:** Container starts but seeds don't apply.

**Solution:** Seeds only run on first start with empty volume. To force reload:
```bash
docker-compose down -v
docker-compose up -d krai-postgres
```

### Permission errors

**Problem:** `permission denied` when loading seeds.

**Solution:** Ensure files are readable:
```bash
chmod 644 database/seeds/*.sql
```

### Connection errors

**Problem:** Can't connect to database after seeding.

**Solution:** Wait for health check:
```bash
docker ps --filter name=krai-postgres
# Wait for "healthy" status
```

### Schema conflicts

**Problem:** `relation already exists` errors.

**Solution:** Schema file includes `DROP ... IF EXISTS`. If still failing:
```bash
# Connect to database
docker exec -it krai-postgres psql -U krai_user -d krai

# Drop schemas manually
DROP SCHEMA IF EXISTS krai_core CASCADE;
DROP SCHEMA IF EXISTS krai_content CASCADE;
DROP SCHEMA IF EXISTS krai_intelligence CASCADE;
DROP SCHEMA IF EXISTS krai_system CASCADE;
DROP SCHEMA IF EXISTS krai_parts CASCADE;

# Exit and reload seeds
\q
```

## CI/CD Integration

For GitHub Actions or other CI:

```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_DB: krai
      POSTGRES_USER: krai_user
      POSTGRES_PASSWORD: krai_password
    volumes:
      - ./database/seeds:/docker-entrypoint-initdb.d/seeds
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

## Maintenance

Update seeds when:
- Schema changes in production
- New reference data added (manufacturers, etc.)
- Breaking changes to data models
- Major version updates

Keep seeds synchronized with `DATABASE_SCHEMA.md` documentation.
