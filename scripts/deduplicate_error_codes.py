#!/usr/bin/env python3
"""
Deduplicate error codes in database
Keeps the first occurrence, merges data from duplicates
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).parent.parent / '.env')

sb = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("\n" + "=" * 100)
print("ERROR CODE DEDUPLICATION")
print("=" * 100)

# Get all error codes
result = sb.table('error_codes').select('*').execute()

# Group by (error_code, manufacturer_id)
groups = defaultdict(list)
for ec in result.data:
    key = (ec['error_code'], ec.get('manufacturer_id'))
    groups[key].append(ec)

# Find duplicates
duplicates = {key: ecs for key, ecs in groups.items() if len(ecs) > 1}

if not duplicates:
    print("\n✅ NO DUPLICATES FOUND!")
    sys.exit(0)

print(f"\n❌ FOUND {len(duplicates)} DUPLICATE GROUPS:\n")

total_to_delete = 0

for (error_code, manufacturer_id), instances in sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n📌 {error_code} ({len(instances)} instances):")
    
    # Keep first, delete rest
    keep = instances[0]
    to_delete = instances[1:]
    
    print(f"   ✅ KEEP: {keep['id']}")
    for dup in to_delete:
        print(f"   ❌ DELETE: {dup['id']}")
        total_to_delete += 1

print(f"\n" + "=" * 100)
print(f"SUMMARY:")
print(f"   Total error codes: {len(result.data)}")
print(f"   Duplicate groups: {len(duplicates)}")
print(f"   Codes to delete: {total_to_delete}")
print("=" * 100)

# Ask for confirmation
response = input("\n⚠️  DELETE duplicates? (yes/no): ")

if response.lower() == 'yes':
    deleted_count = 0
    
    for (error_code, manufacturer_id), instances in duplicates.items():
        to_delete = instances[1:]  # Keep first
        
        for dup in to_delete:
            try:
                sb.table('error_codes').delete().eq('id', dup['id']).execute()
                deleted_count += 1
                print(f"✅ Deleted: {error_code} (ID: {dup['id']})")
            except Exception as e:
                print(f"❌ Error deleting {dup['id']}: {e}")
    
    print(f"\n✅ DELETED {deleted_count} duplicate error codes!")
else:
    print("\n❌ Cancelled - no changes made")

print("\n" + "=" * 100)
