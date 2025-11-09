"""Check if 66.60.32 has images"""

import os

from supabase import create_client

from scripts._env import load_env

load_env(extra_files=['.env.database'])
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

code = "66.60.32"

# Get error code
error = client.table('vw_error_codes').select(
    'error_code, error_description, chunk_id, manufacturer_id, document_id'
).ilike('error_code', f'*{code}*').execute()

print(f"Fehlercode: {code}")
print(f"Gefunden: {len(error.data)} Einträge\n")

if error.data:
    for e in error.data:
        print(f"Error Code: {e.get('error_code')}")
        print(f"Description: {e.get('error_description')}")
        print(f"Chunk ID: {e.get('chunk_id')}")
        print(f"Manufacturer ID: {e.get('manufacturer_id')}")
        print(f"Document ID: {e.get('document_id')}")
        
        chunk_id = e.get('chunk_id')
        if chunk_id:
            print(f"\n🔍 Suche Bilder für chunk_id: {chunk_id}")
            
            # Check images
            images = client.table('vw_images').select(
                'id, storage_url, ai_description, manual_description, image_type'
            ).eq('chunk_id', chunk_id).execute()
            
            print(f"Gefundene Bilder: {len(images.data)}\n")
            
            for img in images.data:
                print(f"  📷 Image ID: {img.get('id')}")
                print(f"     URL: {img.get('storage_url')}")
                print(f"     Type: {img.get('image_type')}")
                print(f"     AI Desc: {img.get('ai_description', 'N/A')[:60]}")
                print(f"     Manual Desc: {img.get('manual_description', 'N/A')[:60]}")
                print()
        else:
            print("❌ Kein chunk_id - keine Bilder möglich!")
        print()
else:
    print("❌ Fehlercode nicht gefunden!")
