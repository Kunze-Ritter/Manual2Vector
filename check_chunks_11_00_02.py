"""Check chunks for 11.00.02"""
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
print("🔍 CHECKING CHUNKS FOR 11.00.02")
print("=" * 80)

# Search chunks
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/vw_intelligence_chunks",
    headers=headers,
    params={
        "select": "text_chunk,page_start",
        "text_chunk": "ilike.%11.00.02%",
        "limit": 5
    }
)

if response.status_code == 200:
    chunks = response.json()
    print(f"\n✅ Found {len(chunks)} chunks\n")
    
    for i, chunk in enumerate(chunks, 1):
        text = chunk.get('text_chunk', '')
        page = chunk.get('page_start')
        
        print(f"Chunk #{i} (Page {page}):")
        print(f"Length: {len(text)} chars")
        print(f"\nContent:")
        print("-" * 80)
        print(text[:1000])  # First 1000 chars
        print("-" * 80)
        print()
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
