#!/usr/bin/env python3
"""Check manufacturers in database"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).parent.parent / '.env')

sb = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

result = sb.table('manufacturers').select('id,name').execute()

print("\n" + "=" * 80)
print("MANUFACTURERS IN DATABASE")
print("=" * 80)

for m in result.data:
    print(f"  - {m['name']} (ID: {m['id']})")

print(f"\nTOTAL: {len(result.data)}")
print("=" * 80)

# Check for Lexmark specifically
lexmark = [m for m in result.data if 'lexmark' in m['name'].lower()]
if lexmark:
    print(f"\n✅ Lexmark found: {lexmark[0]['name']} (ID: {lexmark[0]['id']})")
else:
    print("\n❌ Lexmark NOT found in database!")
    print("\n💡 Need to create Lexmark manufacturer!")
