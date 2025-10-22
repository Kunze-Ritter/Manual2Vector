#!/usr/bin/env python3
"""
Link videos to products based on:
1. Document → Products (via document_id)
2. Video title (extract model numbers)
"""

import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load env
load_dotenv(Path(__file__).parent.parent / '.env.database')

client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("🔗 Linking videos to products...\n")

# Get all videos
videos = client.table('vw_videos').select('id, title, document_id, manufacturer_id, link_id').execute()

print(f"Total videos: {len(videos.data)}\n")

linked_count = 0
from_document = 0
from_title = 0

# Common model patterns
MODEL_PATTERNS = [
    r'\b[A-Z]{1,3}\d{3,4}[A-Z]?\b',  # E.g., E877, M404, C308
    r'\b[A-Z]+-\d{3,4}\b',            # E.g., HP-404
    r'\bLaserJet\s+Pro\s+[A-Z]?\d{3,4}\b',  # LaserJet Pro M404
]

for video in videos.data:
    video_id = video.get('id')
    title = video.get('title', '')
    document_id = video.get('document_id')
    manufacturer_id = video.get('manufacturer_id')
    
    product_ids = set()
    
    # Strategy 1: Get products from document
    if document_id:
        doc_products = client.table('vw_document_products').select('product_id').eq(
            'document_id', document_id
        ).execute()
        
        if doc_products.data:
            for dp in doc_products.data:
                product_ids.add(dp['product_id'])
            from_document += 1
    
    # Strategy 2: Extract model numbers from title
    if title and manufacturer_id:
        # Extract potential model numbers
        models_found = []
        for pattern in MODEL_PATTERNS:
            matches = re.findall(pattern, title)
            models_found.extend(matches)
        
        if models_found:
            # Search for products with these model numbers
            for model in models_found:
                products = client.table('vw_products').select('id').eq(
                    'manufacturer_id', manufacturer_id
                ).ilike('model_number', f'*{model}*').execute()
                
                if products.data:
                    for p in products.data:
                        product_ids.add(p['id'])
                    from_title += 1
                    break  # Only count once per video
    
    # Link video to products
    if product_ids:
        for product_id in product_ids:
            # Check if link already exists
            existing = client.schema('krai_content').table('video_products').select('id').eq(
                'video_id', video_id
            ).eq('product_id', product_id).execute()
            
            if not existing.data:
                # Create link
                client.schema('krai_content').table('video_products').insert({
                    'video_id': video_id,
                    'product_id': product_id
                }).execute()
        
        linked_count += 1
        print(f"✅ [{linked_count}] {title[:60]} → {len(product_ids)} products")

print(f"\n{'='*60}")
print(f"✅ Linked {linked_count}/{len(videos.data)} videos to products")
print(f"   From document: {from_document}")
print(f"   From title: {from_title}")
print(f"   Not linked: {len(videos.data) - linked_count}")

# Show stats
stats = client.schema('krai_content').table('video_products').select('id', count='exact').execute()
print(f"\n📊 Total video-product links: {stats.count}")
