"""
Quick Database Adapter Test

Fast validation that the adapter pattern is working.
Run this after implementing the adapter pattern to verify basic functionality.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts._env import load_env

# Load environment
load_env(extra_files=['.env.database'])


async def quick_test():
    """Quick adapter test"""
    print("\n" + "="*70)
    print("  QUICK DATABASE ADAPTER TEST")
    print("="*70 + "\n")
    
    try:
        # Test 1: Import factory
        print("1️⃣  Importing factory...", end=" ")
        from backend.services.database_factory import create_database_adapter
        print("✅")
        
        # Test 2: Create adapter
        print("2️⃣  Creating adapter...", end=" ")
        db_type = os.getenv("DATABASE_TYPE", "supabase")
        adapter = create_database_adapter()
        print(f"✅ ({adapter.__class__.__name__})")
        
        # Test 3: Connect
        print("3️⃣  Connecting to database...", end=" ")
        await adapter.connect()
        print("✅")
        
        # Test 4: Test connection
        print("4️⃣  Testing connection...", end=" ")
        is_connected = await adapter.test_connection()
        if is_connected:
            print("✅")
        else:
            print("❌ Connection test failed")
            return False
        
        # Test 5: Check attributes
        print("5️⃣  Checking adapter features:")
        if hasattr(adapter, 'client'):
            print(f"   - Supabase client: {'✅' if adapter.client else '❌'}")
        if hasattr(adapter, 'pg_pool'):
            print(f"   - PostgreSQL pool: {'✅' if adapter.pg_pool else '❌'}")
        if hasattr(adapter, 'service_client'):
            print(f"   - Service role: {'✅' if adapter.service_client else '❌'}")
        
        # Test 6: Backward compatibility
        print("6️⃣  Testing backward compatibility...", end=" ")
        from backend.services.database_service_production import DatabaseService
        db = DatabaseService(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_ANON_KEY")
        )
        print("✅")
        
        print("\n" + "="*70)
        print("  ✅ ALL QUICK TESTS PASSED!")
        print("="*70 + "\n")
        
        print("ℹ️  Run full test suite: python tests/test_database_adapters.py")
        return True
        
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)
