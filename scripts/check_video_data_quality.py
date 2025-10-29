"""Check video data quality"""
import os
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

load_dotenv(Path('.env.database'))
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("📊 Video Data Quality Check\n")

# Get all videos
videos = client.table('vw_videos').select('id, title, description, video_url, platform, youtube_id, manufacturer_id').execute()

total = len(videos.data)
with_description = sum(1 for v in videos.data if v.get('description'))
with_video_url = sum(1 for v in videos.data if v.get('video_url'))
with_youtube_id = sum(1 for v in videos.data if v.get('youtube_id'))
with_manufacturer = sum(1 for v in videos.data if v.get('manufacturer_id'))

print(f"Total Videos: {total}\n")
print(f"Data Completeness:")
print(f"  description:     {with_description}/{total} ({with_description/total*100:.1f}%)")
print(f"  video_url:       {with_video_url}/{total} ({with_video_url/total*100:.1f}%)")
print(f"  youtube_id:      {with_youtube_id}/{total} ({with_youtube_id/total*100:.1f}%)")
print(f"  manufacturer_id: {with_manufacturer}/{total} ({with_manufacturer/total*100:.1f}%)")

# Sample videos by platform
print(f"\n📹 Sample by Platform:")
platforms = {}
for v in videos.data:
    platform = v.get('platform') or 'unknown'
    if platform not in platforms:
        platforms[platform] = []
    platforms[platform].append(v)

for platform, vids in platforms.items():
    print(f"\n{platform.upper()} ({len(vids)} videos):")
    sample = vids[0]
    print(f"  Title: {sample.get('title', 'N/A')[:60]}")
    print(f"  Description: {'✅' if sample.get('description') else '❌'} ({len(sample.get('description', '')) if sample.get('description') else 0} chars)")
    print(f"  Video URL: {'✅' if sample.get('video_url') else '❌'}")
    print(f"  YouTube ID: {'✅' if sample.get('youtube_id') else '❌'}")
    print(f"  Manufacturer: {'✅' if sample.get('manufacturer_id') else '❌'}")

# Check links
print(f"\n🔗 Links Check:")
links = client.table('vw_links').select('id, url, link_type, manufacturer_id, document_id').in_(
    'link_type', ['video', 'youtube', 'vimeo']
).limit(10).execute()

with_mfr = sum(1 for l in links.data if l.get('manufacturer_id'))
with_doc = sum(1 for l in links.data if l.get('document_id'))

print(f"  Sample size: {len(links.data)}")
print(f"  With manufacturer_id: {with_mfr}/{len(links.data)}")
print(f"  With document_id: {with_doc}/{len(links.data)}")
