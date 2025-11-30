"""Auth smoke test script for local admin login."""

import json
import os
import sys
from datetime import datetime

import requests


def parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    base_url = os.getenv("AUTH_BASE_URL", "http://localhost:8000").rstrip("/")
    username = os.getenv("AUTH_TEST_USERNAME") or os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    password = os.getenv("AUTH_TEST_PASSWORD") or os.getenv("DEFAULT_ADMIN_PASSWORD")
    remember_me = parse_bool(os.getenv("AUTH_TEST_REMEMBER"))

    if not password:
        print("ERROR: Admin password not provided via AUTH_TEST_PASSWORD or DEFAULT_ADMIN_PASSWORD.", file=sys.stderr)
        return 2

    payload = {
        "username": username,
        "password": password,
        "remember_me": remember_me,
    }

    url = f"{base_url}/api/v1/auth/login"
    print(f"[{datetime.utcnow().isoformat()}] POST {url}")
    print("Payload:", json.dumps({**payload, "password": "***"}))

    try:
        response = requests.post(url, json=payload, timeout=10)
    except requests.RequestException as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 3

    print(f"Status: {response.status_code}")
    print("Response:", response.text)

    if response.status_code != 200:
        return 4

    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON response: {exc}", file=sys.stderr)
        return 5

    success = data.get("success") is True
    tokens = data.get("data", {})
    access_token = tokens.get("access_token")

    if not success or not access_token:
        print("Missing success flag or access token in response", file=sys.stderr)
        return 6

    print("Auth smoke test succeeded. Access token received.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
