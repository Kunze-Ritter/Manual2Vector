"""
Apply Migration 12: Add processing_results to documents table
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

from supabase import create_client


def main():
    """Apply migration 12"""
    
    print("\n" + "="*80)
    print("  APPLYING MIGRATION 12: processing_results column")
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
    migration_file = Path(__file__).parent.parent.parent / 'database' / 'migrations' / '12_add_processing_results.sql'
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return
    
    sql = migration_file.read_text()
    print(f"\n📄 Migration file: {migration_file.name}")
    print(f"   Lines: {len(sql.splitlines())}")
    
    # Execute migration
    print("\n⏳ Executing migration...")
    
    try:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"\n   Statement {i}/{len(statements)}...")
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                print(f"   ✅ Success")
        
        print("\n" + "="*80)
        print("  ✅ MIGRATION 12 APPLIED SUCCESSFULLY!")
        print("="*80)
        print("\n📊 Changes:")
        print("   - Added: processing_results (JSONB)")
        print("   - Added: processing_error (TEXT)")
        print("   - Added: processing_status (TEXT)")
        print("   - Created: Index on processing_status")
        print("   - Created: GIN index on processing_results")
        
    except Exception as e:
        print(f"\n❌ Error executing migration: {e}")
        print("\n💡 Manual execution required:")
        print("   1. Go to Supabase SQL Editor")
        print("   2. Copy the SQL from: database/migrations/12_add_processing_results.sql")
        print("   3. Execute manually")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
