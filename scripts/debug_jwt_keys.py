"""Utility script to verify JWT key environment variables."""

from __future__ import annotations

import os
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


def _build_pem(label: str, key: str | None) -> bytes:
    if not key:
        raise ValueError(f"Missing {label} environment variable")
    return f"-----BEGIN {label}-----\n{key.strip()}\n-----END {label}-----\n".encode()


def main() -> int:
    private_key = os.getenv("JWT_PRIVATE_KEY")
    public_key = os.getenv("JWT_PUBLIC_KEY")

    print(f"private len: {len(private_key) if private_key else None}")
    print(f"public len: {len(public_key) if public_key else None}")

    try:
        pem_private = _build_pem("PRIVATE KEY", private_key)
        serialization.load_pem_private_key(pem_private, password=None, backend=default_backend())
        print("private key ✅ parsed successfully")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"private key ❌ parse failed: {exc}")
        return 2

    try:
        pem_public = _build_pem("PUBLIC KEY", public_key)
        serialization.load_pem_public_key(pem_public, backend=default_backend())
        print("public key ✅ parsed successfully")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"public key ❌ parse failed: {exc}")
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
