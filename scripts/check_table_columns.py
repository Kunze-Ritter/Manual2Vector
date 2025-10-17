"""
Check Table Columns
====================
Query Supabase to get detailed column information for any table.

Usage:
    python check_table_columns.py krai_intelligence chunks
    python check_table_columns.py krai_core products
"""

import os
import sys
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

def check_columns(schema_name, table_name):
    """Get column information for a table"""
    
    query = f"""
    SELECT 
        column_name,
        data_type,
        character_maximum_length,
        is_nullable,
        column_default,
        udt_name
    FROM information_schema.columns
    WHERE table_schema = '{schema_name}'
      AND table_name = '{table_name}'
    ORDER BY ordinal_position;
    """
    
    try:
        result = supabase.postgrest.rpc('exec_sql', {'query': query}).execute()
        return result.data
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python check_table_columns.py <schema> <table>")
        print("\nExamples:")
        print("  python check_table_columns.py krai_intelligence chunks")
        print("  python check_table_columns.py krai_core products")
        print("  python check_table_columns.py krai_content videos")
        sys.exit(1)
    
    schema = sys.argv[1]
    table = sys.argv[2]
    
    print("="*80)
    print(f"COLUMNS FOR: {schema}.{table}")
    print("="*80)
    
    columns = check_columns(schema, table)
    
    if columns:
        print(f"\n{'Column':<30} {'Type':<20} {'Nullable':<10} {'Default':<20}")
        print("-"*80)
        
        for col in columns:
            col_name = col['column_name']
            data_type = col['data_type']
            
            # Show length for varchar
            if col['character_maximum_length']:
                data_type += f"({col['character_maximum_length']})"
            
            # Show UDT name for special types (like vector)
            if col['udt_name'] and col['udt_name'] != col['data_type']:
                data_type = col['udt_name']
            
            nullable = "YES" if col['is_nullable'] == 'YES' else "NO"
            default = col['column_default'] or "-"
            
            # Truncate long defaults
            if len(default) > 20:
                default = default[:17] + "..."
            
            print(f"{col_name:<30} {data_type:<20} {nullable:<10} {default:<20}")
        
        print("\n" + "="*80)
        print(f"Total columns: {len(columns)}")
    else:
        print("\n❌ Could not retrieve columns")
        print("   Table might not exist or you don't have permissions")

if __name__ == "__main__":
    main()
