"""
Cleanup Database - Delete all processed data for fresh start

⚠️  WARNING: This will delete ALL documents, products, videos, links, images!
⚠️  Manufacturers and product_series will be kept.

Usage:
    python scripts/cleanup_database.py
    python scripts/cleanup_database.py --confirm  # Skip confirmation prompt
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from processors.logger import get_logger

logger = get_logger()


def cleanup_database(skip_confirm: bool = False):
    """
    Delete all processed data from database
    
    Deletes:
    - All documents (CASCADE deletes chunks, embeddings)
    - All products and document-product relationships
    - All videos, links, images
    - All intelligence chunks
    - Processing queue
    
    Keeps:
    - Manufacturers
    - Product series
    - All views and functions
    """
    
    # Load environment from root directory
    root_dir = Path(__file__).parent.parent
    env_path = root_dir / '.env'
    load_dotenv(env_path)
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("❌ SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set!")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Get current counts
    logger.info("📊 Current database state:")
    try:
        docs = supabase.table('vw_documents').select('id', count='exact').execute()
        products = supabase.table('vw_products').select('id', count='exact').execute()
        videos = supabase.table('vw_videos').select('id', count='exact').execute()
        links = supabase.table('vw_links').select('id', count='exact').execute()
        chunks = supabase.table('vw_chunks').select('id', count='exact').execute()
        
        logger.info(f"   Documents: {docs.count or 0}")
        logger.info(f"   Products: {products.count or 0}")
        logger.info(f"   Videos: {videos.count or 0}")
        logger.info(f"   Links: {links.count or 0}")
        logger.info(f"   Chunks: {chunks.count or 0}")
    except Exception as e:
        logger.warning(f"Could not get counts: {e}")
    
    # Confirmation
    if not skip_confirm:
        logger.warning("\n⚠️  WARNING: This will DELETE ALL processed data!")
        logger.warning("⚠️  Manufacturers and product_series will be kept.")
        response = input("\n❓ Are you sure? Type 'DELETE' to confirm: ")
        
        if response != "DELETE":
            logger.info("❌ Cancelled by user")
            return False
    
    logger.info("\n🗑️  Starting database cleanup...")
    
    try:
        # 1. Delete content (videos, links, images)
        logger.info("1/8: Deleting videos...")
        supabase.table('vw_videos').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        logger.info("2/8: Deleting links...")
        supabase.table('vw_links').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        logger.info("3/8: Deleting images...")
        supabase.table('vw_images').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # 2. Delete intelligence chunks
        logger.info("4/8: Deleting intelligence chunks...")
        supabase.table('vw_intelligence_chunks').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # 3. Delete products and relationships
        logger.info("5/8: Deleting document-product relationships...")
        supabase.table('vw_document_products').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        logger.info("6/8: Deleting products...")
        supabase.table('vw_products').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # 4. Delete embeddings
        logger.info("7/8: Deleting embeddings...")
        supabase.table('vw_embeddings').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # 5. Delete chunks
        logger.info("8/8: Deleting chunks...")
        supabase.table('vw_chunks').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # 6. Delete documents (CASCADE will handle rest)
        logger.info("9/9: Deleting documents...")
        supabase.table('vw_documents').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # 7. Clear processing queue
        logger.info("Clearing processing queue...")
        supabase.table('vw_processing_queue').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        logger.success("\n✅ Database cleanup completed!")
        logger.info("\n📊 What was kept:")
        logger.info("   ✅ Manufacturers")
        logger.info("   ✅ Product Series")
        logger.info("   ✅ All Views and Functions")
        
        logger.info("\n🚀 Ready for fresh processing!")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Cleanup failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cleanup database for fresh start")
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    success = cleanup_database(skip_confirm=args.confirm)
    sys.exit(0 if success else 1)
