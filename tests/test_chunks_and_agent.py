"""
Test Script: Chunk-Größe prüfen und Agent testen
"""
import os
from dotenv import load_dotenv
from pathlib import Path
import requests
import json

# Load environment
project_root = Path(__file__).parent
load_dotenv(project_root / '.env.database')

# Supabase Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print("=" * 80)
print("KRAI - Chunk-Größe & Agent Test")
print("=" * 80)

# ============================================================================
# 1. Chunk-Größe in Datenbank prüfen
# ============================================================================
print("\n📊 1. CHUNK-GRÖSSE PRÜFEN")
print("-" * 80)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Hole ein paar Chunks und prüfe deren Größe
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/krai_intelligence.chunks",
    headers=headers,
    params={
        "select": "id,text_chunk,chunk_index,page_start,page_end,document_id",
        "limit": 5,
        "order": "created_at.desc"
    }
)

if response.status_code == 200:
    chunks = response.json()
    print(f"✅ {len(chunks)} Chunks gefunden\n")
    
    for i, chunk in enumerate(chunks, 1):
        text_length = len(chunk.get('text_chunk', ''))
        print(f"Chunk #{i}:")
        print(f"  - ID: {chunk['id'][:8]}...")
        print(f"  - Länge: {text_length} Zeichen")
        print(f"  - Seiten: {chunk.get('page_start', '?')} - {chunk.get('page_end', '?')}")
        print(f"  - Vorschau: {chunk.get('text_chunk', '')[:100]}...")
        print()
    
    # Durchschnittliche Chunk-Größe
    avg_length = sum(len(c.get('text_chunk', '')) for c in chunks) / len(chunks)
    print(f"📈 Durchschnittliche Chunk-Größe: {avg_length:.0f} Zeichen")
    
    if avg_length < 100:
        print("⚠️  WARNUNG: Chunks sind sehr klein! (< 100 Zeichen)")
        print("   Das könnte zu schlechten Suchergebnissen führen.")
    elif avg_length < 500:
        print("⚠️  Chunks sind relativ klein (< 500 Zeichen)")
    else:
        print("✅ Chunk-Größe sieht gut aus!")
else:
    print(f"❌ Fehler beim Abrufen der Chunks: {response.status_code}")
    print(response.text)

# ============================================================================
# 2. Agent testen
# ============================================================================
print("\n" + "=" * 80)
print("🤖 2. AGENT TESTEN")
print("-" * 80)

# Prüfe ob API läuft
try:
    health_response = requests.get("http://localhost:8000/health", timeout=5)
    if health_response.status_code == 200:
        print("✅ API läuft auf http://localhost:8000")
    else:
        print(f"⚠️  API antwortet mit Status {health_response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"❌ API nicht erreichbar: {e}")
    print("   Bitte starte die API mit: python backend/main.py")
    exit(1)

# Test 1: Fehlercode-Suche
print("\n📝 Test 1: Fehlercode-Suche")
print("-" * 40)

test_query = "Konica Minolta C3320i Fehler C9402"
print(f"Query: {test_query}")

try:
    search_response = requests.post(
        "http://localhost:8000/search/error-codes",
        json={"query": test_query},
        timeout=30
    )
    
    if search_response.status_code == 200:
        results = search_response.json()
        print(f"✅ {len(results)} Ergebnisse gefunden")
        
        if results:
            print("\nTop Ergebnis:")
            top = results[0]
            print(f"  - Fehlercode: {top.get('error_code', 'N/A')}")
            print(f"  - Beschreibung: {top.get('error_description', 'N/A')[:100]}...")
            print(f"  - Confidence: {top.get('confidence_score', 0):.2f}")
            print(f"  - Hersteller: {top.get('manufacturer_name', 'N/A')}")
        else:
            print("⚠️  Keine Ergebnisse gefunden")
    else:
        print(f"❌ Fehler: {search_response.status_code}")
        print(search_response.text[:500])
except Exception as e:
    print(f"❌ Fehler beim Testen: {e}")

# Test 2: Semantic Search
print("\n📝 Test 2: Semantic Search (Vector Search)")
print("-" * 40)

semantic_query = "Wie behebe ich einen Papierstau?"
print(f"Query: {semantic_query}")

try:
    semantic_response = requests.post(
        "http://localhost:8000/search/semantic",
        json={
            "query": semantic_query,
            "limit": 3
        },
        timeout=30
    )
    
    if semantic_response.status_code == 200:
        results = semantic_response.json()
        print(f"✅ {len(results)} Ergebnisse gefunden")
        
        if results:
            print("\nTop Ergebnis:")
            top = results[0]
            print(f"  - Text: {top.get('text_chunk', 'N/A')[:150]}...")
            print(f"  - Similarity: {top.get('similarity', 0):.3f}")
            print(f"  - Seite: {top.get('page_start', 'N/A')}")
        else:
            print("⚠️  Keine Ergebnisse gefunden")
    else:
        print(f"❌ Fehler: {semantic_response.status_code}")
        print(semantic_response.text[:500])
except Exception as e:
    print(f"❌ Fehler beim Testen: {e}")

print("\n" + "=" * 80)
print("✅ Tests abgeschlossen!")
print("=" * 80)
