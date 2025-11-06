"""
Export Database Schema for Migration 123 Documentation
"""

import os
import csv
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env.database')

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

print("="*60)
print("EXPORTING DATABASE SCHEMA FOR MIGRATION 123")
print("="*60)

# Export schema query
query = """
SELECT table_schema, table_name, column_name, data_type, 
       character_maximum_length, is_nullable, column_default, udt_name
FROM information_schema.columns 
WHERE table_schema LIKE 'krai_%'
ORDER BY table_schema, table_name, ordinal_position
"""

try:
    result = supabase.rpc('exec_sql', {'sql_text': query}).execute()
    
    if result.data and not result.data.get('error'):
        columns = result.data
        
        # Save to CSV
        csv_file = project_root / 'Supabase Migration 123 Columns.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if columns:
                writer = csv.DictWriter(f, fieldnames=columns[0].keys())
                writer.writeheader()
                writer.writerows(columns)
        
        print(f"✅ Exported {len(columns)} columns to {csv_file.name}")
        print(f"📁 Location: {csv_file}")
        
        # Check if structured_extractions has metadata column
        metadata_cols = [col for col in columns 
                        if col['table_schema'] == 'krai_intelligence' 
                        and col['table_name'] == 'structured_extractions'
                        and col['column_name'] == 'metadata']
        
        if metadata_cols:
            print("✅ Confirmed: metadata column exists in structured_extractions")
            for col in metadata_cols:
                print(f"   - Type: {col['data_type']}")
                print(f"   - Nullable: {col['is_nullable']}")
                print(f"   - Default: {col['column_default']}")
        else:
            print("⚠️  Warning: metadata column not found in structured_extractions")
            
    else:
        error = result.data.get('error') if result.data else 'Unknown error'
        print(f"❌ Error exporting schema: {error}")
        
except Exception as e:
    print(f"❌ Exception: {e}")

print("\nNext step: Run 'python generate_db_doc_from_csv.py' to update DATABASE_SCHEMA.md")
