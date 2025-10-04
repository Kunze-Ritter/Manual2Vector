"""
Check which schema the documents table is in
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

print("Checking documents table schema...")
print("="*60)

# Try different schemas
schemas_to_try = ['public', 'krai_core']

for schema in schemas_to_try:
    try:
        if schema == 'public':
            result = supabase.table("documents").select("*").limit(1).execute()
        else:
            result = supabase.table(f"{schema}.documents").select("*").limit(1).execute()
        
        if result.data is not None:
            print(f"\n✅ Found in schema: {schema}")
            
            # Check columns
            if result.data and len(result.data) > 0:
                columns = list(result.data[0].keys())
                print(f"\n   Columns found ({len(columns)}):")
                for col in sorted(columns):
                    print(f"      - {col}")
                
                if 'stage_status' in columns:
                    print(f"\n   ✅ stage_status column EXISTS!")
                else:
                    print(f"\n   ❌ stage_status column MISSING!")
            break
    except Exception as e:
        print(f"\n❌ Not in schema: {schema}")
        print(f"   Error: {str(e)[:100]}")

print("\n" + "="*60)
