"""Check error code data in database"""
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
print("🔍 CHECKING ERROR CODE C9402 DATA")
print("=" * 80)

# Query error code
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/vw_error_codes",
    headers=headers,
    params={
        "select": "error_code,error_description,solution_text,severity_level,page_number",
        "error_code": "ilike.%C9402%",
        "limit": 3
    }
)

if response.status_code == 200:
    results = response.json()
    print(f"\n✅ Found {len(results)} results\n")
    
    for i, result in enumerate(results, 1):
        print(f"Result #{i}:")
        print(f"  Code: {result.get('error_code')}")
        print(f"  Severity: {result.get('severity_level')}")
        print(f"  Page: {result.get('page_number')}")
        print(f"\n  Description ({len(result.get('error_description', ''))} chars):")
        print(f"  {result.get('error_description', 'N/A')}")
        print(f"\n  Solution ({len(result.get('solution_text', ''))} chars):")
        print(f"  {result.get('solution_text', 'N/A')}")
        print("\n" + "-" * 80 + "\n")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
