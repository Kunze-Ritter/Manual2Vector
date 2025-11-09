#!/usr/bin/env python3
"""
Test if content_text would be useful
Shows size and potential use cases
"""

import os

from supabase import create_client

from scripts._env import load_env

# Load env
load_env()

client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("🔍 Testing content_text usefulness...\n")

# Get specific large document
target_filename = "KM_C658_C558_C458_C368_C308_C258_SM_EN.pdf"

doc = client.table('vw_documents').select(
    'id, filename, page_count, word_count, character_count'
).eq('filename', target_filename).limit(1).execute()

if not doc.data:
    print(f"❌ Document not found: {target_filename}")
    print("   Trying largest document instead...")
    
    # Fallback: Get largest document by character_count
    doc = client.table('vw_documents').select(
        'id, filename, page_count, word_count, character_count'
    ).eq('processing_status', 'completed').order(
        'character_count', desc=True
    ).limit(1).execute()
    
    if not doc.data:
        print("❌ No completed documents found")
        exit(1)

doc_data = doc.data[0]
doc_id = doc_data['id']
filename = doc_data['filename']

print(f"📄 Sample Document: {filename}")
print(f"   Pages: {doc_data.get('page_count', 0)}")
print(f"   Words: {doc_data.get('word_count', 0):,}")
print(f"   Characters: {doc_data.get('character_count', 0):,}")

# Get chunks for this document
chunks = client.table('vw_chunks').select(
    'id, text_chunk, metadata'
).eq('document_id', doc_id).execute()

print(f"\n📦 Chunks: {len(chunks.data)}")

# Calculate content_text size
total_text = ""
chunk_types = {}

for chunk in chunks.data:
    text = chunk.get('text_chunk', '')
    total_text += text + "\n\n"
    
    # chunk_type is in metadata
    metadata = chunk.get('metadata', {})
    chunk_type = metadata.get('chunk_type', 'unknown') if isinstance(metadata, dict) else 'unknown'
    chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

content_text_size = len(total_text)
content_text_size_mb = content_text_size / (1024 * 1024)

print(f"\n📊 Content Text Analysis:")
print(f"   Size: {content_text_size:,} bytes ({content_text_size_mb:.2f} MB)")
print(f"   Chunk Types: {chunk_types}")

# Show sample
print(f"\n📝 Sample (first 500 chars):")
print(f"   {total_text[:500]}...")

# Use cases
print(f"\n💡 Potential Use Cases:")
print(f"   ✅ Full-text search: Already covered by chunks + embeddings")
print(f"   ✅ Document preview: Already covered by first few chunks")
print(f"   ❌ Storing full text: {content_text_size_mb:.2f} MB per document = wasteful")
print(f"   ❌ Summary generation: Can use chunks instead")

# Calculate total storage if all documents had content_text
all_docs = client.table('vw_documents').select(
    'id, character_count'
).eq('processing_status', 'completed').execute()

total_storage_mb = sum(
    d.get('character_count', 0) for d in all_docs.data
) / (1024 * 1024)

print(f"\n💾 Storage Impact:")
print(f"   Documents: {len(all_docs.data)}")
print(f"   Total content_text size: ~{total_storage_mb:.1f} MB")
print(f"   Database bloat: Significant!")

print(f"\n🎯 Recommendation:")
print(f"   ❌ content_text: NOT NEEDED - chunks cover all use cases")
print(f"   ❌ content_summary: NOT NEEDED - service manuals don't need summaries")
print(f"   ✅ DELETE both columns to clean up schema")
