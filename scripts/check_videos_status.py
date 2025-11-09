"""Check video enrichment status"""

import os

from supabase import create_client

from scripts._env import load_env

load_env()
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("📊 Video Enrichment Status\n")

# Check video links
links = client.table('vw_links').select('id, url, link_type, video_id').in_(
    'link_type', ['video', 'youtube', 'vimeo', 'brightcove']
).execute()

total_links = len(links.data)
enriched = sum(1 for l in links.data if l.get('video_id'))
pending = total_links - enriched

print(f"Video Links:")
print(f"  Total: {total_links}")
print(f"  Enriched: {enriched} ✅")
print(f"  Pending: {pending} ⏳")
print(f"  Rate: {enriched/total_links*100:.1f}%" if total_links > 0 else "  Rate: N/A")

# Check videos table
videos = client.table('vw_videos').select('id, title, platform, youtube_id, manufacturer_id').execute()

print(f"\nVideos Table:")
print(f"  Total: {len(videos.data)}")

# Group by platform
platforms = {}
for v in videos.data:
    platform = v.get('platform', 'unknown')
    platforms[platform] = platforms.get(platform, 0) + 1

for platform, count in sorted(platforms.items(), key=lambda x: (x[0] is None, x[0])):
    print(f"  {platform or 'unknown'}: {count}")

# Check manufacturer linking
with_mfr = sum(1 for v in videos.data if v.get('manufacturer_id'))
print(f"\nManufacturer Linking:")
print(f"  With manufacturer_id: {with_mfr} ✅")
print(f"  Without manufacturer_id: {len(videos.data) - with_mfr} ❌")

# Show sample videos
print(f"\n📹 Sample Videos:")
for i, video in enumerate(videos.data[:5], 1):
    title = video.get('title', 'N/A')[:60]
    platform = video.get('platform', 'N/A')
    mfr_id = "✅" if video.get('manufacturer_id') else "❌"
    print(f"{i}. [{platform}] {title} (mfr: {mfr_id})")

# Show pending links
if pending > 0:
    print(f"\n⏳ Sample Pending Links:")
    pending_links = [l for l in links.data if not l.get('video_id')][:5]
    for i, link in enumerate(pending_links, 1):
        url = link.get('url', 'N/A')[:70]
        link_type = link.get('link_type', 'N/A')
        print(f"{i}. [{link_type}] {url}")

print(f"\n{'='*60}")
print(f"✅ Ready to run enrichment!" if pending > 0 else "✅ All videos enriched!")
