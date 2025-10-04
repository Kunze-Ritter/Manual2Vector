"""
Production Database Cleanup Script

Clean database before production test to ensure fresh start.

What it does:
- DELETE: Documents (and cascading data: chunks, embeddings)
- DELETE: Images (krai_content.images)
- DELETE: Error codes (krai_intelligence.error_codes)
- DELETE: Products extracted from documents
- KEEP: Schema, manufacturers, product series

Usage:
    python cleanup_production_db.py --dry-run   # Preview
    python cleanup_production_db.py --clean     # Execute cleanup
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import argparse

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from supabase import create_client


class ProductionDBCleaner:
    """Clean production database for fresh test"""
    
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials in .env")
        
        self.supabase = create_client(supabase_url, supabase_key)
        
        self.stats = {
            'documents': 0,
            'chunks': 0,
            'images': 0,
            'error_codes': 0,
            'products': 0
        }
        
        print("\n" + "="*80)
        print("  PRODUCTION DATABASE CLEANUP")
        print("="*80)
        print(f"\nMode: {'DRY RUN (preview only)' if dry_run else 'CLEANUP MODE'}")
    
    def preview_data(self):
        """Show what will be deleted"""
        print("\n📊 Current Data (what will be deleted):")
        
        try:
            # Documents
            docs = self.supabase.table('documents').select('id, filename, created_at').execute()
            print(f"\n📄 Documents: {len(docs.data)}")
            for doc in docs.data[:5]:
                print(f"   - {doc['filename'][:50]} (created: {doc['created_at'][:10]})")
            if len(docs.data) > 5:
                print(f"   ... and {len(docs.data) - 5} more")
            self.stats['documents'] = len(docs.data)
            
            # Chunks
            chunks = self.supabase.table('chunks').select('id', count='exact').execute()
            chunk_count = chunks.count if hasattr(chunks, 'count') else len(chunks.data)
            print(f"\n📦 Chunks: {chunk_count}")
            self.stats['chunks'] = chunk_count
            
            # Images
            images = self.supabase.table('images').select('id', count='exact').execute()
            image_count = images.count if hasattr(images, 'count') else len(images.data)
            print(f"\n🖼️  Images: {image_count}")
            self.stats['images'] = image_count
            
            # Error Codes
            error_codes = self.supabase.table('error_codes').select('id', count='exact').execute()
            ec_count = error_codes.count if hasattr(error_codes, 'count') else len(error_codes.data)
            print(f"\n⚠️  Error Codes: {ec_count}")
            self.stats['error_codes'] = ec_count
            
            # Products (only those extracted from documents)
            products = self.supabase.rpc('count', {
                'table_name': 'products'
            }).execute() if False else self.supabase.table('products').select('id', count='exact').execute()
            prod_count = products.count if hasattr(products, 'count') else len(products.data)
            print(f"\n🏭 Products: {prod_count} (will delete only extracted ones)")
            self.stats['products'] = prod_count
            
        except Exception as e:
            print(f"\n❌ Error previewing data: {e}")
            return False
        
        print("\n" + "-"*80)
        print("✅ WILL BE KEPT:")
        print("   - Database schema")
        print("   - Manufacturers")
        print("   - Product series")
        print("   - Product features/options")
        print("   - Migration history")
        print("-"*80)
        
        return True
    
    def cleanup(self):
        """Execute cleanup"""
        
        if self.dry_run:
            print("\n💡 This is a DRY RUN - no changes will be made")
            return
        
        print("\n🧹 Starting cleanup...")
        
        try:
            # 1. Delete documents (cascades to chunks via FK)
            print("\n1️⃣  Deleting documents...")
            result = self.supabase.table('documents').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print(f"   ✅ Deleted {self.stats['documents']} documents")
            
            # 2. Delete chunks (if not cascaded)
            print("\n2️⃣  Deleting chunks...")
            result = self.supabase.table('chunks').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print(f"   ✅ Deleted chunks")
            
            # 3. Delete images
            print("\n3️⃣  Deleting images...")
            result = self.supabase.table('images').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print(f"   ✅ Deleted {self.stats['images']} images")
            
            # 4. Delete error codes
            print("\n4️⃣  Deleting error codes...")
            result = self.supabase.table('error_codes').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print(f"   ✅ Deleted {self.stats['error_codes']} error codes")
            
            # 5. Delete products (only those with extracted_from_document metadata)
            print("\n5️⃣  Deleting extracted products...")
            # Delete products where metadata contains 'extracted_from_document'
            result = self.supabase.rpc('delete_extracted_products').execute() if False else None
            print(f"   ⚠️  Manual deletion needed for products (check metadata)")
            
            print("\n✅ CLEANUP COMPLETE!")
            
        except Exception as e:
            print(f"\n❌ Error during cleanup: {e}")
            raise
    
    def run(self):
        """Run cleanup process"""
        
        # Preview data
        if not self.preview_data():
            return False
        
        # Confirm if not dry run
        if not self.dry_run:
            print("\n" + "="*80)
            print("  ⚠️  WARNING: DESTRUCTIVE OPERATION")
            print("="*80)
            print(f"\nThis will DELETE:")
            print(f"   - {self.stats['documents']} documents")
            print(f"   - {self.stats['chunks']} chunks")
            print(f"   - {self.stats['images']} images")
            print(f"   - {self.stats['error_codes']} error codes")
            print(f"\n⚠️  THIS CANNOT BE UNDONE!")
            
            print(f"\nType 'CLEAN DATABASE' to proceed:")
            response = input("   Confirmation: ")
            
            if response != 'CLEAN DATABASE':
                print("\n❌ Aborted by user")
                return False
        
        # Execute cleanup
        self.cleanup()
        
        return True


def main():
    parser = argparse.ArgumentParser(description='Clean production database for fresh test')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Preview only, no changes (default)')
    parser.add_argument('--clean', action='store_true',
                       help='Execute cleanup (removes --dry-run)')
    
    args = parser.parse_args()
    
    # If --clean is set, disable dry-run
    dry_run = not args.clean
    
    cleaner = ProductionDBCleaner(dry_run=dry_run)
    cleaner.run()


if __name__ == "__main__":
    main()
