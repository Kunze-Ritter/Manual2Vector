"""
Sync OEM Relationships to Database
===================================

Syncs OEM mappings from oem_mappings.py to Supabase database.
Also updates existing products with OEM information.

Usage:
    # Sync OEM relationships only
    python scripts/sync_oem_to_database.py
    
    # Sync OEM relationships AND update products
    python scripts/sync_oem_to_database.py --update-products
    
    # Dry run (show what would be done)
    python scripts/sync_oem_to_database.py --dry-run
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from supabase import create_client
from processors.env_loader import load_all_env_files
from utils.oem_sync import (
    sync_oem_relationships_to_db,
    batch_update_products_oem_info
)

# Load environment variables (consolidated + legacy overrides)
project_root = Path(__file__).parent.parent
loaded_env_files = load_all_env_files(project_root)
print("Loading environment variables...")
for env_file in loaded_env_files:
    print(f"  ✓ Loaded: {env_file}")

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n❌ Error: SUPABASE credentials not found")
    sys.exit(1)

print(f"✓ Connected to Supabase: {SUPABASE_URL}\n")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def main():
    """Main entry point"""
    dry_run = '--dry-run' in sys.argv
    update_products = '--update-products' in sys.argv
    
    print("=" * 80)
    print(f"OEM Relationships Sync {'(DRY RUN)' if dry_run else ''}")
    print("=" * 80)
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made to database")
        print("\nThis would:")
        print("  1. Sync 32 OEM mappings to oem_relationships table")
        if update_products:
            print("  2. Update all products with OEM information")
        print("\nRun without --dry-run to execute")
        return
    
    # Step 1: Sync OEM relationships
    print("\n" + "=" * 80)
    print("Step 1: Syncing OEM Relationships to Database")
    print("=" * 80)
    
    stats = sync_oem_relationships_to_db(supabase)
    
    print(f"\n✅ OEM Relationships Sync Complete:")
    print(f"   Total mappings: {stats['total_mappings']}")
    print(f"   Inserted: {stats['inserted']}")
    print(f"   Updated: {stats['updated']}")
    print(f"   Errors: {stats['errors']}")
    
    # Step 2: Update products (optional)
    if update_products:
        print("\n" + "=" * 80)
        print("Step 2: Updating Products with OEM Information")
        print("=" * 80)
        
        product_stats = batch_update_products_oem_info(supabase, limit=10000)
        
        print(f"\n✅ Products Update Complete:")
        print(f"   Total products: {product_stats['total_products']}")
        print(f"   Updated with OEM: {product_stats['updated']}")
        print(f"   No OEM relationship: {product_stats['no_oem']}")
        print(f"   Errors: {product_stats['errors']}")
    else:
        print("\n💡 Tip: Use --update-products to also update existing products with OEM info")
    
    print("\n" + "=" * 80)
    print("Sync Complete!")
    print("=" * 80)
    
    print("\nWhat's next:")
    print("  1. OEM relationships are now in database")
    print("  2. Search queries will automatically expand to include OEM equivalents")
    print("  3. Example: Search 'Konica Minolta 5000i' will also find Brother documents")
    
    if not update_products:
        print("\n  Run with --update-products to update existing products:")
        print("  python scripts/sync_oem_to_database.py --update-products")


if __name__ == '__main__':
    main()
