"""Check if parts exist for error code 11.00.02"""
import os
from dotenv import load_dotenv
from pathlib import Path
import requests

load_dotenv(Path(__file__).parent / '.env.database')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

print("=" * 80)
print("🔍 CHECKING PARTS FOR ERROR 11.00.02")
print("=" * 80)

# Strategy: Search parts catalog for "formatter" (mentioned in solution)
# or search by document/chunk that contains the error code

# First, check if there are any parts at all
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/vw_parts",
    headers=headers,
    params={
        "select": "part_number,part_name,part_description",
        "limit": 10
    }
)

if response.status_code == 200:
    parts = response.json()
    print(f"\n✅ Found {len(parts)} parts in catalog\n")
    
    if parts:
        for part in parts[:5]:
            print(f"Part: {part.get('part_number')}")
            print(f"  Name: {part.get('part_name')}")
            print(f"  Description: {part.get('part_description', 'N/A')[:80]}")
            print()
    else:
        print("❌ No parts in catalog yet")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)

# Search for "formatter" parts
print("\n" + "=" * 80)
print("🔍 SEARCHING FOR FORMATTER PARTS")
print("=" * 80)

response = requests.get(
    f"{SUPABASE_URL}/rest/v1/vw_parts",
    headers=headers,
    params={
        "select": "part_number,part_name,part_description",
        "or": "(part_name.ilike.*formatter*,part_description.ilike.*formatter*)",
        "limit": 10
    }
)

if response.status_code == 200:
    parts = response.json()
    print(f"\n✅ Found {len(parts)} formatter parts\n")
    
    for part in parts:
        print(f"Part: {part.get('part_number')}")
        print(f"  Name: {part.get('part_name')}")
        print()
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
