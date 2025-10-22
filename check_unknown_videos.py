import os
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

load_dotenv(Path('.env.database'))
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

# Get unknown platform videos
videos = client.table('vw_videos').select('id, title, video_url, youtube_id, platform, link_id').is_('platform', 'null').execute()

print(f"Videos with platform=NULL: {len(videos.data)}\n")

for i, video in enumerate(videos.data[:5], 1):
    print(f"{i}. {video.get('title', 'N/A')[:60]}")
    url = video.get('video_url') or 'N/A'
    print(f"   video_url: {url[:70] if url != 'N/A' else url}")
    print(f"   youtube_id: {video.get('youtube_id', 'N/A')}")
    print(f"   platform: {video.get('platform', 'NULL')}")
    
    # Get link
    if video.get('link_id'):
        link = client.table('vw_links').select('url, link_type').eq('id', video['link_id']).limit(1).execute()
        if link.data:
            print(f"   link_url: {link.data[0].get('url', 'N/A')[:70]}")
            print(f"   link_type: {link.data[0].get('link_type', 'N/A')}")
    print()
