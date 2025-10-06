#!/usr/bin/env python3
"""Check if images are in database"""

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

DOC_ID = '89387251-6506-4c41-ac7c-53666e82d457'

print("=" * 80)
print("IMAGE EXTRACTION CHECK")
print("=" * 80)

# Check images
images = supabase.table('images').select('*').eq('document_id', DOC_ID).execute()
print(f"\n📸 IMAGES: {len(images.data)} found")

if images.data:
    print("\nSample images:")
    for img in images.data[:5]:
        page = img.get('page_number', 'N/A')
        storage_url = img.get('storage_url', 'N/A')
        has_ocr = bool(img.get('ocr_text'))
        has_ai = bool(img.get('ai_description'))
        print(f"  Page {page}: {storage_url[:50]}...")
        print(f"    OCR: {'✅' if has_ocr else '❌'} | AI: {'✅' if has_ai else '❌'}")
else:
    print("  ❌ No images found!")
    print("\n  Possible reasons:")
    print("  1. Image extraction disabled")
    print("  2. PDF has no images")
    print("  3. Processing not complete")

# Check error codes with images
error_codes = supabase.table('error_codes').select('error_code, image_id, page_number').eq('document_id', DOC_ID).execute()
with_images = [ec for ec in error_codes.data if ec.get('image_id')]
without_images = [ec for ec in error_codes.data if not ec.get('image_id')]

print(f"\n🔴 ERROR CODES:")
print(f"  Total: {len(error_codes.data)}")
print(f"  With image_id: {len(with_images)}")
print(f"  Without image_id: {len(without_images)}")

if with_images:
    print(f"\n  Sample with images:")
    for ec in with_images[:3]:
        print(f"    {ec['error_code']} (page {ec['page_number']}): {ec['image_id'][:8]}...")

print("\n" + "=" * 80)
