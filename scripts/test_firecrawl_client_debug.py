"""
Debug Firecrawl Python client behavior
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_firecrawl_client():
    """Test Firecrawl Python client with detailed logging"""
    
    try:
        from firecrawl import AsyncFirecrawl
    except ImportError:
        print("❌ firecrawl-py not installed!")
        print("   Install with: pip install firecrawl-py")
        return
    
    firecrawl_url = os.getenv('FIRECRAWL_API_URL', 'http://localhost:9004')
    api_key = os.getenv('FIRECRAWL_API_KEY', 'fc-local-dev-key-not-required')
    
    print("=" * 80)
    print("🔍 Firecrawl Python Client Debug")
    print("=" * 80)
    print()
    print(f"🔗 API URL: {firecrawl_url}")
    print(f"🔑 API Key: {api_key}")
    print()
    
    # Create client
    print("🔧 Creating AsyncFirecrawl client...")
    client = AsyncFirecrawl(api_key=api_key, api_url=firecrawl_url)
    print(f"✅ Client created: {client}")
    print()
    
    # Check client attributes
    print("📋 Client Configuration:")
    print(f"   api_url: {getattr(client, 'api_url', 'N/A')}")
    print(f"   api_key: {getattr(client, 'api_key', 'N/A')[:20]}...")
    print()
    
    # Try scraping
    test_url = "https://example.com"
    print(f"🧪 Testing scrape: {test_url}")
    print("⏳ Waiting for response (30s timeout)...")
    print()
    
    try:
        # Use asyncio.wait_for to add timeout
        response = await asyncio.wait_for(
            client.scrape(url=test_url, options={"formats": ["markdown"]}),
            timeout=30.0
        )
        
        print("✅ Scrape successful!")
        print(f"   Response type: {type(response)}")
        print(f"   Response keys: {list(response.keys()) if isinstance(response, dict) else 'N/A'}")
        print()
        print("📊 Response:")
        print(response)
        
    except asyncio.TimeoutError:
        print("❌ Timeout after 30 seconds")
        print("   Firecrawl client is not receiving a response")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("✅ Test Complete")
    print("=" * 80)

if __name__ == '__main__':
    asyncio.run(test_firecrawl_client())
