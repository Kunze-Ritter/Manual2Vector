#!/usr/bin/env python3
"""
Export Database Schema to CSV
==============================
Queries information_schema.columns for all krai_* schemas and exports to CSV.
This CSV can then be used by generate_db_doc_from_csv.py to update DATABASE_SCHEMA.md.

Usage:
    python scripts/export_db_schema_csv.py
"""

import sys
import csv
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.migration_helpers import create_connected_adapter, pg_fetch_all, run_async


async def export_schema():
    """Export database schema to CSV"""
    print("🔍 Connecting to database...")
    adapter = await create_connected_adapter()
    
    try:
        print("📊 Querying information_schema.columns for krai_* schemas...")
        
        query = """
        SELECT 
            table_schema, 
            table_name, 
            column_name, 
            data_type,
            character_maximum_length, 
            is_nullable, 
            column_default, 
            udt_name
        FROM information_schema.columns 
        WHERE table_schema LIKE 'krai_%'
        ORDER BY table_schema, table_name, ordinal_position
        """
        
        rows = await pg_fetch_all(adapter, query)
        
        if not rows:
            print("⚠️  No krai_* schemas found in database!")
            return
        
        print(f"✅ Found {len(rows)} columns across krai_* schemas")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = PROJECT_ROOT / f"Supabase_Schema_Export_{timestamp}.csv"
        
        print(f"💾 Writing to: {csv_filename.name}")
        
        # Write CSV
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'table_schema',
                'table_name', 
                'column_name',
                'data_type',
                'character_maximum_length',
                'is_nullable',
                'column_default',
                'udt_name'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in rows:
                writer.writerow({
                    'table_schema': row['table_schema'],
                    'table_name': row['table_name'],
                    'column_name': row['column_name'],
                    'data_type': row['data_type'],
                    'character_maximum_length': row['character_maximum_length'] or '',
                    'is_nullable': row['is_nullable'],
                    'column_default': row['column_default'] or '',
                    'udt_name': row['udt_name']
                })
        
        print(f"✅ Schema exported successfully!")
        print(f"📄 File: {csv_filename}")
        print(f"\n🔧 Next step: Run generate_db_doc_from_csv.py to update DATABASE_SCHEMA.md")
        
    finally:
        await adapter.close()


if __name__ == '__main__':
    run_async(export_schema())
