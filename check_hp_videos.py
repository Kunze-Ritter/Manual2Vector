"""Check HP videos in database"""
import os
from dotenv import load_dotenv
from pathlib import Path
import requests

load_dotenv(Path(__file__).parent / '.env.database')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

print("=" * 80)
print("🔍 CHECKING HP VIDEOS")
print("=" * 80)

# First, get HP manufacturer ID
mfr_response = requests.get(
    f"{SUPABASE_URL}/rest/v1/vw_manufacturers",
    headers=headers,
    params={
        "select": "id,name",
        "name": "ilike.%HP%",
        "limit": 5
    }
)

if mfr_response.status_code == 200:
    manufacturers = mfr_response.json()
    print(f"\n✅ Found {len(manufacturers)} HP manufacturers:\n")
    
    for mfr in manufacturers:
        print(f"  - {mfr.get('name')} (ID: {mfr.get('id')})")
        
        # Get videos for this manufacturer
        video_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/vw_videos",
            headers=headers,
            params={
                "select": "title,platform,video_url",
                "manufacturer_id": f"eq.{mfr.get('id')}",
                "limit": 10
            }
        )
        
        if video_response.status_code == 200:
            videos = video_response.json()
            print(f"    Videos: {len(videos)}")
            for video in videos[:3]:
                print(f"      - {video.get('title')[:60]} [{video.get('platform', 'N/A')}]")
        print()
else:
    print(f"❌ Error: {mfr_response.status_code}")
    print(mfr_response.text)
