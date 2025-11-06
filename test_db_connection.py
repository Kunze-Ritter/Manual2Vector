#!/usr/bin/env python3
"""Quick test to debug database connection issues"""

import os
import asyncio
import sys
import asyncpg
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / 'backend'))

from backend.services.database_factory import create_database_adapter

async def test_connection():
    """Test database connection using factory"""
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    print("Environment variables:")
    print(f"DATABASE_TYPE: {os.getenv('DATABASE_TYPE')}")
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
    print(f"DATABASE_HOST: {os.getenv('DATABASE_HOST')}")
    print(f"DATABASE_PORT: {os.getenv('DATABASE_PORT')}")
    print(f"DATABASE_NAME: {os.getenv('DATABASE_NAME')}")
    print(f"DATABASE_USER: {os.getenv('DATABASE_USER')}")
    print(f"DATABASE_PASSWORD: {os.getenv('DATABASE_PASSWORD')}")
    print()
    print("Factory environment variables:")
    print(f"POSTGRES_URL: {os.getenv('POSTGRES_URL')}")
    print(f"DATABASE_CONNECTION_URL: {os.getenv('DATABASE_CONNECTION_URL')}")
    print(f"POSTGRES_HOST: {os.getenv('POSTGRES_HOST')}")
    print(f"POSTGRES_PORT: {os.getenv('POSTGRES_PORT')}")
    print(f"POSTGRES_DB: {os.getenv('POSTGRES_DB')}")
    print(f"POSTGRES_USER: {os.getenv('POSTGRES_USER')}")
    print(f"POSTGRES_PASSWORD: {os.getenv('POSTGRES_PASSWORD')}")
    print()
    
    try:
        print("Testing direct asyncpg connection...")
        conn = await asyncpg.connect(
            host='127.0.0.1',
            port=5432,
            user='krai_user',
            password='krai_secure_password',
            database='krai'
        )
        print("✅ Direct asyncpg connection successful!")
        
        # Test a simple query
        result = await conn.fetchval("SELECT version()")
        print(f"PostgreSQL version: {result}")
        
        await conn.close()
        print("✅ Disconnected successfully")
        
    except Exception as e:
        print(f"❌ Direct asyncpg connection failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    try:
        print("\nTesting database adapter...")
        adapter = create_database_adapter()
        
        print("Connecting to database...")
        await adapter.connect()
        
        print("✅ Database adapter connection successful!")
        
        # Test connection using the available method
        success = await adapter.test_connection()
        print(f"✅ Database adapter test connection: {'Success' if success else 'Failed'}")
        
        print("✅ Database adapter is working correctly!")
        
    except Exception as e:
        print(f"❌ Database adapter connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
