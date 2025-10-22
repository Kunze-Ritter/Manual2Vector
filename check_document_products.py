import os
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

load_dotenv(Path('.env.database'))
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

# Check document_products
doc_products = client.table('vw_document_products').select('*').limit(10).execute()
print(f"document_products: {len(doc_products.data)} entries")

if doc_products.data:
    for dp in doc_products.data[:3]:
        print(f"  - Document: {dp.get('document_id')[:8]}... → Product: {dp.get('product_id')[:8]}...")

# Check products
products = client.table('vw_products').select('id, model_number, manufacturer_id').limit(10).execute()
print(f"\nproducts: {len(products.data)} entries")

if products.data:
    for p in products.data[:3]:
        print(f"  - {p.get('model_number')} (mfr: {p.get('manufacturer_id')[:8] if p.get('manufacturer_id') else 'None'}...)")
