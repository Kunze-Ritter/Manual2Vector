"""
Delete Document Data Script
============================
Deletes ALL data associated with one or more document IDs from Supabase.

This includes:
- Products
- Error Codes
- Parts
- Chunks
- Document Metadata
- All related junction tables

Usage:
    python scripts/delete_document_data.py <document_id1> [<document_id2> ...]
    
Examples:
    # Delete single document
    python scripts/delete_document_data.py f05a555b-626b-4e90-990e-f1108a43eccf
    
    # Delete multiple documents
    python scripts/delete_document_data.py f05a555b-626b-4e90-990e-f1108a43eccf 379da86a-7294-4692-99ef-8f34e8ad17ec
    
    # Interactive mode (prompts for confirmation)
    python scripts/delete_document_data.py --interactive
"""

import sys
import os
from pathlib import Path
from typing import List
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent

# Load all .env files in correct order
env_files = ['.env', '.env.database', '.env.storage', '.env.external', '.env.pipeline', '.env.ai']
print("Loading environment variables...")
for env_file in env_files:
    env_path = project_root / env_file
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"  ✓ Loaded: {env_file}")
    else:
        print(f"  ⚠️  Not found: {env_file}")

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
# Try both key names (SERVICE_KEY and SERVICE_ROLE_KEY)
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n❌ Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not found in environment")
    print("\nDebug info:")
    print(f"  SUPABASE_URL: {'SET' if SUPABASE_URL else 'NOT SET'}")
    print(f"  SUPABASE_SERVICE_KEY: {'SET' if os.getenv('SUPABASE_SERVICE_KEY') else 'NOT SET'}")
    print(f"  SUPABASE_SERVICE_ROLE_KEY: {'SET' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'NOT SET'}")
    print("\nMake sure .env.database exists with:")
    print("  SUPABASE_URL=https://...")
    print("  SUPABASE_SERVICE_KEY=eyJ... (or SUPABASE_SERVICE_ROLE_KEY)")
    sys.exit(1)

print(f"✓ Connected to Supabase: {SUPABASE_URL}")
print()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format"""
    try:
        UUID(uuid_string)
        return True
    except ValueError:
        return False


def get_document_info(document_id: str) -> dict:
    """Get document information"""
    try:
        result = supabase.table('documents').select('*').eq('id', document_id).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"❌ Error fetching document info: {e}")
        return None


def count_related_data(document_id: str) -> dict:
    """Count all related data for a document"""
    counts = {}
    
    # Tables with document_id column
    direct_tables = {
        'error_codes': 'error_codes',
        'chunks': 'chunks'
    }
    
    # Junction tables (many-to-many)
    junction_tables = {
        'document_products': 'document_products'
    }
    
    # Count direct tables
    for key, table in direct_tables.items():
        try:
            result = supabase.table(table).select('id', count='exact').eq('document_id', document_id).execute()
            counts[key] = result.count if hasattr(result, 'count') else len(result.data)
        except Exception as e:
            counts[key] = 0
            print(f"⚠️  Warning: Could not count {key}: {e}")
    
    # Count junction tables
    for key, table in junction_tables.items():
        try:
            result = supabase.table(table).select('id', count='exact').eq('document_id', document_id).execute()
            counts[key] = result.count if hasattr(result, 'count') else len(result.data)
        except Exception as e:
            counts[key] = 0
            print(f"⚠️  Warning: Could not count {key}: {e}")
    
    return counts


def delete_document_data(document_id: str, dry_run: bool = False) -> bool:
    """
    Delete all data associated with a document
    
    Args:
        document_id: UUID of document to delete
        dry_run: If True, only show what would be deleted
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing document: {document_id}")
    
    # Validate UUID
    if not validate_uuid(document_id):
        print(f"❌ Invalid UUID format: {document_id}")
        return False
    
    # Get document info
    doc_info = get_document_info(document_id)
    if not doc_info:
        print(f"❌ Document not found: {document_id}")
        return False
    
    print(f"📄 Document: {doc_info.get('filename', doc_info.get('original_filename', 'Unknown'))}")
    print(f"   Manufacturer: {doc_info.get('manufacturer', 'Unknown')}")
    print(f"   Uploaded: {doc_info.get('created_at', 'Unknown')}")
    
    # Count related data
    print("\n📊 Related data:")
    counts = count_related_data(document_id)
    total_items = sum(counts.values())
    
    for table, count in counts.items():
        if count > 0:
            print(f"   - {table}: {count} items")
    
    print(f"\n   Total items to delete: {total_items}")
    
    if dry_run:
        print("\n✓ Dry run complete (no data deleted)")
        return True
    
    # Delete data in correct order (children first, then parent)
    # Based on actual DB schema with CASCADE deletes
    deletion_order = [
        # Junction tables first (many-to-many)
        ('document_products', 'document_id'),
        # Child tables with document_id
        ('chunks', 'document_id'),
        ('error_codes', 'document_id'),
        # Parent table last (CASCADE will handle orphans)
        ('documents', 'id')
    ]
    
    print("\n🗑️  Deleting data...")
    
    for table, id_column in deletion_order:
        try:
            result = supabase.table(table).delete().eq(id_column, document_id).execute()
            
            deleted_count = len(result.data) if result.data else 0
            if deleted_count > 0:
                print(f"   ✓ Deleted {deleted_count} items from {table}")
        
        except Exception as e:
            print(f"   ⚠️  Error deleting from {table}: {e}")
    
    print(f"\n✅ Successfully deleted all data for document: {document_id}")
    return True


