"""Check if error code exists in database"""
import os
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

load_dotenv(Path(__file__).parent / '.env.database')

client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Search for error code
code = "66.60.30"
result = client.table('vw_error_codes').select(
    'error_code, error_description, manufacturer_id, document_id, page_number, chunk_id'
).ilike('error_code', f'*{code}*').execute()

print(f"Suche nach Fehlercode: {code}")
print(f"Gefunden: {len(result.data)} Ergebnisse\n")

for i, error in enumerate(result.data[:3], 1):
    print(f"{i}. {error.get('error_code')}")
    print(f"   Beschreibung: {error.get('error_description', 'N/A')}")
    print(f"   Document ID: {error.get('document_id')}")
    print(f"   Seite: {error.get('page_number')}")
    print(f"   Chunk ID: {error.get('chunk_id')}")
    print()

# Check for images
if result.data:
    first_error = result.data[0]
    chunk_id = first_error.get('chunk_id')
    
    if chunk_id:
        print(f"Prüfe Bilder für Chunk ID: {chunk_id}")
        images = client.table('vw_images').select(
            'image_url, image_type, page_number, caption'
        ).eq('chunk_id', chunk_id).execute()
        
        print(f"Gefundene Bilder: {len(images.data)}\n")
        for img in images.data:
            print(f"  - {img.get('image_type')}: {img.get('image_url')}")
            print(f"    Caption: {img.get('caption', 'N/A')}")
            print()
