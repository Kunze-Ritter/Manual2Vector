#!/usr/bin/env python3
"""
Test script to verify Playwright microservice endpoint.

This script tests both /scrape and /api/scrape endpoints to determine
which one is correct for the Playwright service used by Firecrawl.
"""

import requests
import sys
import time
from typing import Dict, Optional

def test_endpoint(base_url: str, endpoint: str) -> Dict[str, any]:
    """Test a specific endpoint and return results."""
    url = f"{base_url}{endpoint}"
    
    try:
        print(f"Testing {url}...")
        
        # Test health endpoint first
        health_url = f"{base_url}/health"
        try:
            health_response = requests.get(health_url, timeout=5)
            print(f"Health check ({health_url}): {health_response.status_code}")
        except Exception as e:
            print(f"Health check failed: {e}")
        
        # Test the scrape endpoint
        response = requests.get(url, timeout=10)
        
        return {
            "endpoint": endpoint,
            "url": url,
            "status_code": response.status_code,
            "success": response.status_code != 404,
            "response_text": response.text[:200] + "..." if len(response.text) > 200 else response.text,
            "headers": dict(response.headers)
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "endpoint": endpoint,
            "url": url,
            "status_code": None,
            "success": False,
            "error": str(e),
            "response_text": None,
            "headers": None
        }

def main():
    """Main test function."""
    base_url = "http://playwright-test:3000"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"Testing Playwright service endpoints at: {base_url}")
    print("=" * 60)
    
    # Test both possible endpoints
    endpoints_to_test = ["/scrape", "/api/scrape"]
    results = {}
    
    for endpoint in endpoints_to_test:
        result = test_endpoint(base_url, endpoint)
        results[endpoint] = result
        print()
        
        if result["success"]:
            print(f"✅ {endpoint} responded with status {result['status_code']}")
            if result["response_text"]:
                print(f"Response preview: {result['response_text']}")
        else:
            print(f"❌ {endpoint} failed")
            if "error" in result:
                print(f"Error: {result['error']}")
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    
    working_endpoints = [ep for ep, result in results.items() if result["success"]]
    
    if working_endpoints:
        print(f"✅ Working endpoints found: {working_endpoints}")
        
        if len(working_endpoints) == 1:
            print(f"🎯 CORRECT ENDPOINT: {working_endpoints[0]}")
            print("\nUpdate docker-compose.test.yml to use:")
            print(f"PLAYWRIGHT_MICROSERVICE_URL=http://playwright-test:3000{working_endpoints[0]}")
        else:
            print("⚠️  Multiple endpoints working - check responses to determine correct one")
    else:
        print("❌ No working endpoints found")
        print("Possible issues:")
        print("- Playwright service not running")
        print("- Network connectivity issues")
        print("- Service using different port or URL")
    
    return working_endpoints

if __name__ == "__main__":
    working_endpoints = main()
    
    if len(working_endpoints) == 1:
        print(f"\n🎯 VERIFICATION COMPLETE: Use {working_endpoints[0]}")
        sys.exit(0)
    elif len(working_endpoints) > 1:
        print(f"\n⚠️  MULTIPLE WORKING ENDPOINTS: Manual verification needed")
        sys.exit(1)
    else:
        print(f"\n❌ VERIFICATION FAILED: No working endpoints")
        sys.exit(2)
