#!/usr/bin/env python3
"""Check for duplicate error codes in database"""

import os
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).parent.parent / '.env')

sb = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Get all error codes
result = sb.table('error_codes').select('error_code,manufacturer_id,id').execute()

print("\n" + "=" * 100)
print("DUPLICATE ERROR CODES CHECK")
print("=" * 100)

# Count by error_code
code_counts = Counter(ec['error_code'] for ec in result.data)

# Find duplicates
duplicates = {code: count for code, count in code_counts.items() if count > 1}

if duplicates:
    print(f"\n❌ FOUND {len(duplicates)} DUPLICATE ERROR CODES:\n")
    
    for code, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True):
        print(f"   {code}: {count} times")
        
        # Show details
        instances = [ec for ec in result.data if ec['error_code'] == code]
        for inst in instances:
            print(f"      - ID: {inst['id']}, Manufacturer: {inst.get('manufacturer_id', 'N/A')}")
else:
    print("\n✅ NO DUPLICATES FOUND!")

print(f"\nTOTAL ERROR CODES: {len(result.data)}")
print(f"UNIQUE ERROR CODES: {len(code_counts)}")
print("=" * 100)

# Check specific codes
test_codes = ["30.03.30", "30.03", "30.3.30"]

for test_code in test_codes:
    test_result = sb.table('error_codes').select('*').eq('error_code', test_code).execute()
    
    print(f"\n🔍 CHECKING CODE: {test_code}")
    if test_result.data:
        print(f"✅ Found {len(test_result.data)} instance(s)")
        for ec in test_result.data:
            print(f"   - ID: {ec['id']}")
            print(f"   - Manufacturer: {ec.get('manufacturer_id', 'N/A')}")
            print(f"   - Description: {ec.get('error_description', 'N/A')[:80]}...")
    else:
        print(f"❌ NOT FOUND in database!")

# Check all codes starting with 30
print(f"\n🔍 ALL CODES STARTING WITH '30.':")
result_30 = sb.table('error_codes').select('error_code').ilike('error_code', '30.%').execute()
if result_30.data:
    for ec in result_30.data[:10]:
        print(f"   - {ec['error_code']}")
    if len(result_30.data) > 10:
        print(f"   ... and {len(result_30.data) - 10} more")
else:
    print("   ❌ No codes found")

print("\n" + "=" * 100)
