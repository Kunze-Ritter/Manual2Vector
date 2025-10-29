"""Test Supabase database connection"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / '.env.database')

import asyncpg

async def test():
    supabase_url = os.getenv('SUPABASE_URL')
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    
    print(f"SUPABASE_URL: {supabase_url}")
    print(f"Password loaded: {bool(db_password)}")
    print(f"Password length: {len(db_password) if db_password else 0}")
    
    if not db_password:
        print("\n❌ SUPABASE_DB_PASSWORD not found in .env.database")
        return
    
    project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
    
    # Try direct connection
    conn_string = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
    
    print(f"\nTrying to connect to: db.{project_ref}.supabase.co:5432")
    
    try:
        conn = await asyncpg.connect(conn_string, timeout=10)
        print("✅ Connection successful!")
        
        # Test query
        version = await conn.fetchval('SELECT version()')
        print(f"PostgreSQL version: {version[:50]}...")
        
        await conn.close()
    except asyncpg.InvalidPasswordError:
        print("❌ Invalid password")
        print("   Check SUPABASE_DB_PASSWORD in .env.database")
    except asyncio.TimeoutError:
        print("❌ Connection timeout")
        print("   Your IP might not be whitelisted in Supabase")
        print("   Go to: Dashboard > Settings > Database > Connection Pooling")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")

if __name__ == '__main__':
    asyncio.run(test())
