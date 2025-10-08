"""Cleanup Duplicate Error Codes

Finds and removes duplicate error codes, keeping the newest one.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client

# Load environment
load_dotenv()


def find_duplicates():
    """Find duplicate error codes"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found in .env")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    print("🔍 Finding duplicate error codes...")
    print("=" * 80)
    
    # Get all error codes
    result = supabase.table('error_codes').select(
        'id, error_code, manufacturer_id, document_id, created_at'
    ).order('created_at', desc=False).execute()
    
    error_codes = result.data
    print(f"Total error codes in DB: {len(error_codes)}")
    
    # Group by unique key
    seen = {}
    duplicates = []
    
    for ec in error_codes:
        # Create key matching unique constraint
        key = (
            ec['error_code'],
            ec.get('manufacturer_id'),
            ec.get('document_id')
        )
        
        if key in seen:
            # This is a duplicate!
            duplicates.append({
                'id': ec['id'],
                'error_code': ec['error_code'],
                'created_at': ec['created_at'],
                'original_id': seen[key]['id'],
                'original_created_at': seen[key]['created_at']
            })
        else:
            seen[key] = ec
    
    print(f"\n📊 Found {len(duplicates)} duplicate error codes")
    
    if duplicates:
        print("\nDuplicates:")
        print("-" * 80)
        for dup in duplicates[:10]:  # Show first 10
            print(f"Error Code: {dup['error_code']}")
            print(f"  Original: {dup['original_id']} (created: {dup['original_created_at']})")
            print(f"  Duplicate: {dup['id']} (created: {dup['created_at']})")
            print()
        
        if len(duplicates) > 10:
            print(f"... and {len(duplicates) - 10} more")
    
    return duplicates, supabase


def delete_duplicates(duplicates, supabase):
    """Delete duplicate error codes"""
    if not duplicates:
        print("✅ No duplicates to delete")
        return
    
    print(f"\n🗑️  Deleting {len(duplicates)} duplicate error codes...")
    
    deleted_count = 0
    for dup in duplicates:
        try:
            supabase.table('error_codes').delete().eq('id', dup['id']).execute()
            deleted_count += 1
        except Exception as e:
            print(f"❌ Failed to delete {dup['id']}: {e}")
    
    print(f"✅ Deleted {deleted_count} duplicate error codes")


def main():
    """Run cleanup"""
    duplicates, supabase = find_duplicates()
    
    if duplicates:
        print("\n" + "=" * 80)
        response = input(f"Delete {len(duplicates)} duplicates? (yes/no): ")
        
        if response.lower() == 'yes':
            delete_duplicates(duplicates, supabase)
            print("\n✅ Cleanup complete!")
        else:
            print("❌ Cancelled")
    else:
        print("\n✅ No duplicates found!")


if __name__ == '__main__':
    main()
