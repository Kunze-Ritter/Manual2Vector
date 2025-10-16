"""
Delete ALL processed data from database
WARNING: This will delete EVERYTHING except manufacturers!
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env.database')

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

print("="*60)
print("⚠️  DELETE ALL PROCESSED DATA")
print("="*60)
print("\nThis will delete:")
print("  - All documents")
print("  - All chunks")
print("  - All error codes")
print("  - All parts")
print("  - All products")
print("  - All product series")
print("  - All bulletins")
print("  - All videos")
print("\nManufacturers will be KEPT!")

# Ask for confirmation
print("\n" + "="*60)
response = input("Type 'DELETE ALL' to confirm: ")

if response != 'DELETE ALL':
    print("\n❌ Cancelled")
    exit(0)

print("\n" + "="*60)
print("DELETING ALL DATA...")
print("="*60)

# Delete in correct order (foreign key constraints)

try:
    # 1. Delete error codes
    print("\n1. Deleting error codes...")
    result = supabase.table('error_codes').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    print(f"   ✅ Deleted error codes")

    # 2. Delete chunks
    print("\n2. Deleting chunks...")
    result = supabase.table('chunks').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    print(f"   ✅ Deleted chunks")

    # 3. Delete parts
    print("\n3. Deleting parts...")
    result = supabase.table('parts_catalog').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    print(f"   ✅ Deleted parts")

    # 4. Delete products
    print("\n4. Deleting products...")
    result = supabase.table('products').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    print(f"   ✅ Deleted products")

    # 5. Delete product series
    print("\n5. Deleting product series...")
    result = supabase.table('product_series').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    print(f"   ✅ Deleted product series")

    # 6. Delete bulletins
    print("\n6. Deleting bulletins...")
    result = supabase.table('bulletins').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    print(f"   ✅ Deleted bulletins")

    # 7. Delete videos
    print("\n7. Deleting videos...")
    result = supabase.table('videos').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    print(f"   ✅ Deleted videos")

    # 8. Delete documents (last because of foreign keys)
    print("\n8. Deleting documents...")
    result = supabase.table('documents').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    print(f"   ✅ Deleted documents")

    print("\n" + "="*60)
    print("✅ ALL DATA DELETED SUCCESSFULLY")
    print("="*60)
    print("\nManufacturers were kept.")
    print("You can now reprocess PDFs with improved extractors!")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nSome data may have been partially deleted.")
    print("Check Supabase dashboard for details.")
