"""
Check manufacturers in database
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

from backend.services.database_service import DatabaseService


async def check_manufacturers():
    """Check manufacturers in database"""
    print("=" * 80)
    print("🏭 Checking Manufacturers in Database")
    print("=" * 80)
    print()
    
    db = DatabaseService()
    
    try:
        await db.connect()
        print("✅ Connected to database")
        print()
        
        # Get all manufacturers
        query = """
            SELECT id, name, created_at
            FROM krai_core.manufacturers
            ORDER BY name
        """
        
        manufacturers = await db.fetch_all(query)
        
        if manufacturers:
            print(f"✅ Found {len(manufacturers)} manufacturers:")
            print()
            for m in manufacturers:
                print(f"   • {m['name']}")
                print(f"     ID: {m['id']}")
                print()
        else:
            print("❌ No manufacturers found in database")
            print()
            print("This is why Product Discovery cannot save products!")
        
        # Check for HP specifically
        print("=" * 80)
        print("🔍 Checking for HP")
        print("=" * 80)
        print()
        
        hp_query = """
            SELECT id, name
            FROM krai_core.manufacturers
            WHERE name ILIKE '%HP%'
        """
        
        hp_manufacturers = await db.fetch_all(hp_query)
        
        if hp_manufacturers:
            print(f"✅ Found {len(hp_manufacturers)} HP manufacturers:")
            for m in hp_manufacturers:
                print(f"   • {m['name']} (ID: {m['id']})")
        else:
            print("❌ No HP manufacturers found")
            print()
            print("Need to add 'HP Inc.' to manufacturers table!")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db.disconnect()
        print()
        print("=" * 80)
        print("✅ Check Complete")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(check_manufacturers())
