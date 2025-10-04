"""
Check krai_core.documents table directly
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

print("Checking krai_core.documents table...")
print("="*60)

# Try to query with raw SQL using RPC or direct query
try:
    # Query krai_core.documents directly
    result = supabase.rpc('sql', {
        'query': 'SELECT column_name FROM information_schema.columns WHERE table_schema = \'krai_core\' AND table_name = \'documents\' ORDER BY ordinal_position'
    }).execute()
    
    print("Columns in krai_core.documents:")
    if result.data:
        for col in result.data:
            print(f"  - {col}")
    
except Exception as e:
    print(f"RPC method failed: {e}")
    print("\nTrying alternative method...")
    
    # Alternative: Try to select from schema-qualified table
    try:
        # Some Supabase setups might need this syntax
        result = supabase.postgrest.from_('krai_core.documents').select('*').limit(1).execute()
        print("Found krai_core.documents!")
        
        if result.data and len(result.data) > 0:
            columns = list(result.data[0].keys())
            print(f"\nColumns ({len(columns)}):")
            for col in sorted(columns):
                print(f"  - {col}")
                
            if 'stage_status' in columns:
                print("\n✅ stage_status EXISTS!")
            else:
                print("\n❌ stage_status MISSING!")
    except Exception as e2:
        print(f"Alternative method also failed: {e2}")
        
        print("\n⚠️  Supabase Python client kann nicht direkt auf krai_core zugreifen")
        print("    Das ist normal - PostgREST arbeitet mit public schema")
        print("\n    Die Migration 10 hat wahrscheinlich krai_core.documents geändert,")
        print("    aber wir müssen testen ob die Functions funktionieren!")

print("\n" + "="*60)
