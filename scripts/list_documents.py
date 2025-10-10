"""
List All Documents
==================
Shows all documents in the database with their data counts.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent
env_files = ['.env', '.env.database', '.env.storage', '.env.external', '.env.pipeline', '.env.ai']
for env_file in env_files:
    env_path = project_root / env_file
    if env_path.exists():
        load_dotenv(env_path, override=True)

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE credentials not found")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def list_all_documents():
    """List all documents with their data counts"""
    print("=" * 100)
    print("All Documents in Database")
    print("=" * 100)
    
    # Get all documents
    result = supabase.table('documents').select('id,filename,original_filename,manufacturer,created_at').order('created_at', desc=True).execute()
    
    if not result.data:
        print("\n❌ No documents found in database!")
        return
    
    print(f"\nFound {len(result.data)} documents:\n")
    
    for idx, doc in enumerate(result.data, 1):
        doc_id = doc['id']
        filename = doc.get('filename') or doc.get('original_filename', 'Unknown')
        manufacturer = doc.get('manufacturer', 'Unknown')
        created = doc.get('created_at', 'Unknown')[:19] if doc.get('created_at') else 'Unknown'
        
        print(f"{idx}. {filename}")
        print(f"   ID: {doc_id}")
        print(f"   Manufacturer: {manufacturer}")
        print(f"   Created: {created}")
        
        # Count related data
        try:
            # Error codes
            ec_result = supabase.table('error_codes').select('id', count='exact').eq('document_id', doc_id).execute()
            ec_count = ec_result.count if hasattr(ec_result, 'count') else len(ec_result.data)
            
            # Chunks
            chunk_result = supabase.table('chunks').select('id', count='exact').eq('document_id', doc_id).execute()
            chunk_count = chunk_result.count if hasattr(chunk_result, 'count') else len(chunk_result.data)
            
            # Products (via junction)
            prod_result = supabase.table('document_products').select('id', count='exact').eq('document_id', doc_id).execute()
            prod_count = prod_result.count if hasattr(prod_result, 'count') else len(prod_result.data)
            
            print(f"   Data: {ec_count} error codes, {chunk_count} chunks, {prod_count} products")
        except Exception as e:
            print(f"   ⚠️  Could not count data: {e}")
        
        print()


if __name__ == '__main__':
    list_all_documents()
