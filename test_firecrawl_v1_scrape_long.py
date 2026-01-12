"""\
Long-timeout end-to-end test for Firecrawl v1 scrape endpoint.

Goals:
- Use a v1-valid request body (strict schema: avoid unrecognized keys like webhook)
- Use a long client timeout so we can observe real behavior
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    firecrawl_url = os.getenv("FIRECRAWL_API_URL", "http://localhost:9004").rstrip("/")
    api_key = os.getenv("FIRECRAWL_API_KEY", "fc-local-dev-key-not-required")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "url": "https://example.com",
        "formats": ["markdown", "html"],
        "onlyMainContent": True,
        "timeout": 180000,
        "waitFor": 0,
        "blockAds": True,
        "proxy": "basic",
        "parsePDF": True,
    }

    url = f"{firecrawl_url}/v1/scrape"

    print("=" * 80)
    print("🔍 Firecrawl v1 scrape (long timeout)")
    print("=" * 80)
    print(f"URL: {url}")
    print("Payload keys:", ", ".join(sorted(payload.keys())))
    print()

    timeout_seconds = 240.0
    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.post(url, json=payload, headers=headers)

    print("Status:", response.status_code)
    print("Body (first 500 chars):")
    print(response.text[:500])


if __name__ == "__main__":
    main()
