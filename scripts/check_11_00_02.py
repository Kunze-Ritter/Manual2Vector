"""Check error code 11.00.02"""
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
print("🔍 CHECKING ERROR CODE 11.00.02")
print("=" * 80)

# Get error code details
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/vw_error_codes",
    headers=headers,
    params={
        "select": "*",
        "error_code": "ilike.%11.00.02%",
        "limit": 3
    }
)

if response.status_code == 200:
    results = response.json()
    print(f"\n✅ Found {len(results)} results\n")
    
    for i, result in enumerate(results, 1):
        print(f"Result #{i}:")
        print(f"  ID: {result.get('id')}")
        print(f"  Code: {result.get('error_code')}")
        print(f"  Description: {result.get('error_description')}")
        print(f"  Chunk ID: {result.get('chunk_id')}")
        print(f"  Document ID: {result.get('document_id')}")
        print(f"  Page: {result.get('page_number')}")
        
        # Check if chunk has images
        chunk_id = result.get('chunk_id')
        if chunk_id:
            img_response = requests.get(
                f"{SUPABASE_URL}/rest/v1/vw_images",
                headers=headers,
                params={
                    "select": "id,storage_url",
                    "chunk_id": f"eq.{chunk_id}",
                    "limit": 5
                }
            )
            if img_response.status_code == 200:
                images = img_response.json()
                print(f"  Images: {len(images)}")
                for img in images:
                    print(f"    - {img.get('storage_url')}")
        
        print("\n" + "-" * 80 + "\n")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
