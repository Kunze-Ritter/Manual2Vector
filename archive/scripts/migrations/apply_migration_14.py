"""
Apply Migration 14: RPC function for updating document manufacturer
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from supabase import create_client


def main():
    """Apply migration 14"""
    
    print("\n" + "="*80)
    print("  APPLYING MIGRATION 14: update_document_manufacturer RPC function")
    print("="*80)
    
    # Connect to Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: Supabase credentials not found")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    print("✅ Connected to Supabase")
    
    # Read migration file
    migration_file = Path(__file__).parent.parent / 'database' / 'migrations' / '14_rpc_update_document_manufacturer.sql'
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return
    
    sql = migration_file.read_text()
    print(f"\n📄 Migration file: {migration_file.name}")
    print(f"   Lines: {len(sql.splitlines())}")
    
    # Execute migration
    print("\n⏳ Executing migration...")
    
    try:
        # Execute the entire SQL (it's a single function definition)
        print(f"\n   Creating RPC function...")
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()
        print(f"   ✅ Success")
        
        print("\n" + "="*80)
        print("  ✅ MIGRATION 14 APPLIED SUCCESSFULLY!")
        print("="*80)
        print("\n📊 Changes:")
        print("   - Created: krai_core.update_document_manufacturer() RPC function")
        print("   - Purpose: Bypass PostgREST schema cache issues")
        print("   - Usage: supabase.rpc('update_document_manufacturer', {...})")
        
    except Exception as e:
        error_msg = str(e)
        
        # Check if it's the exec_sql not found error
        if 'exec_sql' in error_msg and 'PGRST202' in error_msg:
            print(f"\n⚠️  exec_sql RPC function not available")
            print("\n💡 Manual execution required:")
            print("   1. Go to Supabase SQL Editor:")
            print("      https://supabase.com/dashboard/project/crujfdpqdjzcfqeyhang/sql/new")
            print("   2. Copy and paste the following SQL:\n")
            print("-" * 80)
            print(sql)
            print("-" * 80)
            print("\n   3. Click 'Run' to execute")
        else:
            print(f"\n❌ Error executing migration: {e}")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
