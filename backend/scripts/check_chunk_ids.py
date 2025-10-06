#!/usr/bin/env python3
"""Check if error codes have chunk_ids"""

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
print("ERROR CODES WITH CHUNK IDs")
print("=" * 80)

# Get sample error codes
result = supabase.table('error_codes') \
    .select('error_code, chunk_id, page_number') \
    .eq('document_id', '89387251-6506-4c41-ac7c-53666e82d457') \
    .limit(10) \
    .execute()

print(f"\nSample error codes (first 10):")
for ec in result.data:
    chunk_id = ec.get('chunk_id')
    chunk_display = chunk_id[:8] + "..." if chunk_id else "NULL"
    print(f"  {ec['error_code']:<12} chunk_id={chunk_display:<12} (page {ec['page_number']})")

# Count with/without chunk_id
with_chunk = supabase.table('error_codes') \
    .select('id', count='exact') \
    .eq('document_id', '89387251-6506-4c41-ac7c-53666e82d457') \
    .not_.is_('chunk_id', 'null') \
    .execute()

without_chunk = supabase.table('error_codes') \
    .select('id', count='exact') \
    .eq('document_id', '89387251-6506-4c41-ac7c-53666e82d457') \
    .is_('chunk_id', 'null') \
    .execute()

total = with_chunk.count + without_chunk.count

print(f"\n" + "=" * 80)
print("STATISTICS")
print("=" * 80)
print(f"Total error codes: {total}")
print(f"✅ With chunk_id: {with_chunk.count} ({with_chunk.count/total*100:.1f}%)")
print(f"❌ Without chunk_id: {without_chunk.count} ({without_chunk.count/total*100:.1f}%)")

if with_chunk.count == total:
    print("\n🎉 ALL ERROR CODES HAVE CHUNK IDs!")
