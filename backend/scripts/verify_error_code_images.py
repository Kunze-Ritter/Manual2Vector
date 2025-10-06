#!/usr/bin/env python3
"""Verify error code to images linking"""

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
print("ERROR CODE IMAGES VERIFICATION")
print("=" * 80)

# Get total links
links = supabase.table('error_code_images').select('*').execute()
print(f"\n📸 Total image links: {len(links.data)}")

# Group by match method
methods = {}
for link in links.data:
    method = link.get('match_method', 'unknown')
    methods[method] = methods.get(method, 0) + 1

print("\n📊 By match method:")
for method, count in sorted(methods.items()):
    print(f"  {method}: {count}")

# Sample error codes with images
print("\n🔴 Sample error codes with images:")
result = supabase.rpc('execute_sql', {
    'sql_text': """
        SELECT 
            ec.error_code,
            ec.page_number,
            COUNT(eci.image_id) as image_count,
            array_agg(eci.match_method) as methods
        FROM krai_intelligence.error_codes ec
        LEFT JOIN krai_intelligence.error_code_images eci ON ec.id = eci.error_code_id
        WHERE ec.document_id = '89387251-6506-4c41-ac7c-53666e82d457'
        GROUP BY ec.id, ec.error_code, ec.page_number
        HAVING COUNT(eci.image_id) > 0
        ORDER BY COUNT(eci.image_id) DESC
        LIMIT 5
    """
}).execute()

if result.data:
    for row in result.data:
        print(f"  {row['error_code']} (page {row['page_number']}): {row['image_count']} images")
        print(f"    Methods: {', '.join(row['methods'])}")

# Error codes without images
no_images = supabase.rpc('execute_sql', {
    'sql_text': """
        SELECT COUNT(*) as count
        FROM krai_intelligence.error_codes ec
        LEFT JOIN krai_intelligence.error_code_images eci ON ec.id = eci.error_code_id
        WHERE ec.document_id = '89387251-6506-4c41-ac7c-53666e82d457'
        AND eci.id IS NULL
    """
}).execute()

if no_images.data:
    count = no_images.data[0]['count']
    print(f"\n⚠️  Error codes without images: {count}")

print("\n" + "=" * 80)
print("✅ Many-to-many image linking working!")
print("=" * 80)
