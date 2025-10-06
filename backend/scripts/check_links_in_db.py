#!/usr/bin/env python3
"""Check links and videos in database"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 80)
print("LINKS & VIDEOS IN DATABASE")
print("=" * 80)

# Check links
links_result = supabase.table('links').select('*').limit(10).execute()
print(f"\n📎 LINKS: {len(links_result.data)} found")
if links_result.data:
    for i, link in enumerate(links_result.data, 1):
        url = link.get('url', 'N/A')
        page = link.get('page_number', 'N/A')
        link_type = link.get('link_type', 'N/A')
        print(f"{i}. {url[:70]}...")
        print(f"   Page: {page} | Type: {link_type}")
else:
    print("   ❌ No links found in database")

# Check videos
videos_result = supabase.table('videos').select('*').limit(10).execute()
print(f"\n🎥 VIDEOS: {len(videos_result.data)} found")
if videos_result.data:
    for i, video in enumerate(videos_result.data, 1):
        title = video.get('title', 'N/A')
        youtube_id = video.get('youtube_id', 'N/A')
        duration = video.get('duration_seconds', 0)
        views = video.get('view_count', 0)
        print(f"{i}. {title[:60]}...")
        print(f"   YouTube ID: {youtube_id} | Duration: {duration}s | Views: {views:,}")
else:
    print("   ❌ No videos found in database")

# Check recent documents
docs_result = supabase.table('documents').select('id, filename, created_at').order('created_at', desc=True).limit(5).execute()
print(f"\n📄 RECENT DOCUMENTS: {len(docs_result.data)}")
for i, doc in enumerate(docs_result.data, 1):
    doc_id = doc['id']
    filename = doc['filename']
    
    # Count links for this document
    doc_links = supabase.table('links').select('id').eq('document_id', doc_id).execute()
    link_count = len(doc_links.data)
    
    print(f"{i}. {filename}")
    print(f"   ID: {doc_id}")
    print(f"   Links: {link_count}")

print("\n" + "=" * 80)
