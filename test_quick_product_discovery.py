"""
Quick test of Product Discovery in Pipeline with small document
"""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.pipeline.master_pipeline import KRMasterPipeline


async def test_quick():
    """Quick test with small document"""
    print("=" * 80)
    print("🧪 Quick Product Discovery Test")
    print("=" * 80)
    print()
    
    # Use a smaller test file
    test_file = r"C:\Users\haast\OneDrive - Kunze & Ritter\Desktop\ServiceManuals\Brother\Brother_HL-L8360CDW_UM_ENG.pdf"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        # Try HP file instead
        test_file = r"C:\Users\haast\OneDrive - Kunze & Ritter\Desktop\ServiceManuals\HP\HP_E877_CPMD.pdf"
        if not Path(test_file).exists():
            print("❌ No test files found")
            return
    
    print(f"📄 Test File: {Path(test_file).name}")
    print()
    
    # Initialize pipeline
    print("🔧 Initializing Pipeline...")
    pipeline = KRMasterPipeline()
    
    try:
        await pipeline.initialize_services()
        print("✅ Pipeline initialized")
        print()
        
        # Check services
        if hasattr(pipeline, 'manufacturer_verification_service'):
            print("✅ Manufacturer Verification Service: Available")
        
        # Check if ClassificationProcessor has the service
        if 'classification' in pipeline.processors:
            classifier = pipeline.processors['classification']
            if hasattr(classifier, 'manufacturer_verification_service'):
                if classifier.manufacturer_verification_service:
                    print("✅ ClassificationProcessor: Has verification service")
                else:
                    print("⚠️  ClassificationProcessor: Service is None")
            else:
                print("❌ ClassificationProcessor: No verification service attribute")
        print()
        
        # Process document
        print("=" * 80)
        print("📋 Processing Document (Classification Stage Only)")
        print("=" * 80)
        print()
        
        result = await pipeline.process_single_document_full_pipeline(test_file, 1, 1)
        
        print()
        print("=" * 80)
        print("📊 Result")
        print("=" * 80)
        print()
        
        if result and result.get('success'):
            print("✅ Processing successful")
            
            if result.get('data'):
                data = result['data']
                if 'classification' in data:
                    cls = data['classification']
                    print(f"   Manufacturer: {cls.get('manufacturer')}")
                    print(f"   Document Type: {cls.get('document_type')}")
                    
                    if 'products_discovered' in cls:
                        products = cls['products_discovered']
                        if products:
                            print(f"\n   ✅ Products Discovered: {len(products)}")
                            for p in products:
                                print(f"      • {p['model']}")
                                print(f"        URL: {p['url']}")
                                print(f"        Confidence: {p['confidence']}")
                                if p.get('product_id'):
                                    print(f"        DB ID: {p['product_id']}")
                        else:
                            print("\n   ⚠️  No products discovered")
        else:
            print("❌ Processing failed")
            if result:
                print(f"   Error: {result.get('message')}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if pipeline.database_service:
            await pipeline.database_service.disconnect()
        print()
        print("=" * 80)
        print("✅ Test Complete")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_quick())
