"""
Delete Documents by Manufacturer
==================================
Deletes ALL documents from a specific manufacturer or date range.

Useful for:
- Cleaning up after batch processing with wrong manufacturer detection
- Removing test data
- Clearing documents from a specific time period

Usage:
    # Delete all documents from wrong manufacturer
    python scripts/delete_by_manufacturer.py --manufacturer "Konica Minolta" --after "2025-10-11"
    
    # Dry run (show what would be deleted)
    python scripts/delete_by_manufacturer.py --manufacturer "Konica Minolta" --after "2025-10-11" --dry-run
    
    # Delete documents from today
    python scripts/delete_by_manufacturer.py --after "2025-10-11"
    
    # Interactive mode
    python scripts/delete_by_manufacturer.py --interactive
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent
env_files = ['.env', '.env.database']
for env_file in env_files:
    env_path = project_root / env_file
    if env_path.exists():
        load_dotenv(env_path, override=True)

# Initialize Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not found")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def find_documents(
    manufacturer: Optional[str] = None,
    after_date: Optional[str] = None,
    before_date: Optional[str] = None
) -> List[dict]:
    """Find documents matching criteria"""
    
    query = supabase.table('documents').select('id,filename,original_filename,manufacturer,created_at')
    
    if manufacturer:
        query = query.eq('manufacturer', manufacturer)
    
    if after_date:
        query = query.gte('created_at', after_date)
    
    if before_date:
        query = query.lte('created_at', before_date)
    
    result = query.order('created_at', desc=True).execute()
    return result.data if result.data else []


def delete_document_cascade(document_id: str) -> bool:
    """Delete document and all related data (CASCADE)"""
    try:
        # Delete in order (CASCADE will handle children)
        tables = [
            ('document_products', 'document_id'),
            ('chunks', 'document_id'),
            ('error_codes', 'document_id'),
            ('documents', 'id')
        ]
        
        for table, id_col in tables:
            supabase.table(table).delete().eq(id_col, document_id).execute()
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Delete documents by manufacturer/date')
    parser.add_argument('--manufacturer', help='Manufacturer name (e.g., "Konica Minolta")')
    parser.add_argument('--after', help='Delete documents after this date (YYYY-MM-DD)')
    parser.add_argument('--before', help='Delete documents before this date (YYYY-MM-DD)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    
    args = parser.parse_args()
    
    # Interactive mode
    if args.interactive or (not args.manufacturer and not args.after and not args.before):
        print("="*80)
        print("Delete Documents by Manufacturer/Date")
        print("="*80)
        
        print("\nRecent documents:")
        docs = find_documents()[:20]
        
        if not docs:
            print("❌ No documents found")
            return
        
        # Group by manufacturer
        by_mfr = {}
        for doc in docs:
            mfr = doc.get('manufacturer', 'Unknown')
            if mfr not in by_mfr:
                by_mfr[mfr] = []
            by_mfr[mfr].append(doc)
        
        print("\nDocuments by manufacturer:")
        for mfr, docs_list in sorted(by_mfr.items()):
            print(f"\n  {mfr}: {len(docs_list)} documents")
            for doc in docs_list[:3]:
                filename = doc.get('filename') or doc.get('original_filename', 'Unknown')
                created = doc.get('created_at', '')[:10]
                print(f"    - {filename[:50]} ({created})")
            if len(docs_list) > 3:
                print(f"    ... and {len(docs_list)-3} more")
        
        print("\nEnter manufacturer name to delete (or 'q' to quit):")
        mfr_input = input("> ").strip()
        
        if mfr_input.lower() == 'q':
            print("Cancelled.")
            return
        
        print("\nEnter date filter (YYYY-MM-DD) or press Enter for all:")
        date_input = input("After date (or Enter): ").strip()
        
        args.manufacturer = mfr_input
        args.after = date_input if date_input else None
    
    # Find matching documents
    print("\n" + "="*80)
    print("Searching for documents...")
    print("="*80)
    
    if args.manufacturer:
        print(f"  Manufacturer: {args.manufacturer}")
    if args.after:
        print(f"  After: {args.after}")
    if args.before:
        print(f"  Before: {args.before}")
    
    docs = find_documents(args.manufacturer, args.after, args.before)
    
    if not docs:
        print("\n❌ No documents found matching criteria")
        return
    
    print(f"\n✓ Found {len(docs)} documents:")
    print("-"*80)
    
    for doc in docs:
        filename = doc.get('filename') or doc.get('original_filename', 'Unknown')
        mfr = doc.get('manufacturer', 'Unknown')
        created = doc.get('created_at', '')[:19]
        print(f"  {filename[:45]:45} | {mfr:15} | {created}")
    
    if args.dry_run:
        print("\n✓ Dry run complete (no data deleted)")
        return
    
    # Confirm deletion
    print("\n" + "="*80)
    print(f"⚠️  WARNING: This will permanently delete {len(docs)} documents!")
    print("="*80)
    print("\nType 'DELETE' to confirm:")
    confirm = input("> ").strip()
    
    if confirm != 'DELETE':
        print("Cancelled.")
        return
    
    # Delete documents
    print("\n🗑️  Deleting documents...")
    success = 0
    
    for doc in docs:
        filename = doc.get('filename') or doc.get('original_filename', 'Unknown')
        print(f"  Deleting: {filename[:50]}...", end=' ')
        
        if delete_document_cascade(doc['id']):
            print("✓")
            success += 1
        else:
            print("✗")
    
    print("\n" + "="*80)
    print(f"✅ Successfully deleted {success}/{len(docs)} documents")
    print("="*80)


if __name__ == '__main__':
    main()
