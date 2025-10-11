"""
Cleanup Orphaned Chunks
========================
Deletes chunks that reference non-existent documents.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv

# Load environment
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')
load_dotenv(project_root / '.env.database', override=True)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Supabase credentials not found")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# The document that was deleted
document_id = "b2eaba70-993b-4226-aba5-3c16f6b1127a"

print(f"Cleaning up orphaned chunks for document: {document_id}\n")

# Check if chunks exist
try:
    chunks_result = supabase.table('chunks').select('id', count='exact').eq('document_id', document_id).execute()
    chunk_count = chunks_result.count if hasattr(chunks_result, 'count') else len(chunks_result.data)
    
    print(f"Found {chunk_count} orphaned chunks")
    
    if chunk_count == 0:
        print("✅ No orphaned chunks found!")
        sys.exit(0)
    
    # Confirm deletion
    print(f"\n⚠️  This will delete {chunk_count} chunks")
    confirm = input("Type 'DELETE' to confirm: ").strip()
    
    if confirm != 'DELETE':
        print("Cancelled.")
        sys.exit(0)
    
    # Delete in batches (avoid timeout)
    batch_size = 100
    deleted_total = 0
    
    print(f"\n🗑️  Deleting in batches of {batch_size}...")
    
    while True:
        # Get batch of chunk IDs
        batch_result = supabase.table('chunks').select('id').eq('document_id', document_id).limit(batch_size).execute()
        
        if not batch_result.data:
            break
        
        # Delete batch
        chunk_ids = [chunk['id'] for chunk in batch_result.data]
        for chunk_id in chunk_ids:
            supabase.table('chunks').delete().eq('id', chunk_id).execute()
        
        deleted_total += len(chunk_ids)
        print(f"   ✓ Deleted {deleted_total}/{chunk_count} chunks...")
    
    print(f"\n✅ Successfully deleted {deleted_total} orphaned chunks!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
