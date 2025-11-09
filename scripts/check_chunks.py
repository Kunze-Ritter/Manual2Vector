"""Quick Chunk Size Check"""
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

response = requests.get(
    f"{SUPABASE_URL}/rest/v1/vw_intelligence_chunks",
    headers=headers,
    params={"select": "id,text_chunk", "limit": 10, "order": "created_at.desc"}
)

if response.status_code == 200:
    chunks = response.json()
    print(f"✅ {len(chunks)} Chunks gefunden\n")
    
    for i, chunk in enumerate(chunks, 1):
        text_length = len(chunk.get('text_chunk', ''))
        preview = chunk.get('text_chunk', '')[:80].replace('\n', ' ')
        print(f"{i}. Länge: {text_length:5d} | {preview}...")
    
    avg = sum(len(c.get('text_chunk', '')) for c in chunks) / len(chunks)
    print(f"\n📊 Durchschnitt: {avg:.0f} Zeichen")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
