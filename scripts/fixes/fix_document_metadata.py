#!/usr/bin/env python3
"""
Fix Document Metadata
Copies metadata from processing_results to document columns
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load env
load_dotenv(Path(__file__).parent.parent.parent / '.env.database')

client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("🔧 Fixing Document Metadata...\n")

# Get all documents with missing metadata
docs = client.table('vw_documents').select(
    'id, filename, page_count, word_count, character_count, processing_results'
).eq('processing_status', 'completed').execute()

print(f"Found {len(docs.data)} completed documents\n")

# Count documents with missing metadata
missing_metadata = [
    d for d in docs.data 
    if d.get('page_count', 0) == 0 or d.get('word_count', 0) == 0
]

print(f"Documents with missing metadata: {len(missing_metadata)}\n")

if not missing_metadata:
    print("✅ All documents have metadata!")
    sys.exit(0)

fixed_count = 0

for doc in missing_metadata:
    doc_id = doc['id']
    filename = doc['filename']
    results = doc.get('processing_results', {})
    
    if not results:
        print(f"⚠️  {filename} - No processing_results")
        continue
    
    # Extract metadata from processing_results
    metadata = results.get('metadata', {})
    stats = results.get('statistics', {})
    
    # Build update data
    update_data = {}
    
    # Page count
    page_count = stats.get('total_pages', 0) or metadata.get('page_count', 0)
    if page_count > 0:
        update_data['page_count'] = page_count
    
    # Word count
    word_count = stats.get('total_words', 0) or metadata.get('word_count', 0)
    if word_count > 0:
        update_data['word_count'] = word_count
    
    # Character count
    char_count = stats.get('total_characters', 0) or metadata.get('char_count', 0)
    if char_count > 0:
        update_data['character_count'] = char_count
    
    if not update_data:
        print(f"⚠️  {filename} - No metadata in processing_results")
        continue
    
    # Update document
    try:
        client.schema('krai_core').table('documents').update(update_data).eq(
            'id', doc_id
        ).execute()
        
        print(f"✅ {filename}")
        print(f"   Pages: {update_data.get('page_count', 'N/A')}, "
              f"Words: {update_data.get('word_count', 'N/A')}, "
              f"Chars: {update_data.get('character_count', 'N/A')}")
        
        fixed_count += 1
    except Exception as e:
        print(f"❌ {filename} - Error: {e}")

print(f"\n{'='*60}")
print(f"✅ Fixed {fixed_count}/{len(missing_metadata)} documents!")
print(f"{'='*60}")
