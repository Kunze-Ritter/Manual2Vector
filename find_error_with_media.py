"""Find error codes that have both images and videos"""
import os
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

load_dotenv(Path(__file__).parent / '.env.database')

client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("Suche Fehlercodes mit Bildern UND Videos...\n")

# Get error codes with images (chunk_id not null)
errors_with_images = client.table('vw_error_codes').select(
    'error_code, error_description, manufacturer_id, chunk_id, document_id'
).not_.is_('chunk_id', 'null').limit(50).execute()

print(f"Fehlercodes mit Bildern: {len(errors_with_images.data)}")

# Check which manufacturers have videos
candidates = []

for error in errors_with_images.data:
    mfr_id = error.get('manufacturer_id')
    if not mfr_id:
        continue
    
    # Check for videos
    videos = client.table('vw_videos').select('id, title').eq(
        'manufacturer_id', mfr_id
    ).limit(1).execute()
    
    if videos.data:
        # Verify images exist
        chunk_id = error.get('chunk_id')
        images = client.table('vw_images').select('id, image_url').eq(
            'chunk_id', chunk_id
        ).limit(1).execute()
        
        if images.data:
            candidates.append({
                'error': error,
                'video_count': len(videos.data),
                'image_count': len(images.data)
            })

print(f"Fehlercodes mit Bildern UND Videos: {len(candidates)}\n")

# Show top 5
for i, candidate in enumerate(candidates[:5], 1):
    error = candidate['error']
    code = error.get('error_code')
    desc = error.get('error_description', 'N/A')
    
    print(f"{i}. 🎯 {code}")
    print(f"   📝 {desc[:80]}")
    print(f"   🖼️  {candidate['image_count']} Bilder")
    print(f"   🎥 {candidate['video_count']}+ Videos verfügbar")
    
    # Get manufacturer name
    mfr_id = error.get('manufacturer_id')
    if mfr_id:
        mfr = client.table('vw_manufacturers').select('name').eq('id', mfr_id).limit(1).execute()
        if mfr.data:
            print(f"   🏢 {mfr.data[0].get('name')}")
    print()
