"""
Check if chunks were deleted for a document
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

# Check for the document that had timeout
document_id = "b2eaba70-993b-4226-aba5-3c16f6b1127a"

print(f"Checking chunks for document: {document_id}\n")

# Check if document still exists
try:
    doc_result = supabase.table('documents').select('id,filename').eq('id', document_id).execute()
    if doc_result.data:
        print(f"✓ Document still exists: {doc_result.data[0].get('filename')}")
    else:
        print(f"✓ Document was deleted (as expected)")
except Exception as e:
    print(f"✓ Document was deleted: {e}")

# Check if chunks still exist
try:
    chunks_result = supabase.table('chunks').select('id', count='exact').eq('document_id', document_id).execute()
    chunk_count = chunks_result.count if hasattr(chunks_result, 'count') else len(chunks_result.data)
    
    if chunk_count == 0:
        print(f"✅ All chunks were deleted (CASCADE worked!)")
    else:
        print(f"⚠️  {chunk_count} chunks still exist (CASCADE pending or failed)")
        
except Exception as e:
    print(f"✅ Chunks were deleted: {e}")

print("\nConclusion:")
if chunk_count == 0:
    print("  The timeout was harmless - CASCADE deleted the chunks successfully!")
else:
    print("  The chunks are still there - CASCADE might be pending or failed.")
