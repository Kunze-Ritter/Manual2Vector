"""Test improved OpenAI responses"""
import requests

API_URL = "http://localhost:8000"

print("=" * 80)
print("🤖 TEST: VERBESSERTE ANTWORTEN")
print("=" * 80)

test_cases = [
    {
        "name": "Fehlercode C9402",
        "query": "Konica Minolta C3320i Fehler C9402"
    },
    {
        "name": "HP Fehler 66.60.30",
        "query": "HP Fehler 66.60.30"
    },
    {
        "name": "Allgemeine Frage",
        "query": "Wie behebe ich einen Papierstau?"
    }
]

for test in test_cases:
    print(f"\n{'=' * 80}")
    print(f"📝 Test: {test['name']}")
    print(f"Query: {test['query']}")
    print("=" * 80)
    
    try:
        response = requests.post(
            f"{API_URL}/v1/chat/completions",
            json={
                "model": "krai-assistant",
                "messages": [{"role": "user", "content": test['query']}],
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            message = data['choices'][0]['message']['content']
            
            print("\n📌 Antwort:")
            print("-" * 80)
            print(message)
            print("-" * 80)
            
            # Stats
            usage = data.get('usage', {})
            print(f"\n📊 Tokens: {usage.get('total_tokens', 0)}")
            print(f"📏 Länge: {len(message)} Zeichen")
        else:
            print(f"❌ Error {response.status_code}")
            print(response.text[:500])
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    input("\n⏸️  Drücke Enter für nächsten Test...")

print("\n" + "=" * 80)
print("✅ Alle Tests abgeschlossen!")
print("=" * 80)
