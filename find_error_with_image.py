"""Find error codes that have images"""
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
print("🔍 SEARCHING FOR ERROR CODES WITH IMAGES")
print("=" * 80)

# Strategy: Find error codes that have chunk_id, then find images with same chunk_id
# First, get error codes with chunk_id
ec_response = requests.get(
    f"{SUPABASE_URL}/rest/v1/vw_error_codes",
    headers=headers,
    params={
        "select": "id,error_code,error_description,chunk_id,page_number",
        "chunk_id": "not.is.null",
        "limit": 20
    }
)

if ec_response.status_code != 200:
    print(f"❌ Error getting error codes: {ec_response.status_code}")
    print(ec_response.text)
    exit()

error_codes = ec_response.json()
print(f"\n✅ Found {len(error_codes)} error codes with chunk_id\n")

# Now find images for these chunks
chunk_ids = [ec['chunk_id'] for ec in error_codes if ec.get('chunk_id')]

if not chunk_ids:
    print("❌ No error codes have chunk_id")
    exit()

response = requests.get(
    f"{SUPABASE_URL}/rest/v1/vw_images",
    headers=headers,
    params={
        "select": "id,chunk_id,storage_url,ai_description,page_number",
        "chunk_id": f"in.({','.join(chunk_ids[:10])})",  # Limit to first 10
        "limit": 10
    }
)

if response.status_code == 200:
    images = response.json()
    print(f"✅ Found {len(images)} images for these chunks\n")
    
    if images:
        # Match error codes with images
        for ec in error_codes:
            chunk_id = ec.get('chunk_id')
            ec_images = [img for img in images if img.get('chunk_id') == chunk_id]
            
            if ec_images:
                print(f"🎯 Error Code: {ec.get('error_code')}")
                print(f"   Description: {ec.get('error_description', 'N/A')[:80]}...")
                print(f"   Page: {ec.get('page_number')}")
                print(f"   Images: {len(ec_images)}")
                for img in ec_images:
                    desc = img.get('ai_description') or 'No description'
                    print(f"     - {desc[:60]}...")
                    print(f"       URL: {img.get('storage_url', 'No URL')}")
                print("\n" + "-" * 80 + "\n")
                break  # Just show first match
    else:
        print("❌ No images found for these error codes")
else:
    print(f"❌ Error getting images: {response.status_code}")
    print(response.text)
