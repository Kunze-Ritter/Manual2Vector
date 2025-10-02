import asyncio
import httpx

async def test_model():
    try:
        client = httpx.AsyncClient(timeout=30.0)
        print("Testing llava:7b...")
        resp = await client.post(
            'http://localhost:11434/api/generate',
            json={'model': 'llava:7b', 'prompt': 'Say OK', 'stream': False}
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("✓ Model works!")
            print(resp.json())
        else:
            print(f"✗ Error: {resp.text[:200]}")
    except Exception as e:
        print(f"✗ Exception: {e}")

asyncio.run(test_model())
