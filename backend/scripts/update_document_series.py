#!/usr/bin/env python3
"""
Update document series from existing products

Reads product_series from document_products and updates documents.series
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
print("UPDATE DOCUMENT SERIES FROM PRODUCTS")
print("=" * 80)

# Get all documents without series
docs = supabase.table('documents') \
    .select('id, filename, manufacturer') \
    .is_('series', 'null') \
    .execute()

print(f"\n📄 Documents without series: {len(docs.data)}")

updated_count = 0

for doc in docs.data:
    doc_id = doc['id']
    filename = doc['filename']
    
    # Get products for this document via JOIN
    result = supabase.rpc('execute_sql', {
        'sql_text': f"""
            SELECT DISTINCT p.series
            FROM krai_core.document_products dp
            JOIN krai_core.products p ON dp.product_id = p.id
            WHERE dp.document_id = '{doc_id}'
            AND p.series IS NOT NULL
        """
    }).execute()
    
    if not result.data:
        continue
    
    # Collect unique series
    series_set = set()
    for row in result.data:
        series = row.get('series')
        if series:
            series_set.add(series)
    
    if series_set:
        # Update document with series
        series_str = ','.join(sorted(series_set))
        
        supabase.table('documents') \
            .update({'series': series_str}) \
            .eq('id', doc_id) \
            .execute()
        
        print(f"✅ {filename}: {series_str}")
        updated_count += 1

print(f"\n" + "=" * 80)
print(f"SUMMARY")
print(f"=" * 80)
print(f"Documents updated: {updated_count}")
print(f"✅ Done!")
