#!/usr/bin/env python3
"""Run migration to create error_code_images junction table"""

import os
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.env_loader import load_all_env_files
from services.db_pool import get_pool

# Load environment variables
project_root = Path(__file__).parent.parent.parent
load_all_env_files(project_root)

print("=" * 80)
print("RUNNING MIGRATION: error_code_images junction table")
print("=" * 80)

# Read migration file
migration_file = Path(__file__).parent.parent / "migrations" / "create_error_code_images_junction.sql"
with open(migration_file, 'r') as f:
    sql = f.read()

print("\n📝 Migration SQL:")
print("-" * 80)
print(sql[:500] + "..." if len(sql) > 500 else sql)
print("-" * 80)

print("\n🚀 Executing migration...")


async def run_migration():
    """Execute migration using asyncpg"""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(sql)
            print("✅ Migration executed successfully!")
            print("\n📋 Next steps:")
            print("   Run: python scripts/link_error_codes_to_images.py")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\n📋 Please run SQL manually in PostgreSQL client (psql or pgAdmin):")
        print(f"   File: {migration_file}")
        sys.exit(1)


try:
    asyncio.run(run_migration())
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
