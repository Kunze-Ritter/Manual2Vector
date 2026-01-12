"""
Test Master Pipeline with Product Discovery

Tests the complete pipeline with automatic product discovery and database storage.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.pipeline.master_pipeline import KRMasterPipeline


async def test_pipeline_with_discovery():
    """
    Test complete pipeline with product discovery
    """
    print("=" * 80)
    print("🧪 Master Pipeline Test with Product Discovery")
    print("=" * 80)
    print()
    
    # Test file
    test_file = r"C:\Users\haast\OneDrive - Kunze & Ritter\Desktop\ServiceManuals\HP\HP_E877_CPMD.pdf"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"📄 Test File: {Path(test_file).name}")
    print(f"📁 Path: {test_file}")
    print()
    
    # Initialize pipeline
    print("🔧 Initializing Master Pipeline...")
    pipeline = KRMasterPipeline()
    
    try:
        await pipeline.initialize_services()
        print("✅ Pipeline initialized successfully")
        print()
        
        # Check if manufacturer verification service is available
        if hasattr(pipeline, 'manufacturer_verification_service'):
            print("✅ Manufacturer Verification Service: Available")
            print(f"   Perplexity API: {'Configured' if pipeline.manufacturer_verification_service.perplexity_api_key else 'Not configured'}")
            print(f"   Google API: {'Configured' if pipeline.manufacturer_verification_service.google_api_key else 'Not configured'}")
        else:
            print("⚠️  Manufacturer Verification Service: Not available")
        print()
        
        # Process document
        print("=" * 80)
        print("📋 Processing Document")
        print("=" * 80)
        print()
        
        print("⚠️  Note: This will process the complete document through all stages:")
        print("   1. Text Extraction")
        print("   2. Classification (with Product Discovery)")
        print("   3. Chunking")
        print("   4. Embedding")
        print("   5. Image Processing")
        print("   6. Table Extraction")
        print("   7. Storage")
        print()
        
        # Process the file through full pipeline
        result = await pipeline.process_single_document_full_pipeline(test_file, 1, 1)
        
        print()
        print("=" * 80)
        print("📊 Processing Result")
        print("=" * 80)
        print()
        
        if result and result.get('success'):
            print("✅ Document processed successfully!")
            print()
            
            if result.get('data'):
                print("📋 Result Data:")
                for key, value in result.data.items():
                    if key == 'classification' and isinstance(value, dict):
                        print(f"   {key}:")
                        for k, v in value.items():
                            if k == 'models' and isinstance(v, list):
                                print(f"      {k}: {len(v)} models found")
                                for model in v[:3]:  # Show first 3
                                    print(f"         - {model}")
                            else:
                                print(f"      {k}: {v}")
                    else:
                        print(f"   {key}: {value}")
            
            # Check if products were saved to database
            print()
            print("=" * 80)
            print("💾 Checking Database for Saved Products")
            print("=" * 80)
            print()
            
            try:
                # Query for recently added products
                query = """
                    SELECT 
                        p.id,
                        p.model_number,
                        m.name as manufacturer_name,
                        p.urls,
                        p.metadata,
                        p.created_at
                    FROM krai_core.products p
                    JOIN krai_core.manufacturers m ON p.manufacturer_id = m.id
                    ORDER BY p.created_at DESC
                    LIMIT 5
                """
                
                products = await pipeline.database_service.fetch_all(query)
                
                if products:
                    print(f"✅ Found {len(products)} recent products in database:")
                    print()
                    for product in products:
                        print(f"   📦 {product['manufacturer_name']} {product['model_number']}")
                        print(f"      ID: {product['id']}")
                        print(f"      Created: {product['created_at']}")
                        if product.get('urls'):
                            urls = product['urls']
                            if isinstance(urls, dict) and 'product_page' in urls:
                                print(f"      URL: {urls['product_page']}")
                        print()
                else:
                    print("ℹ️  No products found in database yet")
            
            except Exception as e:
                print(f"⚠️  Could not query products: {e}")
        
        else:
            print("❌ Document processing failed")
            if result and hasattr(result, 'message'):
                print(f"   Error: {result.message}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if pipeline.database_service:
            await pipeline.database_service.disconnect()
        print()
        print("=" * 80)
        print("✅ Test Complete")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_pipeline_with_discovery())
