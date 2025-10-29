"""Check all videos with details"""
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
print("🔍 ALL VIDEOS IN DATABASE")
print("=" * 80)

response = requests.get(
    f"{SUPABASE_URL}/rest/v1/vw_videos",
    headers=headers,
    params={
        "select": "title,platform,manufacturer_id,description",
        "limit": 10
    }
)

if response.status_code == 200:
    videos = response.json()
    print(f"\n✅ Total videos: {len(videos)}\n")
    
    for i, video in enumerate(videos, 1):
        print(f"Video #{i}:")
        print(f"  Title: {video.get('title')[:80]}")
        print(f"  Platform: {video.get('platform', 'N/A')}")
        print(f"  Manufacturer ID: {video.get('manufacturer_id', 'NULL')}")
        print(f"  Description: {video.get('description', 'N/A')[:100]}")
        print()
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
