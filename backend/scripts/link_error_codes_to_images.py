#!/usr/bin/env python3
"""
Link error codes to images using the new junction table

Matching strategies:
1. SMART: Vision AI description contains error code
2. PAGE: All images on same page as error code
3. CONTEXT: Images within ±2 pages of error code
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv
import re

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 80)
print("LINKING ERROR CODES TO IMAGES (MANY-TO-MANY)")
print("=" * 80)

# Get all error codes
print("\n1. Loading error codes...")
error_codes = supabase.table('vw_error_codes') \
    .select('id, error_code, page_number, document_id') \
    .execute()

print(f"   Found {len(error_codes.data)} error codes")

# Group by document
docs = {}
for ec in error_codes.data:
    doc_id = ec['document_id']
    if doc_id not in docs:
        docs[doc_id] = []
    docs[doc_id].append(ec)

print(f"   {len(docs)} documents to process")

total_links = 0
smart_matches = 0
page_matches = 0
context_matches = 0

for doc_id, codes in docs.items():
    print(f"\n2. Processing document: {doc_id[:8]}...")
    print(f"   Error codes: {len(codes)}")
    
    # Get all images for this document
    images = supabase.table('vw_images') \
        .select('id, page_number, ai_description, ocr_text') \
        .eq('document_id', doc_id) \
        .execute()
    
    print(f"   Images: {len(images.data)}")
    
    if not images.data:
        print("   ⚠️  No images found - skipping")
        continue
    
    # Build page -> images mapping
    page_images = {}
    for img in images.data:
        page = img['page_number']
        if page not in page_images:
            page_images[page] = []
        page_images[page].append(img)
    
    # Link each error code
    for ec in codes:
        error_code = ec['error_code']
        page_num = ec['page_number']
        error_code_id = ec['id']
        
        if not page_num:
            continue
        
        linked_images = []
        
        # STRATEGY 1: SMART MATCH - AI description contains error code
        for img in images.data:
            ai_desc = (img.get('ai_description') or '').lower()
            ocr_text = (img.get('ocr_text') or '').lower()
            
            # Check if error code appears in AI description or OCR
            error_variations = [
                error_code.lower(),
                error_code.replace('-', '').lower(),
                error_code.replace('.', '').lower(),
                error_code.replace(' ', '').lower()
            ]
            
            if any(var in ai_desc or var in ocr_text for var in error_variations):
                linked_images.append({
                    'image_id': img['id'],
                    'method': 'smart_vision_ai',
                    'confidence': 0.95,
                    'order': 0  # Most relevant
                })
                smart_matches += 1
        
        # STRATEGY 2: PAGE MATCH - Images on same page
        if page_num in page_images:
            for img in page_images[page_num]:
                # Skip if already added via smart match
                if not any(li['image_id'] == img['id'] for li in linked_images):
                    linked_images.append({
                        'image_id': img['id'],
                        'method': 'page_match',
                        'confidence': 0.7,
                        'order': 1
                    })
                    page_matches += 1
        
        # STRATEGY 3: CONTEXT MATCH - Images within ±2 pages
        for offset in [-2, -1, 1, 2]:
            context_page = page_num + offset
            if context_page in page_images:
                for img in page_images[context_page]:
                    # Skip if already added
                    if not any(li['image_id'] == img['id'] for li in linked_images):
                        linked_images.append({
                            'image_id': img['id'],
                            'method': 'context_match',
                            'confidence': 0.5,
                            'order': 2 + abs(offset)
                        })
                        context_matches += 1
        
        # Insert links into junction table
        for link in linked_images:
            try:
                supabase.table('error_code_images').insert({
                    'error_code_id': error_code_id,
                    'image_id': link['image_id'],
                    'match_method': link['method'],
                    'match_confidence': link['confidence'],
                    'display_order': link['order']
                }).execute()
                total_links += 1
            except Exception as e:
                # Skip duplicates
                if 'duplicate' not in str(e).lower():
                    print(f"      ⚠️  Failed to link: {e}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total links created: {total_links}")
print(f"  ✨ Smart matches (AI): {smart_matches}")
print(f"  📍 Page matches: {page_matches}")
print(f"  📄 Context matches (±2 pages): {context_matches}")
print("\n✅ Done!")
