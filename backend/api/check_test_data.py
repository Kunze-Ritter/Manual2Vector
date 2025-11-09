"""
Quick check if test data exists in Supabase
"""

import os
import sys
from pathlib import Path

from supabase import create_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.processors.env_loader import load_all_env_files

# Load environment
load_all_env_files(PROJECT_ROOT)

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

print("="*60)
print("CHECKING TEST DATA IN SUPABASE")
print("="*60)

# 1. Check for error code C9402
print("\n1. Checking for error code C9402...")
result = supabase.table('vw_error_codes').select('*').ilike('error_code', '%C9402%').execute()
if result.data:
    print(f"   ✅ FOUND: {len(result.data)} results")
    for row in result.data[:2]:
        print(f"      - {row.get('error_code')}: {row.get('description', '')[:50]}...")
else:
    print("   ❌ NOT FOUND")

# 2. Check for error code 10.00.33
print("\n2. Checking for error code 10.00.33...")
result = supabase.table('vw_error_codes').select('*').ilike('error_code', '%10.00.33%').execute()
if result.data:
    print(f"   ✅ FOUND: {len(result.data)} results")
    for row in result.data[:2]:
        print(f"      - {row.get('error_code')}: {row.get('description', '')[:50]}...")
else:
    print("   ❌ NOT FOUND")

# 3. Check for HP E877 parts
print("\n3. Checking for HP E877 parts...")
result = supabase.table('vw_parts').select('*').ilike('part_number', '%E877%').execute()
if result.data:
    print(f"   ✅ FOUND: {len(result.data)} results")
    for row in result.data[:2]:
        print(f"      - {row.get('part_number')}: {row.get('manufacturer_name', 'Unknown')}")
else:
    print("   ❌ NOT FOUND - trying broader search...")
    result = supabase.table('vw_parts').select('*').limit(5).execute()
    if result.data:
        print(f"   Sample parts in DB:")
        for row in result.data[:3]:
            print(f"      - {row.get('part_number')}: {row.get('manufacturer_name', 'Unknown')}")

# 4. Check total counts
print("\n" + "="*60)
print("TOTAL COUNTS")
print("="*60)

error_codes = supabase.table('vw_error_codes').select('*', count='exact').limit(1).execute()
print(f"Error Codes: {error_codes.count}")

products = supabase.table('vw_products').select('*', count='exact').limit(1).execute()
print(f"Products: {products.count}")

parts = supabase.table('vw_parts').select('*', count='exact').limit(1).execute()
print(f"Parts: {parts.count}")

# 5. Sample some error codes
print("\n" + "="*60)
print("SAMPLE ERROR CODES (for better test queries)")
print("="*60)

sample_errors = supabase.table('vw_error_codes').select('error_code, error_description').limit(10).execute()
if sample_errors.data:
    for row in sample_errors.data:
        print(f"  - {row.get('error_code')}: {row.get('error_description', '')[:80]}...")

print("\n" + "="*60)
print("DONE")
print("="*60)
