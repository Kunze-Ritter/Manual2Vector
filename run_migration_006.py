"""
Run migration 006 to add product discovery columns
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run_migration():
    # Read migration SQL
    with open('database/migrations_postgresql/006_add_product_discovery_columns.sql', 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    # Connect to database
    postgres_url = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_CONNECTION_URL')
    if not postgres_url:
        postgres_url = f"postgresql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
    
    print(f"Connecting to database...")
    conn = await asyncpg.connect(postgres_url)
    
    try:
        print(f"Running migration 006...")
        await conn.execute(migration_sql)
        print("✅ Migration 006 completed successfully!")
        
        # Verify columns were added
        result = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'krai_core' 
            AND table_name = 'products'
            AND column_name IN ('specifications', 'urls', 'metadata', 'oem_manufacturer')
            ORDER BY column_name
        """)
        
        print("\n✅ Verified columns:")
        for row in result:
            print(f"   - {row['column_name']} ({row['data_type']})")
            
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(run_migration())
