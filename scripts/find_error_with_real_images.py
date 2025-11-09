"""Find error codes that REALLY have images"""
import os

from supabase import create_client

from scripts._env import load_env

load_env()
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("Suche Fehlercodes mit echten Bildern...\n")

# Get all images with chunk_id
images = client.table('vw_images').select('chunk_id').not_.is_('chunk_id', 'null').limit(100).execute()
chunk_ids_with_images = list(set([img['chunk_id'] for img in images.data if img.get('chunk_id')]))

print(f"Chunks mit Bildern: {len(chunk_ids_with_images)}\n")

# Find error codes with these chunk_ids
found = []
for chunk_id in chunk_ids_with_images[:20]:
    errors = client.table('vw_error_codes').select(
        'error_code, error_description, chunk_id'
    ).eq('chunk_id', chunk_id).execute()
    
    if errors.data:
        # Verify images exist
        imgs = client.table('vw_images').select('id, storage_url').eq('chunk_id', chunk_id).execute()
        if imgs.data:
            found.append({
                'error': errors.data[0],
                'image_count': len(imgs.data),
                'image_url': imgs.data[0].get('storage_url')
            })

print(f"Fehlercodes mit Bildern: {len(found)}\n")

for i, item in enumerate(found[:5], 1):
    error = item['error']
    code = error.get('error_code')
    desc = error.get('error_description', 'N/A')
    
    print(f"{i}. 🎯 **{code}**")
    print(f"   📝 {desc[:80]}")
    print(f"   🖼️  {item['image_count']} Bilder")
    print(f"   📷 {item['image_url'][:80]}...")
    print()

if found:
    print(f"\n✅ Teste mit: '{found[0]['error']['error_code']}'")
