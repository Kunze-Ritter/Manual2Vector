"""
Delete all Konica Minolta data from database before reprocessing
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env.database')

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

print("="*60)
print("DELETING KONICA MINOLTA DATA")
print("="*60)

# Get Konica Minolta manufacturer ID
mfr_result = supabase.table('manufacturers').select('id, name').ilike('name', '%Konica%').execute()

if not mfr_result.data:
    print("\n❌ Konica Minolta manufacturer not found!")
    exit(1)

manufacturer_id = mfr_result.data[0]['id']
manufacturer_name = mfr_result.data[0]['name']

print(f"\nManufacturer: {manufacturer_name}")
print(f"ID: {manufacturer_id}")

# Get all Konica Minolta documents
docs_result = supabase.table('documents').select('id, filename').eq('manufacturer_id', manufacturer_id).execute()

print(f"\nFound {len(docs_result.data)} documents")

if not docs_result.data:
    print("\n✅ No documents to delete")
    exit(0)

# Show documents
print("\nDocuments to delete:")
for doc in docs_result.data:
    print(f"  - {doc['filename']}")

# Ask for confirmation
print("\n" + "="*60)
response = input("Delete all Konica Minolta data? (yes/no): ")

if response.lower() != 'yes':
    print("\n❌ Cancelled")
    exit(0)

print("\n" + "="*60)
print("DELETING DATA...")
print("="*60)

document_ids = [doc['id'] for doc in docs_result.data]

# Delete in correct order (foreign key constraints)

# 1. Delete error codes
print("\n1. Deleting error codes...")
result = supabase.table('error_codes').delete().in_('document_id', document_ids).execute()
print(f"   ✅ Deleted error codes")

# 2. Delete chunks
print("\n2. Deleting chunks...")
result = supabase.table('chunks').delete().in_('document_id', document_ids).execute()
print(f"   ✅ Deleted chunks")

# 3. Delete products
print("\n3. Deleting products...")
result = supabase.table('products').delete().eq('manufacturer_id', manufacturer_id).execute()
print(f"   ✅ Deleted products")

# 4. Delete product series
print("\n4. Deleting product series...")
result = supabase.table('product_series').delete().eq('manufacturer_id', manufacturer_id).execute()
print(f"   ✅ Deleted product series")

# 5. Delete documents
print("\n5. Deleting documents...")
result = supabase.table('documents').delete().in_('id', document_ids).execute()
print(f"   ✅ Deleted documents")

print("\n" + "="*60)
print("✅ ALL KONICA MINOLTA DATA DELETED")
print("="*60)
print("\nYou can now reprocess the PDFs with the improved extractor!")
