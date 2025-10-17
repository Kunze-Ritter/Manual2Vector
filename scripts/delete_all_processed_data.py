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
    # Delete in batches to avoid timeout
    def delete_table_in_batches(table_name, batch_size=500):
        """Delete all rows from a table in batches"""
        total_deleted = 0
        while True:
            # Get batch of IDs
            result = supabase.table(table_name).select('id').limit(batch_size).execute()
            
            if not result.data or len(result.data) == 0:
                break
            
            # Delete batch by ID
            ids_to_delete = [row['id'] for row in result.data]
            for chunk_start in range(0, len(ids_to_delete), 100):  # Delete in chunks of 100
                chunk = ids_to_delete[chunk_start:chunk_start + 100]
                supabase.table(table_name).delete().in_('id', chunk).execute()
            
            total_deleted += len(ids_to_delete)
            print(f"   Deleted {total_deleted} rows...", end='\r')
        
        return total_deleted
    
    # 1. Delete error codes
    print("\n1. Deleting error codes...")
    count = delete_table_in_batches('error_codes')
    print(f"   ✅ Deleted {count} error codes")

    # 2. Delete chunks
    print("\n2. Deleting chunks...")
    count = delete_table_in_batches('chunks')
    print(f"   ✅ Deleted {count} chunks")

    # 3. Delete parts
    print("\n3. Deleting parts...")
    count = delete_table_in_batches('parts_catalog')
    print(f"   ✅ Deleted {count} parts")

    # 4. Delete products
    print("\n4. Deleting products...")
    count = delete_table_in_batches('products')
    print(f"   ✅ Deleted {count} products")

    # 5. Delete product series
    print("\n5. Deleting product series...")
    count = delete_table_in_batches('product_series')
    print(f"   ✅ Deleted {count} series")

    # 6. Delete bulletins (if exists)
    print("\n6. Deleting bulletins...")
    try:
        count = delete_table_in_batches('bulletins')
        print(f"   ✅ Deleted {count} bulletins")
    except Exception as e:
        print(f"   ⚠️  Table not found, skipping")

    # 7. Delete videos (if exists)
    print("\n7. Deleting videos...")
    try:
        count = delete_table_in_batches('videos')
        print(f"   ✅ Deleted {count} videos")
    except Exception as e:
        print(f"   ⚠️  Table not found, skipping")

    # 8. Delete images
    print("\n8. Deleting images...")
    try:
        count = delete_table_in_batches('images')
        print(f"   ✅ Deleted {count} images")
    except Exception as e:
        print(f"   ⚠️  Table not found, skipping")

    # 9. Delete links (external links/videos)
    print("\n9. Deleting links...")
    try:
        count = delete_table_in_batches('links')
        print(f"   ✅ Deleted {count} links")
    except Exception as e:
        print(f"   ⚠️  Table not found, skipping")

    # 10. Delete processing queue
    print("\n10. Deleting processing queue...")
    try:
        count = delete_table_in_batches('processing_queue')
        print(f"   ✅ Deleted {count} queue entries")
    except Exception as e:
        print(f"   ⚠️  Table not found, skipping")

    # 11. Delete documents (last because of foreign keys)
    print("\n11. Deleting documents...")
    count = delete_table_in_batches('documents')
    print(f"   ✅ Deleted {count} documents")

    print("\n" + "="*60)
    print("✅ ALL DATA DELETED SUCCESSFULLY")
    print("="*60)
    print("\nManufacturers were kept.")
    print("You can now reprocess PDFs with improved extractors!")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nSome data may have been partially deleted.")
    print("Check Supabase dashboard for details.")
