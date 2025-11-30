import os

from supabase import create_client

from scripts._env import load_env

load_env()
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

# Get sample videos with document_id
videos = client.table('vw_videos').select('id, title, document_id').not_.is_('document_id', 'null').limit(5).execute()

print(f"Videos with document_id: {len(videos.data)}\n")

for video in videos.data:
    doc_id = video.get('document_id')
    title = video.get('title', 'N/A')[:60]
    
    print(f"Video: {title}")
    print(f"  document_id: {doc_id}")
    
    # Check if document has products
    doc_products = client.table('vw_document_products').select('product_id').eq('document_id', doc_id).execute()
    
    print(f"  Products: {len(doc_products.data)}")
    
    if doc_products.data:
        for dp in doc_products.data[:3]:
            # Get product details
            product = client.table('vw_products').select('model_number').eq('id', dp['product_id']).limit(1).execute()
            if product.data:
                print(f"    - {product.data[0].get('model_number')}")
    print()
