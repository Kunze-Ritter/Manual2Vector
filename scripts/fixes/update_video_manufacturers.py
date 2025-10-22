#!/usr/bin/env python3
"""
Update manufacturer_id for existing videos
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

print("🔧 Updating manufacturer_id for existing videos...\n")

# Get all videos without manufacturer_id
videos = client.table('vw_videos').select('id, title, link_id').is_('manufacturer_id', 'null').execute()

print(f"Videos without manufacturer_id: {len(videos.data)}\n")

updated = 0
from_document = 0
from_title = 0

for video in videos.data:
    video_id = video.get('id')
    title = video.get('title', '')
    link_id = video.get('link_id')
    
    manufacturer_id = None
    source = None
    
    # Strategy 1: Get from link → document
    if link_id:
        link = client.table('vw_links').select('document_id').eq('id', link_id).limit(1).execute()
        
        if link.data and link.data[0].get('document_id'):
            doc_id = link.data[0]['document_id']
            doc = client.table('vw_documents').select('manufacturer_id, manufacturer').eq('id', doc_id).limit(1).execute()
            
            if doc.data and doc.data[0].get('manufacturer_id'):
                manufacturer_id = doc.data[0]['manufacturer_id']
                source = f"document ({doc.data[0].get('manufacturer')})"
                from_document += 1
    
    # Strategy 2: Detect from title
    if not manufacturer_id and title:
        manufacturers = client.table('vw_manufacturers').select('id, name').execute()
        
        title_upper = title.upper()
        for mfr in manufacturers.data:
            mfr_name = mfr.get('name', '').upper()
            if mfr_name and mfr_name in title_upper:
                manufacturer_id = mfr['id']
                source = f"title ({mfr['name']})"
                from_title += 1
                break
    
    # Update if found
    if manufacturer_id:
        client.schema('krai_content').table('videos').update({
            'manufacturer_id': manufacturer_id
        }).eq('id', video_id).execute()
        
        updated += 1
        print(f"✅ [{updated}] {title[:60]} → {source}")

print(f"\n{'='*60}")
print(f"✅ Updated {updated}/{len(videos.data)} videos")
print(f"   From document: {from_document}")
print(f"   From title: {from_title}")
print(f"   Not found: {len(videos.data) - updated}")
