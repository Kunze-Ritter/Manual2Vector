"""
Test Firecrawl synchronous scrape endpoint (non-async)
"""
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

def test_sync_scrape():
    """Test if Firecrawl has a synchronous scrape endpoint"""
    
    firecrawl_url = os.getenv('FIRECRAWL_API_URL', 'http://localhost:9004')
    api_key = os.getenv('FIRECRAWL_API_KEY', 'fc-local-dev-key-not-required')
    
    print("=" * 80)
    print("🔍 Testing Firecrawl Synchronous Scrape")
    print("=" * 80)
    print()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": "https://example.com"
    }
    
    # Test different endpoint variations
    endpoints = [
        "/scrape",
        "/v0/scrape",
        "/v1/scrape",
        "/api/scrape",
        "/api/v0/scrape",
    ]
    
    with httpx.Client(timeout=10.0) as client:
        for endpoint in endpoints:
            url = f"{firecrawl_url}{endpoint}"
            print(f"Testing: {endpoint}")
            
            try:
                response = client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    print(f"  ✅ SUCCESS! Status: {response.status_code}")
                    print(f"  Response: {response.text[:200]}")
                    print()
                    return endpoint
                elif response.status_code == 404:
                    print(f"  ❌ Not Found (404)")
                elif response.status_code == 401:
                    print(f"  🔒 Unauthorized (401)")
                else:
                    print(f"  ⚠️  Status: {response.status_code}")
                    print(f"  Response: {response.text[:200]}")
                    
            except httpx.TimeoutException:
                print(f"  ⏱️  Timeout (10s)")
            except Exception as e:
                print(f"  ❌ Error: {type(e).__name__}")
            
            print()
    
    print("=" * 80)
    print("❌ No working synchronous endpoint found")
    print("=" * 80)
    return None

if __name__ == '__main__':
    result = test_sync_scrape()
    if result:
        print()
        print(f"✅ Working endpoint: {result}")
