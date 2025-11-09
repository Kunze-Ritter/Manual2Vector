"""
Direct test of KRAI Tools without Agent
"""

import json
import os
import sys
from pathlib import Path

from supabase import create_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.processors.env_loader import load_all_env_files

# Load environment
load_all_env_files(PROJECT_ROOT)

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# Import tools
from agent_api import KRAITools

print("="*60)
print("TESTING KRAI TOOLS DIRECTLY")
print("="*60)

tools = KRAITools(supabase)

# Test 1: Search for C9402
print("\n1. Testing search_error_codes('C9402')...")
result = tools.search_error_codes("C9402")
data = json.loads(result)
print(f"   Found: {data.get('found')}")
print(f"   Raw data keys: {list(data.keys())}")
if data.get('found'):
    print(f"   Count: {data.get('count')}")
    # Check what key contains the results
    if 'results' in data:
        print(f"   First result: {data['results'][0]['error_code']} - {data['results'][0].get('error_description', '')[:60]}...")
    elif 'error_codes' in data:
        print(f"   First result: {data['error_codes'][0]['error_code']} - {data['error_codes'][0].get('error_description', '')[:60]}...")
    else:
        print(f"   Data: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")

# Test 2: Search for 10.00.33
print("\n2. Testing search_error_codes('10.00.33')...")
result = tools.search_error_codes("10.00.33")
data = json.loads(result)
print(f"   Found: {data.get('found')}")
if data.get('found'):
    print(f"   Count: {data.get('count')}")
    print(f"   First result: {data['error_codes'][0]['error_code']} - {data['error_codes'][0].get('error_description', '')[:60]}...")
    print(f"   Manufacturer: {data['error_codes'][0].get('manufacturer_name', 'Unknown')}")
    print(f"   Document: {data['error_codes'][0].get('document_filename', 'Unknown')}")

# Test 3: Search for HP 10.00.33
print("\n3. Testing search_error_codes('HP Fehler 10.00.33')...")
result = tools.search_error_codes("HP Fehler 10.00.33")
data = json.loads(result)
print(f"   Found: {data.get('found')}")
if data.get('found'):
    print(f"   Count: {data.get('count')}")
    for i, res in enumerate(data['error_codes'][:3]):
        print(f"   Result {i+1}: {res['error_code']} - Manufacturer: {res.get('manufacturer_name', 'Unknown')}")

# Test 4: Search parts
print("\n4. Testing search_parts('Fuser')...")
result = tools.search_parts("Fuser")
data = json.loads(result)
print(f"   Found: {data.get('found')}")
if data.get('found'):
    print(f"   Count: {data.get('count')}")

# Test 5: Search parts for Lexmark
print("\n5. Testing search_parts('41X5345')...")
result = tools.search_parts("41X5345")
data = json.loads(result)
print(f"   Found: {data.get('found')}")
if data.get('found'):
    print(f"   Count: {data.get('count')}")
    print(f"   First result: {data['parts'][0]['part_number']}")
    print(f"   Manufacturer: {data['parts'][0].get('manufacturer_name', 'Unknown')}")
    print(f"   Full data: {json.dumps(data['parts'][0], indent=2, ensure_ascii=False)}")

print("\n" + "="*60)
print("DONE")
print("="*60)
