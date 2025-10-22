#!/usr/bin/env python3
"""
Fix Parts Catalog Products
Removes false products (part numbers) and adds correct product with product_code
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))

from processors.product_code_extractor import ProductCodeExtractor

# Load env
load_dotenv(Path(__file__).parent.parent.parent / '.env.database')

client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("🔧 Fixing Parts Catalog Products...\n")

# Get Konica Minolta manufacturer ID
km_result = client.table('vw_manufacturers').select('id').ilike('name', '*konica*').limit(1).execute()
if not km_result.data:
    print("❌ Konica Minolta manufacturer not found!")
    sys.exit(1)

km_id = km_result.data[0]['id']
print(f"✅ Konica Minolta ID: {km_id}\n")

# Get all documents with document_type = service_manual (should be parts_catalog)
docs = client.table('vw_documents').select(
    'id, filename, document_type, processing_results'
).eq('manufacturer_id', km_id).execute()

print(f"Found {len(docs.data)} Konica Minolta documents\n")

extractor = ProductCodeExtractor(debug=True)
print("🔍 Debug mode enabled for Product Code Extractor\n")
fixed_count = 0

for doc in docs.data:
    doc_id = doc['id']
    filename = doc['filename']
    doc_type = doc['document_type']
    results = doc.get('processing_results', {})
    
    # Check if this looks like a parts catalog
    stats = results.get('statistics', {})
    parts_count = stats.get('parts_count', 0)
    products_count = stats.get('total_products', 0)
    error_codes_count = stats.get('total_error_codes', 0)
    
    # Parts catalog: Many parts, no error codes, many "products" (false positives)
    if parts_count > 100 and error_codes_count == 0 and products_count > 5:
        print(f"\n📦 {filename}")
        print(f"   Parts: {parts_count}, Products: {products_count}, Errors: {error_codes_count}")
        print(f"   → Looks like Parts Catalog!")
        
        # Get parts from processing_results (not from DB - parts have no document_id!)
        parts_from_results = results.get('products', [])  # These are actually parts!
        
        if not parts_from_results:
            print(f"   ⚠️  No parts found in processing_results")
            continue
        
        # Convert to format expected by extractor
        parts_data = [
            {
                'part_number': p.get('model_number', ''),
                'part_description': p.get('specifications', {}).get('specifications', {}).get('description', '')
            }
            for p in parts_from_results
        ]
        
        # Debug: Show sample parts
        print(f"   🔍 Sample parts (first 3):")
        for i, part in enumerate(parts_data[:3]):
            print(f"      {i+1}. {part['part_number']} - {part['part_description'][:50] if part['part_description'] else 'N/A'}")
        
        # Extract product code
        pdf_title = results.get('metadata', {}).get('title', filename)
        pdf_metadata = {
            'title': pdf_title,
            'filename': filename,
            'creation_date': results.get('metadata', {}).get('pdf_metadata', {}).get('creation_date', '')
        }
        
        # Debug: Show metadata
        print(f"   📄 Filename: {filename}")
        print(f"   📋 Title: {pdf_title}")
        
        product_info = extractor.extract_from_parts_catalog(
            parts=parts_data,
            pdf_metadata=pdf_metadata
        )
        
        if not product_info:
            print(f"   ⚠️  Could not extract product code")
            continue
        
        print(f"   ✅ Product Code: {product_info['product_code']}")
        print(f"   ✅ Series: {product_info.get('series_name', 'N/A')}")
        print(f"   🔍 Extraction method: {product_info.get('extraction_method', 'N/A')}")
        
        # Delete false products (part numbers) - use schema() method
        model_numbers_to_delete = [p['model_number'] for p in results.get('products', [])]
        
        if not model_numbers_to_delete:
            print(f"   ⚠️  No model numbers to delete")
        else:
            # Delete each product individually (Supabase doesn't support .in_() with delete)
            deleted_count = 0
            for model_num in model_numbers_to_delete:
                try:
                    delete_result = client.schema('krai_core').table('products').delete().eq(
                        'manufacturer_id', km_id
                    ).eq('model_number', model_num).execute()
                    if delete_result.data:
                        deleted_count += len(delete_result.data)
                except Exception as e:
                    # Product might not exist, that's ok
                    pass
            
            print(f"   🗑️  Deleted {deleted_count} false products")
        
        # Create correct product
        product_data = {
            'manufacturer_id': km_id,
            'model_number': product_info['series_name'] or product_info['product_code'],
            'product_code': product_info['product_code'],
            'product_type': 'laser_multifunction',  # Konica Minolta bizhub are laser MFPs
        }
        
        # Check if product already exists
        existing = client.table('vw_products').select('id').eq(
            'model_number', product_data['model_number']
        ).limit(1).execute()
        
        if existing.data:
            print(f"   ℹ️  Product already exists: {product_data['model_number']}")
            product_id = existing.data[0]['id']
        else:
            # Insert new product
            insert_result = client.schema('krai_core').table('products').insert(product_data).execute()
            product_id = insert_result.data[0]['id']
            print(f"   ✅ Created product: {product_data['model_number']}")
        
        # Link document to product
        link_data = {
            'document_id': doc_id,
            'product_id': product_id
        }
        
        # Check if link exists
        existing_link = client.schema('krai_core').table('document_products').select('id').eq(
            'document_id', doc_id
        ).eq('product_id', product_id).execute()
        
        if not existing_link.data:
            client.schema('krai_core').table('document_products').insert(link_data).execute()
            print(f"   🔗 Linked document to product")
        
        # Update document_type to parts_catalog
        client.schema('krai_core').table('documents').update({
            'document_type': 'parts_catalog'
        }).eq('id', doc_id).execute()
        print(f"   📝 Updated document_type to parts_catalog")
        
        fixed_count += 1

print(f"\n✅ Fixed {fixed_count} parts catalogs!")
