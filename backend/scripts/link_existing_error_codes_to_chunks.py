#!/usr/bin/env python3
"""
Link existing error codes to chunks retroactively

This script updates error_codes.chunk_id for all error codes that don't have a chunk_id yet.
"""

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
print("LINKING ERROR CODES TO CHUNKS")
print("=" * 80)

# Get all error codes without chunk_id
print("\n1. Finding error codes without chunk_id...")
error_codes = supabase.table('vw_error_codes') \
    .select('id, document_id, error_code, page_number') \
    .is_('chunk_id', 'null') \
    .execute()

total_codes = len(error_codes.data)
print(f"   Found {total_codes} error codes without chunk_id")

if total_codes == 0:
    print("\n✅ All error codes already have chunk_id!")
    sys.exit(0)

# Group by document
print("\n2. Grouping by document...")
docs = {}
for ec in error_codes.data:
    doc_id = ec['document_id']
    if doc_id not in docs:
        docs[doc_id] = []
    docs[doc_id].append(ec)

print(f"   {len(docs)} documents need linking")

# Link each document's error codes
print("\n3. Linking error codes to chunks...")
total_linked = 0
total_not_found = 0

for doc_id, codes in docs.items():
    print(f"\n   Document: {doc_id}")
    print(f"   Error codes: {len(codes)}")
    
    linked = 0
    not_found = 0
    
    for ec in codes:
        page_num = ec.get('page_number')
        if not page_num:
            not_found += 1
            continue
        
        # Find chunk that contains this page
        chunk = supabase.table('vw_chunks') \
            .select('id') \
            .eq('document_id', doc_id) \
            .lte('page_start', page_num) \
            .gte('page_end', page_num) \
            .limit(1) \
            .execute()
        
        if chunk.data:
            chunk_id = chunk.data[0]['id']
            
            # Update error code with chunk_id
            supabase.table('vw_error_codes') \
                .update({'chunk_id': chunk_id}) \
                .eq('id', ec['id']) \
                .execute()
            
            linked += 1
        else:
            not_found += 1
            print(f"      ⚠️  No chunk found for error code {ec['error_code']} on page {page_num}")
    
    print(f"   ✅ Linked: {linked}")
    if not_found > 0:
        print(f"   ⚠️  Not found: {not_found}")
    
    total_linked += linked
    total_not_found += not_found

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total error codes processed: {total_codes}")
print(f"✅ Successfully linked: {total_linked}")
if total_not_found > 0:
    print(f"⚠️  Could not link: {total_not_found}")
    print(f"   (No matching chunk found - page might be outside chunk range)")

print("\n✅ Done!")
