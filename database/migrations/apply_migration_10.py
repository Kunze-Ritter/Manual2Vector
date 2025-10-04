"""
Apply Migration 10: Per-Stage Status Tracking

Automatically applies the migration to Supabase.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv()

def apply_migration():
    """Apply migration 10"""
    
    print("="*80)
    print("  Applying Migration 10: Per-Stage Status Tracking")
    print("="*80)
    
    # Read migration file
    migration_file = Path(__file__).parent / "10_stage_status_tracking.sql"
    
    if not migration_file.exists():
        print(f"\n❌ Migration file not found: {migration_file}")
        return False
    
    print(f"\n📄 Reading migration file...")
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print(f"   File size: {len(sql)} bytes")
    print(f"   Lines: {sql.count(chr(10))}")
    
    # Connect to Supabase
    print(f"\n🔌 Connecting to Supabase...")
    
    try:
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    # Execute migration
    print(f"\n⚙️  Executing migration...")
    print("   This may take 10-20 seconds...")
    
    try:
        # Supabase PostgREST doesn't support direct SQL execution
        # We need to use the RPC or direct connection
        print("\n   ⚠️  Note: Supabase client doesn't support direct SQL execution.")
        print("   Please apply this migration manually via SQL Editor in Supabase Dashboard.")
        print("\n   Steps:")
        print("   1. Go to: https://supabase.com/dashboard")
        print("   2. Select your project")
        print("   3. Click 'SQL Editor' in left menu")
        print("   4. Click '+ New query'")
        print(f"   5. Copy content from: {migration_file}")
        print("   6. Paste and click 'Run'")
        
        return None
        
    except Exception as e:
        print(f"\n   ❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    result = apply_migration()
    
    if result is True:
        print("\n" + "="*80)
        print("  ✅ Migration 10 applied successfully!")
        print("="*80)
        print("\n  Next steps:")
        print("  1. Test with: python test_migration_10.py")
        print("  2. Check Supabase Dashboard → Database → Tables")
        print("  3. Look for 'stage_status' column in 'documents' table")
        print("\n")
    elif result is False:
        print("\n" + "="*80)
        print("  ❌ Migration failed!")
        print("="*80)
        print("\n  Please check the error message above.")
        print("\n")
    else:
        print("\n" + "="*80)
        print("  📋 Manual application required")
        print("="*80)
        print("\n  Follow the steps above to apply the migration manually.")
        print("\n")
