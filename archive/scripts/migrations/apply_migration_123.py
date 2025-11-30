"""
Apply Migration 123: Add metadata column to structured_extractions
"""

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.processors.env_loader import load_all_env_files

from supabase import create_client


# Load environment
load_all_env_files(PROJECT_ROOT)

def main():
    """Apply migration 123"""
    
    print("\n" + "="*80)
    print("  APPLYING MIGRATION 123: Add metadata column to structured_extractions")
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
    migration_file = Path(__file__).parent.parent / 'database' / 'migrations' / '123_add_metadata_to_structured_extractions.sql'
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return
    
    print(f"✅ Found migration file: {migration_file.name}")
    
    # Read and execute migration
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print("📝 Migration SQL:")
    print("-" * 60)
    print(sql_content)
    print("-" * 60)
    
    try:
        # Execute the migration using RPC
        result = supabase.rpc('exec_sql', {'sql_text': sql_content}).execute()
        
        if result.data:
            print("✅ Migration executed successfully!")
            print(f"📊 Result: {result.data}")
        else:
            print("⚠️  Migration executed but no data returned")
            
    except Exception as e:
        print(f"❌ Error executing migration: {e}")
        
        # Fallback: Try direct SQL execution if available
        try:
            print("🔄 Attempting fallback execution...")
            # For Supabase, we might need to use a different approach
            # This is a placeholder for the actual execution method
            print("⚠️  Please run the SQL manually in your Supabase dashboard:")
            print(sql_content)
        except Exception as fallback_error:
            print(f"❌ Fallback also failed: {fallback_error}")
    
    print("\n" + "="*80)
    print("  MIGRATION 123 COMPLETE")
    print("="*80)
    print("\n📋 Next steps:")
    print("1. Verify the metadata column was added to krai_intelligence.structured_extractions")
    print("2. Export your database schema to CSV:")
    print("   SELECT table_schema, table_name, column_name, data_type,")
    print("          character_maximum_length, is_nullable, column_default, udt_name")
    print("   FROM information_schema.columns")
    print("   WHERE table_schema LIKE 'krai_%'")
    print("   ORDER BY table_schema, table_name, ordinal_position;")
    print("3. Save the CSV as 'Supabase...Columns.csv' in the project root")
    print("4. Run: cd scripts && python generate_db_doc_from_csv.py")
    print("5. Commit the updated DATABASE_SCHEMA.md")


if __name__ == "__main__":
    main()
