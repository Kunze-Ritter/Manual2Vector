"""Check if videos exist for HP X580"""
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
print("🔍 CHECKING VIDEOS FOR HP X580")
print("=" * 80)

# Check total videos
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/vw_videos",
    headers=headers,
    params={
        "select": "title,platform,video_url",
        "limit": 10
    }
)

if response.status_code == 200:
    videos = response.json()
    print(f"\n✅ Total videos in DB: {len(videos)}\n")
    
    if videos:
        print("Sample videos:")
        for video in videos[:5]:
            print(f"  - {video.get('title')[:60]} [{video.get('platform', 'N/A')}]")
    else:
        print("❌ No videos in database yet!")
        print("\nYou need to:")
        print("1. Upload videos to the database")
        print("2. Use the /content/videos/upload endpoint")
        print("3. Or import from YouTube API")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)

# Search for X580 specifically
print("\n" + "=" * 80)
print("🔍 SEARCHING FOR 'X580' VIDEOS")
print("=" * 80)

response = requests.get(
    f"{SUPABASE_URL}/rest/v1/vw_videos",
    headers=headers,
    params={
        "select": "title,video_url,platform",
        "or": "(title.ilike.*X580*,description.ilike.*X580*)",
        "limit": 5
    }
)

if response.status_code == 200:
    videos = response.json()
    print(f"\n✅ Found {len(videos)} videos matching 'X580'\n")
    
    for video in videos:
        print(f"Title: {video.get('title')}")
        print(f"URL: {video.get('video_url')}")
        print(f"Platform: {video.get('platform', 'N/A')}")
        print()
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
