"""
Export Supabase Schema and Minimal Seed Data

This script exports the database schema and minimal seed data from Supabase
to create a reproducible local development environment.

Usage:
    python scripts/export_supabase_schema.py

Output:
    - database/seeds/01_schema.sql (DDL only)
    - database/seeds/02_minimal_seed.sql (minimal data for testing)
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts._env import load_env

# Load environment
load_env(extra_files=['.env.database'])


def get_pg_dump_executable() -> str:
    """Return the pg_dump executable path (env override supported)."""
    pg_dump_path = os.getenv('PG_DUMP_PATH')
    if pg_dump_path:
        return pg_dump_path
    return 'pg_dump'

def get_connection_string():
    """Build PostgreSQL connection string from Supabase credentials"""
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not service_role_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env.database")
        sys.exit(1)
    
    # Extract project ref from URL
    # Format: https://PROJECT_REF.supabase.co
    project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
    
    # Supabase direct connection format
    # Note: Password is the service role key, but we need the actual DB password
    # For now, we'll use pg_dump with the Supabase connection pooler
    print("⚠️  Note: You need the database password from Supabase Dashboard")
    print("   Go to: Project Settings > Database > Connection string")
    print("   Copy the password and set it as SUPABASE_DB_PASSWORD in .env.database")
    
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    if not db_password:
        print("\n❌ Please add SUPABASE_DB_PASSWORD to .env.database")
        print("   Get it from: Supabase Dashboard > Settings > Database")
        sys.exit(1)
    
    # Direct connection string
    conn_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
    return conn_string

def export_schema():
    """Export database schema (DDL only)"""
    print("\n" + "="*70)
    print("EXPORTING SUPABASE SCHEMA")
    print("="*70)
    
    conn_string = get_connection_string()
    output_dir = PROJECT_ROOT / 'database' / 'seeds'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    schema_file = output_dir / '01_schema.sql'
    
    print(f"\n📦 Exporting schema to: {schema_file}")
    
    # Export schema only (no data) for krai_* schemas
    cmd = [
        get_pg_dump_executable(),
        '--schema-only',           # DDL only
        '--clean',                 # Add DROP statements
        '--if-exists',             # Add IF EXISTS to DROP
        '--no-owner',              # Don't include ownership
        '--no-privileges',         # Don't include privileges
        '--schema=krai_core',
        '--schema=krai_content',
        '--schema=krai_intelligence',
        '--schema=krai_system',
        '--schema=krai_parts',
        '--file', str(schema_file),
        conn_string
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Schema exported successfully")
        print(f"   File size: {schema_file.stat().st_size / 1024:.1f} KB")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Export failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ pg_dump not found. Please install PostgreSQL client tools.")
        print("   Windows: https://www.postgresql.org/download/windows/")
        print("   Or use: winget install PostgreSQL.PostgreSQL")
        return False

def export_minimal_seed():
    """Export minimal seed data for testing"""
    print("\n" + "="*70)
    print("EXPORTING MINIMAL SEED DATA")
    print("="*70)
    
    conn_string = get_connection_string()
    output_dir = PROJECT_ROOT / 'database' / 'seeds'
    seed_file = output_dir / '02_minimal_seed.sql'
    
    print(f"\n📦 Exporting minimal seed data to: {seed_file}")
    
    # Export only essential tables with limited rows
    # Manufacturers, product series, and a few sample products
    tables = [
        'krai_core.manufacturers',
        'krai_core.product_series',
        'krai_core.products',
    ]
    
    cmd = [
        get_pg_dump_executable(),
        '--data-only',             # Data only (no DDL)
        '--no-owner',              # Don't include ownership
        '--no-privileges',         # Don't include privileges
        '--column-inserts',        # Use column names in INSERT
        '--rows-per-insert=100',   # Batch inserts
    ]
    
    # Add each table
    for table in tables:
        cmd.extend(['--table', table])
    
    cmd.extend([
        '--file', str(seed_file),
        conn_string
    ])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Seed data exported successfully")
        print(f"   File size: {seed_file.stat().st_size / 1024:.1f} KB")
        
        # Add note to limit data in the future
        with open(seed_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        header = """--
-- Minimal Seed Data for Local Development
-- 
-- This file contains essential reference data (manufacturers, products, etc.)
-- for local testing. It does NOT include:
-- - User data
-- - Production documents
-- - Embeddings
-- - Large binary data
--
-- To update this seed:
-- 1. Run: python scripts/export_supabase_schema.py
-- 2. Review changes before committing
-- 3. Keep file size < 1 MB for fast loading
--

"""
        with open(seed_file, 'w', encoding='utf-8') as f:
            f.write(header + content)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Export failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ pg_dump not found. Please install PostgreSQL client tools.")
        return False

def update_docker_compose():
    """Check if docker-compose.yml is configured for seed loading"""
    print("\n" + "="*70)
    print("CHECKING DOCKER CONFIGURATION")
    print("="*70)
    
    docker_compose = PROJECT_ROOT / 'docker-compose.yml'
    
    with open(docker_compose, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'database/seeds' in content:
        print("✅ docker-compose.yml already configured for seed loading")
    else:
        print("⚠️  docker-compose.yml needs to be updated")
        print("\n   Add this to krai-postgres volumes:")
        print("   - ./database/seeds:/docker-entrypoint-initdb.d/seeds")
        print("\n   This will auto-load seeds on first container start")

def main():
    """Main export workflow"""
    print("\n" + "="*70)
    print("SUPABASE SCHEMA & SEED EXPORT")
    print("="*70)
    
    print("\nThis script will export:")
    print("  1. Database schema (DDL) for all krai_* schemas")
    print("  2. Minimal seed data (manufacturers, products, etc.)")
    print("\nThese files will be used to initialize local Docker PostgreSQL.")
    
    # Check for pg_dump
    try:
        subprocess.run([get_pg_dump_executable(), '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n❌ pg_dump not found!")
        print("   Please install PostgreSQL client tools first.")
        print("   Windows: winget install PostgreSQL.PostgreSQL")
        sys.exit(1)
    
    # Export schema
    if not export_schema():
        sys.exit(1)
    
    # Export minimal seed
    if not export_minimal_seed():
        sys.exit(1)
    
    # Check docker-compose
    update_docker_compose()
    
    print("\n" + "="*70)
    print("✅ EXPORT COMPLETE")
    print("="*70)
    
    print("\nNext steps:")
    print("  1. Review exported files in database/seeds/")
    print("  2. Update docker-compose.yml if needed (see above)")
    print("  3. Test with: docker-compose down -v && docker-compose up -d krai-postgres")
    print("  4. Verify with: python scripts/test_adapter_quick.py")
    print("\n💡 Tip: Keep seed files < 1 MB and exclude sensitive data")

if __name__ == '__main__':
    main()
