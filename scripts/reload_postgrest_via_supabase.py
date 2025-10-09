"""
Reload PostgREST Schema Cache via Supabase Client

Alternative method using Supabase client to execute SQL.
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print("❌ SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env")
    exit(1)

try:
    # Connect to Supabase
    print("🔌 Connecting to Supabase...")
    supabase = create_client(supabase_url, supabase_key)
    
    # Execute NOTIFY via RPC (if function exists) or direct SQL
    print("📢 Attempting to reload PostgREST schema...")
    
    # Try using rpc to execute raw SQL
    try:
        result = supabase.rpc('exec_sql', {
            'query': "NOTIFY pgrst, 'reload schema';"
        }).execute()
        print("✅ PostgREST schema cache reload signal sent via RPC!")
    except Exception as rpc_error:
        print(f"⚠️  RPC method failed: {rpc_error}")
        print("   This is expected if exec_sql function doesn't exist.")
        print("\n📝 Alternative: Restart your Supabase project to reload schema:")
        print("   1. Go to https://supabase.com/dashboard/project/crujfdpqdjzcfqeyhang/settings/general")
        print("   2. Click 'Pause project' then 'Resume project'")
        print("   OR wait 24 hours for automatic schema cache refresh")
    
    print("\n💡 Workaround: Use RPC functions instead of direct table updates")
    print("   The code already uses insert_error_code RPC function.")
    print("   We can create similar RPC functions for document updates.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
