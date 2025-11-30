"""
Cleanup Database - Delete all processed data for fresh start

⚠️  WARNING: This will delete ALL documents, products, videos, links, images!
⚠️  Manufacturers and product_series will be kept.

Usage:
    python scripts/cleanup_database.py
    python scripts/cleanup_database.py --confirm  # Skip confirmation prompt
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.migration_helpers import (
    create_connected_adapter,
    pg_execute,
    pg_fetch_all,
    run_async,
)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from processors.logger import get_logger

logger = get_logger()


async def cleanup_database(skip_confirm: bool = False) -> bool:
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

    # Create connected PostgreSQL adapter via shared migration helpers
    try:
        adapter = await create_connected_adapter(database_type="postgresql")
    except Exception as e:
        logger.error(f"❌ Failed to create database adapter: {e}")
        return False

    # Get current counts via direct SQL against documented tables
    logger.info("📊 Current database state:")
    try:
        counts = {}
        queries = {
            "documents": "SELECT COUNT(*) AS count FROM krai_core.documents",
            "products": "SELECT COUNT(*) AS count FROM krai_core.products",
            "videos": "SELECT COUNT(*) AS count FROM krai_content.videos",
            "links": "SELECT COUNT(*) AS count FROM krai_content.links",
            "chunks": "SELECT COUNT(*) AS count FROM krai_intelligence.chunks",
        }

        for key, query in queries.items():
            rows = await pg_fetch_all(adapter, query)
            counts[key] = rows[0]["count"] if rows else 0

        logger.info(f"   Documents: {counts['documents']}")
        logger.info(f"   Products: {counts['products']}")
        logger.info(f"   Videos: {counts['videos']}")
        logger.info(f"   Links: {counts['links']}")
        logger.info(f"   Chunks: {counts['chunks']}")
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
        await pg_execute(adapter, "DELETE FROM krai_content.videos")

        logger.info("2/8: Deleting links...")
        await pg_execute(adapter, "DELETE FROM krai_content.links")

        logger.info("3/8: Deleting images...")
        await pg_execute(adapter, "DELETE FROM krai_content.images")

        # 2. Delete intelligence chunks (includes embeddings)
        logger.info("4/8: Deleting intelligence chunks (including embeddings)...")
        await pg_execute(adapter, "DELETE FROM krai_intelligence.chunks")

        # 3. Delete products and relationships
        logger.info("5/8: Deleting document-product relationships...")
        await pg_execute(adapter, "DELETE FROM krai_core.document_products")

        logger.info("6/8: Deleting products...")
        await pg_execute(adapter, "DELETE FROM krai_core.products")

        # 4. Delete chunks alias/views are already covered by intelligence.chunks
        logger.info("7/8: Chunks/embeddings views are backed by krai_intelligence.chunks (already cleared)")

        # 5. Delete documents (CASCADE will handle remaining relations)
        logger.info("8/8: Deleting documents...")
        await pg_execute(adapter, "DELETE FROM krai_core.documents")

        # 6. Clear processing queue
        logger.info("Clearing processing queue...")
        await pg_execute(adapter, "DELETE FROM krai_system.processing_queue")

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

    success = run_async(cleanup_database(skip_confirm=args.confirm))
    sys.exit(0 if success else 1)
