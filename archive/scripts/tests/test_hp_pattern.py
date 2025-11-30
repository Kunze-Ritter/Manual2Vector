#!/usr/bin/env python3
"""Test HP error code pattern"""

import re

test_codes = [
    "30.03.30",
    "31.13.02",
    "59.00.03",
    "99.09.67",
    "10.0x.12",
    "50.1X.20"
]

# Current pattern
pattern = r'^\d{2}\.\d{2}\.\d{2}$'

print("\n" + "=" * 80)
print("HP ERROR CODE PATTERN TEST")
print("=" * 80)

print(f"\nPattern: {pattern}\n")

for code in test_codes:
    match = re.match(pattern, code)
    status = "✅ MATCH" if match else "❌ NO MATCH"
    print(f"{status}: {code}")
    
    # Analyze
    parts = code.split('.')
    print(f"   Parts: {parts}")
    print(f"   Lengths: {[len(p) for p in parts]}")

print("\n" + "=" * 80)
