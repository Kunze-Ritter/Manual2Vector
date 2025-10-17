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
    count = delete_table_in_batches('vw_error_codes')
    print(f"   ✅ Deleted {count} error codes")

    # 2. Delete chunks
    print("\n2. Deleting chunks...")
    count = delete_table_in_batches('vw_chunks')
    print(f"   ✅ Deleted {count} chunks")

    # 3. Delete intelligence chunks
    print("\n3. Deleting intelligence chunks...")
    try:
        count = delete_table_in_batches('vw_intelligence_chunks')
        print(f"   ✅ Deleted {count} intelligence chunks")
    except Exception as e:
        print(f"   ⚠️  Table not found, skipping")

    # 4. Delete embeddings
    print("\n4. Deleting embeddings...")
    try:
        count = delete_table_in_batches('vw_embeddings')
        print(f"   ✅ Deleted {count} embeddings")
    except Exception as e:
        print(f"   ⚠️  Table not found, skipping")

    # 5. Delete parts
    print("\n5. Deleting parts...")
    count = delete_table_in_batches('vw_parts')
    print(f"   ✅ Deleted {count} parts")

    # 6. Delete document-product relationships
    print("\n6. Deleting document-product relationships...")
    try:
        count = delete_table_in_batches('vw_document_products')
        print(f"   ✅ Deleted {count} relationships")
    except Exception as e:
        print(f"   ⚠️  Table not found, skipping")

    # 7. Delete products
    print("\n7. Deleting products...")
    count = delete_table_in_batches('vw_products')
    print(f"   ✅ Deleted {count} products")

    # 8. Delete product series (optional - can keep for reuse)
    print("\n8. Deleting product series...")
    try:
        count = delete_table_in_batches('vw_product_series')
        print(f"   ✅ Deleted {count} series")
    except Exception as e:
        print(f"   ⚠️  Skipping (keeping for reuse)")

    # 9. Delete videos
    print("\n9. Deleting videos...")
    try:
        count = delete_table_in_batches('vw_videos')
        print(f"   ✅ Deleted {count} videos")
    except Exception as e:
        print(f"   ⚠️  Table not found, skipping")

    # 10. Delete images
    print("\n10. Deleting images...")
    try:
        count = delete_table_in_batches('vw_images')
        print(f"   ✅ Deleted {count} images")
    except Exception as e:
        print(f"   ⚠️  Table not found, skipping")

    # 11. Delete links (external links/videos)
    print("\n11. Deleting links...")
    try:
        count = delete_table_in_batches('vw_links')
        print(f"   ✅ Deleted {count} links")
    except Exception as e:
        print(f"   ⚠️  Table not found, skipping")

    # 12. Delete processing queue
    print("\n12. Deleting processing queue...")
    try:
        count = delete_table_in_batches('vw_processing_queue')
        print(f"   ✅ Deleted {count} queue entries")
    except Exception as e:
        print(f"   ⚠️  Table not found, skipping")

    # 13. Delete documents (last because of foreign keys)
    print("\n13. Deleting documents...")
    count = delete_table_in_batches('vw_documents')
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
