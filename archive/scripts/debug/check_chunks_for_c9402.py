"""Check chunks for C9402 to find full solution text"""
import os
import requests

from scripts._env import load_env

load_env(extra_files=['.env.database'])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

print("=" * 80)
print("🔍 SEARCHING CHUNKS FOR C9402 SOLUTION")
print("=" * 80)

# Search chunks containing C9402
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/vw_intelligence_chunks",
    headers=headers,
    params={
        "select": "text_chunk,page_start,page_end,document_id",
        "text_chunk": "ilike.%C9402%",
        "limit": 5
    }
)

if response.status_code == 200:
    chunks = response.json()
    print(f"\n✅ Found {len(chunks)} chunks containing 'C9402'\n")
    
    for i, chunk in enumerate(chunks, 1):
        text = chunk.get('text_chunk', '')
        page_start = chunk.get('page_start')
        page_end = chunk.get('page_end')
        
        print(f"Chunk #{i} (Pages {page_start}-{page_end}):")
        print(f"Length: {len(text)} chars")
        print(f"\nContent:")
        print("-" * 80)
        print(text)
        print("-" * 80)
        print()
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
