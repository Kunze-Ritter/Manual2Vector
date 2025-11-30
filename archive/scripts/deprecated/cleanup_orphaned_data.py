"""
Cleanup Orphaned Data Script
=============================
Removes data that references non-existent documents (orphaned data).

This happens when documents are deleted but related data wasn't cleaned up.

Usage:
    python scripts/cleanup_orphaned_data.py [--dry-run]
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from supabase import create_client
from backend.processors.env_loader import load_all_env_files

# Load environment variables via centralized loader
print("Loading environment variables...")
loaded_env_files = load_all_env_files(project_root)
for env_file in loaded_env_files:
    print(f"  ✓ Loaded: {env_file}")

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n❌ Error: SUPABASE credentials not found")
    sys.exit(1)

print(f"✓ Connected to Supabase: {SUPABASE_URL}\n")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def find_orphaned_data():
    """Find all orphaned data (references non-existent documents)"""
    print("=" * 80)
    print("Finding Orphaned Data")
    print("=" * 80)
    
    orphans = {}
    
    # Tables to check
    tables_to_check = [
        ('error_codes', 'document_id'),
        ('chunks', 'document_id'),
        ('document_products', 'document_id')
    ]
    
    for table, doc_column in tables_to_check:
        print(f"\nChecking {table}...")
        
        try:
            # Get all unique document_ids from this table
            result = supabase.table(table).select(doc_column).execute()
            
            if not result.data:
                print(f"  ✓ No data in {table}")
                continue
            
            # Get unique document IDs
            doc_ids = set(row[doc_column] for row in result.data if row.get(doc_column))
            
            print(f"  Found {len(doc_ids)} unique document references")
            
            # Check which documents exist
            orphaned_ids = []
            for doc_id in doc_ids:
                doc_result = supabase.table('documents').select('id').eq('id', doc_id).execute()
                if not doc_result.data:
                    orphaned_ids.append(doc_id)
            
            if orphaned_ids:
                # Count orphaned rows
                orphaned_count = sum(1 for row in result.data if row.get(doc_column) in orphaned_ids)
                orphans[table] = {
                    'document_ids': orphaned_ids,
                    'count': orphaned_count
                }
                print(f"  ⚠️  Found {orphaned_count} orphaned rows referencing {len(orphaned_ids)} deleted documents")
            else:
                print(f"  ✓ No orphaned data")
        
        except Exception as e:
            print(f"  ❌ Error checking {table}: {e}")
    
    return orphans


def cleanup_orphaned_data(orphans, dry_run=False):
    """Delete orphaned data"""
    
    if not orphans:
        print("\n✅ No orphaned data found!")
        return
    
    print("\n" + "=" * 80)
    print(f"{'[DRY RUN] ' if dry_run else ''}Cleanup Summary")
    print("=" * 80)
    
    total_rows = sum(info['count'] for info in orphans.values())
    print(f"\nTotal orphaned rows to delete: {total_rows}")
    
    for table, info in orphans.items():
        print(f"  - {table}: {info['count']} rows")
    
    if dry_run:
        print("\n✓ Dry run complete (no data deleted)")
        return
    
    # Confirm
    print("\n⚠️  WARNING: This will permanently delete orphaned data!")
    confirm = input("Type 'DELETE' to confirm: ").strip()
    
    if confirm != 'DELETE':
        print("Cancelled.")
        return
    
    print("\n🗑️  Deleting orphaned data...")
    
    for table, info in orphans.items():
        try:
            deleted_count = 0
            for doc_id in info['document_ids']:
                result = supabase.table(table).delete().eq('document_id', doc_id).execute()
                deleted_count += len(result.data) if result.data else 0
            
            print(f"  ✓ Deleted {deleted_count} orphaned rows from {table}")
        
        except Exception as e:
            print(f"  ❌ Error deleting from {table}: {e}")
    
    print("\n✅ Cleanup complete!")


def main():
    """Main entry point"""
    dry_run = '--dry-run' in sys.argv
    
    # Find orphaned data
    orphans = find_orphaned_data()
    
    # Cleanup
    cleanup_orphaned_data(orphans, dry_run=dry_run)


if __name__ == '__main__':
    main()
