"""
Production Data Validation Script

Validates that all extracted data is being saved correctly to the database.

Usage:
    python validate_production_data.py --document-id <uuid>
    python validate_production_data.py --latest  # Check latest processed document
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from supabase import create_client


def validate_document(document_id: str = None, check_latest: bool = False):
    """Validate that document data was saved correctly"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    
    print("\n" + "="*80)
    print("  PRODUCTION DATA VALIDATION")
    print("="*80)
    
    # Get document
    try:
        if check_latest:
            result = supabase.table('vw_documents') \
                .select('*') \
                .order('created_at', desc=True) \
                .limit(1) \
                .execute()
            
            if not result.data:
                print("\n❌ No documents found in database")
                return False
            
            document = result.data[0]
            document_id = document['id']
            print(f"\n📄 Checking LATEST document:")
        else:
            result = supabase.table('vw_documents') \
                .select('*') \
                .eq('id', document_id) \
                .execute()
            
            if not result.data:
                print(f"\n❌ Document {document_id} not found")
                return False
            
            document = result.data[0]
            print(f"\n📄 Checking document:")
        
        print(f"   ID: {document_id}")
        print(f"   Filename: {document['filename']}")
        print(f"   Status: {document.get('processing_status', 'unknown')}")
        print(f"   Created: {document.get('created_at', 'unknown')}")
        
    except Exception as e:
        print(f"\n❌ Error fetching document: {e}")
        return False
    
    # Validation checks
    all_passed = True
    
    print("\n" + "-"*80)
    print("VALIDATION CHECKS:")
    print("-"*80)
    
    # 1. Check processing_results JSONB
    print("\n1️⃣  Processing Results (JSONB):")
    if document.get('processing_results'):
        results = document['processing_results']
        print("   ✅ processing_results column populated")
        print(f"   - Products: {len(results.get('products', []))}")
        print(f"   - Error Codes: {len(results.get('error_codes', []))}")
        print(f"   - Versions: {len(results.get('versions', []))}")
        print(f"   - Statistics: {bool(results.get('statistics'))}")
    else:
        print("   ❌ processing_results is NULL")
        all_passed = False
    
    # 2. Check chunks in krai_intelligence.chunks
    print("\n2️⃣  Chunks (krai_intelligence.chunks):")
    try:
        chunk_result = supabase.table('vw_chunks') \
            .select('id, text_chunk, embedding') \
            .eq('document_id', document_id) \
            .execute()
        
        chunks = chunk_result.data
        chunks_with_embeddings = [c for c in chunks if c.get('embedding')]
        
        if chunks:
            print(f"   ✅ {len(chunks)} chunks saved")
            print(f"   ✅ {len(chunks_with_embeddings)} chunks with embeddings")
        else:
            print("   ❌ No chunks found")
            all_passed = False
    except Exception as e:
        print(f"   ❌ Error checking chunks: {e}")
        all_passed = False
    
    # 3. Check error codes in krai_intelligence.error_codes
    print("\n3️⃣  Error Codes (krai_intelligence.error_codes):")
    try:
        ec_result = supabase.table('vw_error_codes') \
            .select('*') \
            .eq('document_id', document_id) \
            .execute()
        
        error_codes = ec_result.data
        
        if error_codes:
            print(f"   ✅ {len(error_codes)} error codes saved")
            # Show first 3
            for ec in error_codes[:3]:
                print(f"      - {ec['error_code']}: {ec['error_description'][:50]}...")
        else:
            print("   ⚠️  No error codes found (may be expected)")
    except Exception as e:
        print(f"   ❌ Error checking error codes: {e}")
        all_passed = False
    
    # 4. Check products in krai_core.products
    print("\n4️⃣  Products (krai_core.products):")
    try:
        # Check for products extracted from this document
        if document.get('processing_results'):
            extracted_products = document['processing_results'].get('products', [])
            
            if extracted_products:
                print(f"   ℹ️  {len(extracted_products)} products in processing_results")
                
                # Check if they're in products table
                saved_count = 0
                for prod in extracted_products:
                    model_number = prod.get('model_number')
                    if model_number:
                        prod_result = supabase.table('vw_products') \
                            .select('id') \
                            .eq('model_number', model_number) \
                            .execute()
                        if prod_result.data:
                            saved_count += 1
                
                if saved_count > 0:
                    print(f"   ✅ {saved_count}/{len(extracted_products)} products saved to table")
                else:
                    print(f"   ❌ 0/{len(extracted_products)} products saved to table")
                    all_passed = False
            else:
                print("   ⚠️  No products extracted (may be expected)")
        else:
            print("   ⚠️  No processing_results to check")
    except Exception as e:
        print(f"   ❌ Error checking products: {e}")
        all_passed = False
    
    # 5. Check images in krai_content.images
    print("\n5️⃣  Images (krai_content.images):")
    try:
        img_result = supabase.table('vw_images') \
            .select('id, filename, file_hash, storage_url') \
            .eq('document_id', document_id) \
            .execute()
        
        images = img_result.data
        
        if images:
            print(f"   ✅ {len(images)} images saved")
            # Check for hash-based naming
            hash_based = [img for img in images if img.get('file_hash') and '/' not in img.get('filename', '')]
            if hash_based:
                print(f"   ✅ {len(hash_based)} images use hash-based naming")
            else:
                print(f"   ⚠️  Images use old naming format (will be migrated)")
        else:
            print("   ⚠️  No images found (may be expected if R2 was disabled)")
    except Exception as e:
        print(f"   ❌ Error checking images: {e}")
        all_passed = False
    
    # Summary
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL VALIDATION CHECKS PASSED!")
    else:
        print("❌ SOME VALIDATION CHECKS FAILED - SEE ABOVE")
    print("="*80 + "\n")
    
    return all_passed


def main():
    parser = argparse.ArgumentParser(description='Validate production data persistence')
    parser.add_argument('--document-id', help='Document ID to check')
    parser.add_argument('--latest', action='store_true', help='Check latest processed document')
    
    args = parser.parse_args()
    
    if not args.document_id and not args.latest:
        print("❌ Error: Provide --document-id <uuid> or --latest")
        sys.exit(1)
    
    success = validate_document(
        document_id=args.document_id,
        check_latest=args.latest
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
