"""
Test Firecrawl health/availability
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_firecrawl_health():
    """Test if Firecrawl is running and accessible"""
    
    firecrawl_url = os.getenv('FIRECRAWL_API_URL', 'http://localhost:9004')
    
    print("=" * 80)
    print("🏥 Firecrawl Health Check")
    print("=" * 80)
    print()
    print(f"🔗 Firecrawl URL: {firecrawl_url}")
    print()
    
    # Test 1: Basic connectivity
    print("Test 1: Basic Connectivity")
    print("-" * 80)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{firecrawl_url}/health")
            print(f"✅ Firecrawl is reachable!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except httpx.ConnectError as e:
        print(f"❌ Connection Error: {e}")
        print(f"   Firecrawl is NOT running at {firecrawl_url}")
    except httpx.TimeoutException as e:
        print(f"❌ Timeout Error: {e}")
        print(f"   Firecrawl is not responding")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
    
    print()
    
    # Test 2: API endpoint
    print("Test 2: API Endpoint Check")
    print("-" * 80)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(firecrawl_url)
            print(f"✅ API endpoint is accessible!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
    
    print()
    print("=" * 80)
    print("✅ Health Check Complete")
    print("=" * 80)

if __name__ == '__main__':
    asyncio.run(test_firecrawl_health())
