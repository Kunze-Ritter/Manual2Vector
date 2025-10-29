"""Find error codes with images where manufacturer has videos"""
import os
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

load_dotenv(Path(__file__).parent / '.env.database')

client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("Suche Fehlercodes mit Bildern + Hersteller mit Videos...\n")

# Get manufacturers with videos
mfrs_with_videos = client.table('vw_videos').select('manufacturer_id').execute()
mfr_ids = list(set([v['manufacturer_id'] for v in mfrs_with_videos.data if v.get('manufacturer_id')]))

print(f"Hersteller mit Videos: {len(mfr_ids)}")

# Get error codes with images from these manufacturers
candidates = []

for mfr_id in mfr_ids[:10]:  # Check first 10 manufacturers
    errors = client.table('vw_error_codes').select(
        'error_code, error_description, manufacturer_id, chunk_id'
    ).eq('manufacturer_id', mfr_id).not_.is_('chunk_id', 'null').limit(5).execute()
    
    for error in errors.data:
        chunk_id = error.get('chunk_id')
        
        # Check for images
        images = client.table('vw_images').select('id, image_url, caption').eq(
            'chunk_id', chunk_id
        ).execute()
        
        if images.data:
            # Get videos for this manufacturer
            videos = client.table('vw_videos').select('id, title, video_url').eq(
                'manufacturer_id', mfr_id
            ).limit(3).execute()
            
            candidates.append({
                'error': error,
                'images': images.data,
                'videos': videos.data,
                'mfr_id': mfr_id
            })

print(f"\nGefunden: {len(candidates)} Fehlercodes mit Bildern + Videos\n")

# Show top 3
for i, candidate in enumerate(candidates[:3], 1):
    error = candidate['error']
    code = error.get('error_code')
    desc = error.get('error_description', 'N/A')
    
    print(f"{i}. 🎯 **{code}**")
    print(f"   📝 {desc[:100]}")
    print(f"   🖼️  {len(candidate['images'])} Bilder")
    print(f"   🎥 {len(candidate['videos'])} Videos")
    
    # Get manufacturer name
    mfr_id = candidate['mfr_id']
    mfr = client.table('vw_manufacturers').select('name').eq('id', mfr_id).limit(1).execute()
    if mfr.data:
        print(f"   🏢 {mfr.data[0].get('name')}")
    
    # Show first image
    if candidate['images']:
        img = candidate['images'][0]
        print(f"   📷 {img.get('caption', 'Bild')[:60]}")
    
    # Show first video
    if candidate['videos']:
        vid = candidate['videos'][0]
        print(f"   🎬 {vid.get('title', 'Video')[:60]}")
    
    print()

if candidates:
    print(f"\n✅ Teste mit: '{candidates[0]['error']['error_code']}'")
