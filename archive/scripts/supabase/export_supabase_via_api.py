"""
Export Supabase Schema via API (no database password required)

Uses Supabase REST API with service role key to export schema and data.
This works with your existing SUPABASE_SERVICE_ROLE_KEY.

Usage:
    python scripts/export_supabase_via_api.py
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.processors.env_loader import load_all_env_files

loaded_env_files = load_all_env_files(PROJECT_ROOT, extra_files=['.env.database'])
if not loaded_env_files:
    print("⚠️  No .env files found - relying on system environment variables")

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ supabase-py not installed!")
    print("   Install with: pip install supabase")
    sys.exit(1)


def get_supabase_client() -> Client:
    """Get Supabase client with service role"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)
    
    return create_client(url, key)


def export_schema():
    """Export database schema using information_schema"""
    print("\n" + "="*70)
    print("EXPORTING SCHEMA VIA API")
    print("="*70)
    
    client = get_supabase_client()
    output_dir = PROJECT_ROOT / 'database' / 'seeds'
    output_dir.mkdir(parents=True, exist_ok=True)
    schema_file = output_dir / '01_schema.sql'
    
    schemas = ['krai_core', 'krai_content', 'krai_intelligence', 'krai_system', 'krai_parts']
    
    print("\n⚠️  Note: API-based export has limitations")
    print("   For full schema export, use pg_dump with database password")
    print("   This will export table structure based on existing data\n")
    
    with open(schema_file, 'w', encoding='utf-8') as f:
        f.write("--\n")
        f.write("-- Supabase Schema Export (via API)\n")
        f.write("-- Note: This is a simplified export. For full DDL, use pg_dump.\n")
        f.write("--\n\n")
        
        # Create schemas
        f.write("-- Create schemas\n")
        for schema in schemas:
            f.write(f"CREATE SCHEMA IF NOT EXISTS {schema};\n")
        f.write("\n")
        
        # Note: We can't get full DDL via REST API
        # We'll create a minimal schema based on the data we can export
        f.write("-- Tables will be created based on seed data\n")
        f.write("-- For full schema with indexes, constraints, etc., use pg_dump\n\n")
    
    print(f"✅ Basic schema file created: {schema_file}")
    print(f"   File size: {schema_file.stat().st_size / 1024:.1f} KB")


def export_seed_data():
    """Export seed data via Supabase API"""
    print("\n" + "="*70)
    print("EXPORTING SEED DATA VIA API")
    print("="*70)
    
    client = get_supabase_client()
    output_dir = PROJECT_ROOT / 'database' / 'seeds'
    seed_file = output_dir / '02_minimal_seed.sql'
    
    # Tables to export (using views that are exposed via PostgREST)
    tables_to_export = [
        ('vw_manufacturers', 'manufacturers', 100),
        ('vw_product_series', 'product_series', 100),
        ('vw_products', 'products', 50),
    ]
    
    with open(seed_file, 'w', encoding='utf-8') as f:
        f.write("--\n")
        f.write("-- Minimal Seed Data (exported via Supabase API)\n")
        f.write("--\n\n")
        
        for view_name, table_name, limit in tables_to_export:
            print(f"📦 Exporting: {view_name} -> {table_name} (limit: {limit})")
            
            try:
                # Query via PostgREST (using view name)
                response = client.table(view_name).select("*").limit(limit).execute()
                rows = response.data
                
                if not rows:
                    print(f"   ℹ️  No data found")
                    continue
                
                print(f"   ✅ Exported {len(rows)} rows")
                
                # Determine schema from table name pattern
                if table_name in ['manufacturers', 'product_series', 'products', 'documents']:
                    schema = 'krai_core'
                elif table_name in ['chunks', 'images', 'videos']:
                    schema = 'krai_content'
                elif table_name in ['embeddings']:
                    schema = 'krai_intelligence'
                elif table_name in ['parts_catalog']:
                    schema = 'krai_parts'
                else:
                    schema = 'krai_system'
                
                full_table = f"{schema}.{table_name}"
                
                f.write(f"-- Table: {full_table}\n")
                f.write(f"-- Rows: {len(rows)}\n\n")
                
                # Get column names from first row
                if rows:
                    col_names = list(rows[0].keys())
                    
                    # Write INSERT statements
                    for row in rows:
                        values = []
                        for col_name in col_names:
                            val = row.get(col_name)
                            if val is None:
                                values.append('NULL')
                            elif isinstance(val, str):
                                # Escape single quotes
                                escaped = val.replace("'", "''")
                                values.append(f"'{escaped}'")
                            elif isinstance(val, bool):
                                values.append('TRUE' if val else 'FALSE')
                            elif isinstance(val, (list, dict)):
                                # JSON
                                import json
                                escaped = json.dumps(val).replace("'", "''")
                                values.append(f"'{escaped}'::jsonb")
                            else:
                                values.append(str(val))
                        
                        f.write(f"INSERT INTO {full_table} ({', '.join(col_names)}) VALUES ({', '.join(values)}) ON CONFLICT DO NOTHING;\n")
                    
                    f.write("\n")
            
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
    
    print(f"\n✅ Seed data exported to: {seed_file}")
    print(f"   File size: {seed_file.stat().st_size / 1024:.1f} KB")


def main():
    """Main export workflow"""
    print("\n" + "="*70)
    print("SUPABASE EXPORT VIA API")
    print("="*70)
    
    print("\nThis script uses Supabase REST API (no database password needed)")
    print("It will export:")
    print("  1. Basic schema structure")
    print("  2. Seed data (manufacturers, products, etc.)")
    
    # Export schema
    export_schema()
    
    # Export seed data
    export_seed_data()
    
    print("\n" + "="*70)
    print("✅ EXPORT COMPLETE")
    print("="*70)
    
    print("\nNext steps:")
    print("  1. Review exported files in database/seeds/")
    print("  2. For full schema with indexes/constraints, you'll need pg_dump")
    print("  3. Test with: docker-compose down -v && docker-compose up -d krai-postgres")
    print("  4. Verify with: python scripts/test_adapter_quick.py")


if __name__ == '__main__':
    main()
