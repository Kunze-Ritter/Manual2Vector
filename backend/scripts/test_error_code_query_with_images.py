#!/usr/bin/env python3
"""Test the new error code query with multiple images"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 80)
print("TEST: Error Code Query with Multiple Images")
print("=" * 80)

# Test error code (pick one that should have images)
test_code = input("\nEnter error code to test (or press Enter for '10.99.31'): ").strip() or "10.99.31"

print(f"\n🔍 Searching for: {test_code}")
print("-" * 80)

# Execute the query
query = f"""
SELECT 
  ec.error_code,
  ec.error_description,
  ec.solution_text,
  ec.severity_level,
  ec.requires_technician,
  ec.confidence_score,
  ec.page_number,
  COALESCE(c.text_chunk, '') as context_text,
  COALESCE(d.filename, '') as document_name,
  COALESCE(d.manufacturer, m.name, '') as manufacturer,
  COALESCE(d.series, '') as series,
  ec.created_at,
  -- Multiple images via junction table
  COALESCE(
    json_agg(
      json_build_object(
        'url', i.storage_url,
        'description', COALESCE(i.ai_description, ''),
        'ocr_text', COALESCE(i.ocr_text, ''),
        'match_method', eci.match_method,
        'confidence', eci.match_confidence,
        'page_number', i.page_number
      ) ORDER BY eci.display_order
    ) FILTER (WHERE i.id IS NOT NULL),
    '[]'::json
  ) as images
FROM krai_intelligence.error_codes ec
LEFT JOIN krai_intelligence.chunks c ON ec.chunk_id = c.id
LEFT JOIN krai_intelligence.error_code_images eci ON ec.id = eci.error_code_id
LEFT JOIN krai_content.images i ON eci.image_id = i.id
LEFT JOIN krai_core.documents d ON ec.document_id = d.id
LEFT JOIN krai_core.manufacturers m ON ec.manufacturer_id = m.id
WHERE UPPER(TRIM(ec.error_code)) = UPPER(TRIM('{test_code}'))
GROUP BY ec.id, ec.error_code, ec.error_description, ec.solution_text, 
         ec.severity_level, ec.requires_technician, ec.confidence_score, 
         ec.page_number, c.text_chunk, d.filename, d.manufacturer, 
         m.name, d.series, ec.created_at
LIMIT 1
"""

try:
    result = supabase.rpc('execute_sql', {'sql_text': query}).execute()
    
    if not result.data or len(result.data) == 0:
        print(f"\n❌ Error code '{test_code}' not found!")
        sys.exit(0)
    
    item = result.data[0]
    
    print(f"\n✅ Found: {item['error_code']}")
    print(f"\n📝 Description: {item.get('error_description', 'N/A')}")
    print(f"\n📄 Document: {item.get('document_name', 'N/A')}")
    print(f"🏭 Manufacturer: {item.get('manufacturer', 'N/A')}")
    print(f"📄 Page: {item.get('page_number', 'N/A')}")
    
    # Parse images
    images = item.get('images', [])
    if isinstance(images, str):
        images = json.loads(images)
    
    print(f"\n🖼️ IMAGES: {len(images)}")
    
    if images:
        for idx, img in enumerate(images, 1):
            print(f"\n  {idx}. {img.get('url', 'N/A')[:60]}...")
            print(f"     Page: {img.get('page_number', 'N/A')}")
            print(f"     Method: {img.get('match_method', 'N/A')}")
            print(f"     Confidence: {img.get('confidence', 0):.2f}")
            
            if img.get('description'):
                print(f"     AI: {img['description'][:80]}...")
            
            if img.get('ocr_text'):
                print(f"     OCR: {img['ocr_text'][:80]}...")
    else:
        print("  ⚠️  No images linked to this error code")
    
    # Show solution preview
    if item.get('solution_text'):
        solution = item['solution_text']
        lines = solution.split('\n')[:3]
        print(f"\n🔧 SOLUTION (preview):")
        for line in lines:
            if line.strip():
                print(f"  {line[:70]}")
        if len(solution.split('\n')) > 3:
            print("  ...")
    
    # Show context preview
    if item.get('context_text'):
        context = item['context_text'][:200]
        print(f"\n📄 CONTEXT (preview):")
        print(f"  {context}...")
    
    print("\n" + "=" * 80)
    print("✅ Query working! Multiple images supported!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ Query failed: {e}")
    import traceback
    traceback.print_exc()
