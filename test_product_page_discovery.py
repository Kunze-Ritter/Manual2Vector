"""
Test Product Page Discovery with Multi-Strategy Approach

Tests the new discover_product_page() method with:
1. URL Pattern matching (fast, reliable)
2. Google Custom Search API (if configured)
3. Web scraping fallback
"""

import asyncio
from backend.services.manufacturer_verification_service import ManufacturerVerificationService
from backend.services.web_scraping_service import create_web_scraping_service


async def test_product_page_discovery():
    print("=" * 60)
    print("Testing Product Page Discovery")
    print("=" * 60)
    
    # Initialize services
    web_service = create_web_scraping_service()
    verification_service = ManufacturerVerificationService(
        web_scraping_service=web_service
    )
    
    # Test cases
    test_cases = [
        ("HP Inc.", "M454dn"),
        ("Canon", "imageRUNNER ADVANCE C5535i"),
        ("Brother", "HL-L2350DW"),
        ("Konica Minolta", "bizhub C368"),
    ]
    
    for manufacturer, model in test_cases:
        print(f"\n{'=' * 60}")
        print(f"🔍 Testing: {manufacturer} {model}")
        print(f"{'=' * 60}")
        
        result = await verification_service.discover_product_page(
            manufacturer=manufacturer,
            model_number=model
        )
        
        print(f"\n📊 Results:")
        print(f"  URL: {result.get('url')}")
        print(f"  Source: {result.get('source')}")
        print(f"  Confidence: {result.get('confidence'):.2f}")
        print(f"  Verified: {result.get('verified')}")
        
        if result.get('title'):
            print(f"  Title: {result.get('title')}")
        if result.get('snippet'):
            print(f"  Snippet: {result.get('snippet')[:100]}...")
        
        # If URL found, try to scrape it
        if result.get('url'):
            print(f"\n🌐 Testing URL accessibility...")
            try:
                scrape_result = await web_service.scrape_url(result['url'])
                if scrape_result and scrape_result.get('success'):
                    content = scrape_result.get('content', '')
                    print(f"  ✅ URL accessible")
                    print(f"  📄 Content length: {len(content)} characters")
                    
                    # Check if model is mentioned
                    if model.lower() in content.lower():
                        print(f"  ✅ Model '{model}' found in content")
                    else:
                        print(f"  ⚠️  Model '{model}' NOT found in content")
                else:
                    print(f"  ❌ URL not accessible")
            except Exception as e:
                print(f"  ❌ Error accessing URL: {e}")
    
    print(f"\n{'=' * 60}")
    print("✅ Product Page Discovery Test Complete")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(test_product_page_discovery())
