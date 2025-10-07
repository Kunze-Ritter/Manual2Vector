#!/usr/bin/env python3
"""Check videos in database"""

import os
import sys
from pathlib import Path
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client

# Load env
load_dotenv(Path(__file__).parent.parent / '.env')

# Connect
sb = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Get latest videos
result = sb.table('videos').select('*').order('created_at', desc=True).limit(5).execute()

print("\n" + "=" * 100)
print("LATEST 5 VIDEOS IN DATABASE")
print("=" * 100)

for i, video in enumerate(result.data, 1):
    print(f"\n{i}. {video.get('title', 'N/A')}")
    print(f"   ID: {video.get('id')}")
    print(f"   Platform: {video.get('platform')}")
    print(f"   Manufacturer ID: {video.get('manufacturer_id', 'N/A')}")
    print(f"   Duration: {video.get('duration')}s" if video.get('duration') else "   Duration: N/A")
    print(f"   Resolution: {video.get('metadata', {}).get('resolution', 'N/A')}")
    print(f"   File Size: {video.get('metadata', {}).get('file_size', 'N/A')}")
    print(f"   Models: {video.get('metadata', {}).get('models', [])}")
    thumbnail = video.get('thumbnail_url') or 'N/A'
    print(f"   Thumbnail: {thumbnail[:80] if len(thumbnail) > 80 else thumbnail}...")
    video_url = video.get('video_url') or 'N/A'
    print(f"   Video URL: {video_url[:80] if len(video_url) > 80 else video_url}...")
    print(f"   Created: {video.get('created_at')}")
    
    # Full metadata
    if video.get('metadata'):
        print(f"   Metadata:")
        for key, value in video.get('metadata', {}).items():
            print(f"      {key}: {value}")

print("\n" + "=" * 80)
print(f"TOTAL VIDEOS: {len(result.data)}")
print("=" * 80)

# Count by platform
platform_result = sb.table('videos').select('platform').execute()
platforms = {}
for v in platform_result.data:
    platform = v.get('platform', 'unknown')
    platforms[platform] = platforms.get(platform, 0) + 1

print("\nVIDEOS BY PLATFORM:")
for platform, count in sorted(platforms.items()):
    print(f"   {platform}: {count}")

# Count with manufacturer
with_manufacturer = sb.table('videos').select('id').not_.is_('manufacturer_id', 'null').execute()
print(f"\nVIDEOS WITH MANUFACTURER: {len(with_manufacturer.data)}")

# Count with thumbnail
with_thumbnail = sb.table('videos').select('id').not_.is_('thumbnail_url', 'null').execute()
print(f"VIDEOS WITH THUMBNAIL: {len(with_thumbnail.data)}")

print("\n" + "=" * 80)