def interactive_mode():
    """Interactive mode with document selection"""
    print("=" * 80)
    print("Interactive Document Deletion")
    print("=" * 80)
    
    # List recent documents (last session = last 50 or today)
    try:
        result = supabase.table('documents').select('id,filename,original_filename,manufacturer,created_at').order('created_at', desc=True).limit(50).execute()
        
        if not result.data:
            print("\n❌ No documents found in database")
            return
        
        print(f"\nRecent documents (last {len(result.data)}):")
        print("-" * 80)
        for idx, doc in enumerate(result.data, 1):
            filename = doc.get('filename') or doc.get('original_filename', 'Unknown')
            manufacturer = doc.get('manufacturer', 'Unknown')
            created = doc.get('created_at', 'Unknown')[:19] if doc.get('created_at') else 'Unknown'
            print(f"{idx:2}. {filename[:45]:45} | {manufacturer:15} | {created}")
            print(f"    ID: {doc['id']}")
        
        print("\n" + "=" * 80)
        print("Options:")
        print("  - Enter numbers (comma-separated): 1,2,3")
        print("  - Enter range: 1-20")
        print("  - Enter 'all' to delete all listed documents")
        print("  - Enter 'q' to quit")
        print("=" * 80)
        user_input = input("\nYour selection: ").strip()
        
        if user_input.lower() == 'q':
            print("Cancelled.")
            return
        
        # Parse selection
        try:
            if user_input.lower() == 'all':
                # Select all documents
                selected_docs = result.data
            elif '-' in user_input and ',' not in user_input:
                # Range selection (e.g., "1-20")
                start, end = user_input.split('-')
                start_idx = int(start.strip())
                end_idx = int(end.strip())
                selected_docs = result.data[start_idx-1:end_idx]
            else:
                # Comma-separated numbers
                indices = [int(x.strip()) for x in user_input.split(',')]
                selected_docs = [result.data[i-1] for i in indices if 1 <= i <= len(result.data)]
        except (ValueError, IndexError) as e:
            print(f"❌ Invalid selection: {e}")
            return
        
        if not selected_docs:
            print("❌ No valid documents selected")
            return
        
        # Show summary
        print("\n" + "=" * 80)
        print("Documents to delete:")
        for doc in selected_docs:
            filename = doc.get('filename') or doc.get('original_filename', 'Unknown')
            print(f"  - {filename} ({doc['id']})")
        
        # Confirm
        print("\n⚠️  WARNING: This will permanently delete all data for these documents!")
        confirm = input("Type 'DELETE' to confirm: ").strip()
        
        if confirm != 'DELETE':
            print("Cancelled.")
            return
        
        # Delete documents
        for doc in selected_docs:
            delete_document_data(doc['id'], dry_run=False)
    
    except Exception as e:
        print(f"❌ Error in interactive mode: {e}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nNo arguments provided. Starting interactive mode...\n")
        interactive_mode()
        return
    
    # Parse arguments
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    interactive = '--interactive' in args
    
    if interactive:
        interactive_mode()
        return
    
    # Remove flags from document IDs
    document_ids = [arg for arg in args if not arg.startswith('--')]
    
    if not document_ids:
        print("❌ No document IDs provided")
        print(__doc__)
        sys.exit(1)
    
    print("=" * 80)
    print(f"Document Data Deletion {'(DRY RUN)' if dry_run else ''}")
    print("=" * 80)
    
    # Process each document
    success_count = 0
    for doc_id in document_ids:
        if delete_document_data(doc_id, dry_run=dry_run):
            success_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print(f"Summary: {success_count}/{len(document_ids)} documents processed successfully")
    print("=" * 80)


if __name__ == '__main__':
    main()
