#!/usr/bin/env python3
"""Run migration to create error_code_images junction table"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 80)
print("RUNNING MIGRATION: error_code_images junction table")
print("=" * 80)

# Read migration file
migration_file = Path(__file__).parent.parent / "migrations" / "create_error_code_images_junction.sql"
with open(migration_file, 'r') as f:
    sql = f.read()

print("\n📝 Migration SQL:")
print("-" * 80)
print(sql[:500] + "..." if len(sql) > 500 else sql)
print("-" * 80)

print("\n🚀 Executing migration...")

try:
    # Execute SQL via RPC (if available) or direct query
    # Note: Supabase Python client doesn't support raw SQL directly
    # We need to use psycopg2 or execute via Supabase SQL Editor
    
    print("\n⚠️  MANUAL STEP REQUIRED:")
    print("\n1. Go to Supabase SQL Editor:")
    print("   https://supabase.com/dashboard/project/YOUR_PROJECT/sql")
    print("\n2. Copy and paste this SQL:")
    print(f"\n   File: {migration_file}")
    print("\n3. Run the SQL")
    print("\n4. Then run: python scripts/link_error_codes_to_images.py")
    
    # Alternative: Use psycopg2 if available
    try:
        import psycopg2
        
        # Parse connection string from Supabase URL
        db_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL')
        
        if db_url:
            print("\n✅ Found DATABASE_URL - executing via psycopg2...")
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
            cur.close()
            conn.close()
            print("✅ Migration executed successfully!")
        else:
            print("\n❌ No DATABASE_URL found - please run SQL manually")
            
    except ImportError:
        print("\n💡 TIP: Install psycopg2 for automatic migration:")
        print("   pip install psycopg2-binary")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nPlease run SQL manually in Supabase SQL Editor")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
