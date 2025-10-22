#!/usr/bin/env python3
"""
Fix videos with platform=NULL by detecting from youtube_id or video_url
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load env
load_dotenv(Path(__file__).parent.parent / '.env.database')

client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("🔧 Fixing videos with platform=NULL...\n")

# Get videos with NULL platform
videos = client.table('vw_videos').select('id, youtube_id, video_url, link_id').is_('platform', 'null').execute()

print(f"Videos with platform=NULL: {len(videos.data)}\n")

updated = 0

for video in videos.data:
    video_id = video.get('id')
    youtube_id = video.get('youtube_id')
    video_url = video.get('video_url')
    link_id = video.get('link_id')
    
    platform = None
    new_video_url = None
    
    # Strategy 1: Has youtube_id → YouTube
    if youtube_id:
        platform = 'youtube'
        new_video_url = f"https://www.youtube.com/watch?v={youtube_id}"
    
    # Strategy 2: Check link URL
    elif link_id:
        link = client.table('vw_links').select('url').eq('id', link_id).limit(1).execute()
        if link.data:
            url = link.data[0].get('url', '')
            if 'youtube.com' in url or 'youtu.be' in url:
                platform = 'youtube'
                new_video_url = url
            elif 'vimeo.com' in url:
                platform = 'vimeo'
                new_video_url = url
            elif 'brightcove' in url:
                platform = 'brightcove'
                new_video_url = url
    
    # Update if platform detected
    if platform:
        update_data = {'platform': platform}
        if new_video_url and not video_url:
            update_data['video_url'] = new_video_url
        
        client.schema('krai_content').table('videos').update(update_data).eq('id', video_id).execute()
        
        updated += 1
        print(f"✅ [{updated}] Set platform={platform}" + (f" and video_url" if new_video_url and not video_url else ""))

print(f"\n{'='*60}")
print(f"✅ Updated {updated}/{len(videos.data)} videos")
