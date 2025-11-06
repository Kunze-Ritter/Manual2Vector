#!/usr/bin/env python3
"""
Docker-based test for Playwright microservice endpoint verification.

This script runs inside a temporary Docker container to test the Playwright
service endpoints from within the Docker network.
"""

import subprocess
import sys
import time
import json

def run_test_in_docker():
    """Run the endpoint test inside a Docker container."""
    
    print("🐳 Starting Docker-based endpoint test...")
    
    # Create a temporary container with curl to test endpoints
    test_commands = [
        # Test health endpoint
        "docker run --rm --network krai-test_krai-test-network alpine/curl:latest sh -c 'echo \"Testing health endpoint...\" && curl -f -s http://playwright-test:3000/health || echo \"Health endpoint failed\"'",
        
        # Test /scrape endpoint  
        "docker run --rm --network krai-test_krai-test-network alpine/curl:latest sh -c 'echo \"Testing /scrape endpoint...\" && curl -f -s -w \"Status: %{http_code}\\n\" http://playwright-test:3000/scrape || echo \"Scrape endpoint failed\"'",
        
        # Test /api/scrape endpoint
        "docker run --rm --network krai-test_krai-test-network alpine/curl:latest sh -c 'echo \"Testing /api/scrape endpoint...\" && curl -f -s -w \"Status: %{http_code}\\n\" http://playwright-test:3000/api/scrape || echo \"API scrape endpoint failed\"'"
    ]
    
    results = {}
    
    for i, command in enumerate(test_commands):
        print(f"\n{'='*60}")
        print(f"Test {i+1}/3: {command}")
        print('='*60)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            print(f"Exit code: {result.returncode}")
            print(f"Output: {result.stdout}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            
            results[f"test_{i+1}"] = {
                "command": command,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            print("❌ Test timed out after 30 seconds")
            results[f"test_{i+1}"] = {
                "command": command,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Timeout after 30 seconds"
            }
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[f"test_{i+1}"] = {
                "command": command,
                "exit_code": -2,
                "stdout": "",
                "stderr": str(e)
            }
    
    # Analyze results
    print(f"\n{'='*60}")
    print("ANALYSIS")
    print('='*60)
    
    scrape_working = results.get("test_2", {}).get("exit_code") == 0
    api_scrape_working = results.get("test_3", {}).get("exit_code") == 0
    
    if scrape_working and not api_scrape_working:
        print("🎯 VERIFICATION RESULT: Use /scrape endpoint")
        print("✅ Current configuration in docker-compose.test.yml is CORRECT")
        return "/scrape"
    elif api_scrape_working and not scrape_working:
        print("🎯 VERIFICATION RESULT: Use /api/scrape endpoint") 
        print("⚠️  Current configuration in docker-compose.test.yml needs UPDATE")
        return "/api/scrape"
    elif scrape_working and api_scrape_working:
        print("⚠️  VERIFICATION RESULT: Both endpoints work")
        print("📝 Manual verification needed - check response content")
        return "both"
    else:
        print("❌ VERIFICATION RESULT: Neither endpoint works")
        print("🔧 Check if Playwright service is running and accessible")
        return "none"

def main():
    """Main function."""
    print("Playwright Microservice Endpoint Verification")
    print("=" * 60)
    
    try:
        # Check if test network exists
        network_check = subprocess.run(
            "docker network ls | grep krai-test",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if network_check.returncode != 0:
            print("❌ krai-test network not found")
            print("Please start the test stack first:")
            print("docker-compose -f docker-compose.test.yml --profile firecrawl up -d")
            return 1
        
        # Check if playwright container is running
        playwright_check = subprocess.run(
            "docker ps | grep playwright-test",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if playwright_check.returncode != 0:
            print("❌ playwright-test container not running")
            print("Please start the firecrawl profile first:")
            print("docker-compose -f docker-compose.test.yml --profile firecrawl up -d")
            return 1
        
        result = run_test_in_docker()
        
        print(f"\n{'='*60}")
        print("FINAL RECOMMENDATION")
        print('='*60)
        
        if result == "/scrape":
            print("✅ KEEP current configuration: http://playwright-test:3000/scrape")
            print("No changes needed to docker-compose.test.yml")
            return 0
        elif result == "/api/scrape":
            print("⚠️  UPDATE configuration needed:")
            print("Change PLAYWRIGHT_MICROSERVICE_URL to: http://playwright-test:3000/api/scrape")
            print("In both firecrawl-api-test and firecrawl-worker-test services")
            return 1
        elif result == "both":
            print("🔍 INCONCLUSIVE - Both endpoints respond")
            print("Manual verification required. Check response content to determine correct endpoint.")
            return 2
        else:
            print("❌ VERIFICATION FAILED - Service not accessible")
            print("Check Docker logs and service status")
            return 3
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return 4

if __name__ == "__main__":
    sys.exit(main())
