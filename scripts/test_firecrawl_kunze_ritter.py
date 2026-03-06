"""
Test Firecrawl with Kunze-Ritter website
"""
import asyncio
import os
from dotenv import load_dotenv
from backend.services.web_scraping_service import create_web_scraping_service

load_dotenv()

async def test_firecrawl_kunze_ritter():
    """Test Firecrawl scraping with Kunze-Ritter website"""
    
    test_url = "https://kunze-ritter.de"
    
    print("=" * 80)
    print("🧪 Firecrawl Test: Kunze-Ritter Website")
    print("=" * 80)
    print()
    print(f"📄 Test URL: {test_url}")
    print()
    
    # Create web scraping service
    print("🔧 Initializing web scraping service...")
    scraping_service = create_web_scraping_service(backend='firecrawl')
    print("✅ Service initialized")
    print()
    
    # Test scraping
    print("=" * 80)
    print("🔍 Scraping URL...")
    print("=" * 80)
    print()
    
    try:
        result = await scraping_service.scrape_url(test_url)
        
        print()
        print("=" * 80)
        print("📊 Scraping Result")
        print("=" * 80)
        print()
        
        if result and result.get('success'):
            print("✅ Scraping successful!")
            print()
            print(f"   Backend: {result.get('backend')}")
            print(f"   Content length: {len(result.get('content', ''))} characters")
            print(f"   Markdown length: {len(result.get('markdown', ''))} characters")
            
            # Show first 1000 characters of content
            content = result.get('content', '')
            if content:
                print()
                print("📝 Content Preview (first 1000 chars):")
                print("-" * 80)
                print(content[:1000])
                print("-" * 80)
            
            # Show metadata
            metadata = result.get('metadata', {})
            if metadata:
                print()
                print("📋 Metadata:")
                for key, value in metadata.items():
                    print(f"   {key}: {value}")
        else:
            print("❌ Scraping failed!")
            print()
            print(f"   Backend: {result.get('backend')}")
            print(f"   Error: {result.get('error')}")
            
    except Exception as e:
        print("❌ Error during scraping:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("✅ Test Complete")
    print("=" * 80)

if __name__ == '__main__':
    asyncio.run(test_firecrawl_kunze_ritter())
