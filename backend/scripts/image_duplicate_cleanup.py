#!/usr/bin/env python3
"""
Image Duplicate Cleanup Script
Bereinigt Duplikate in der images Tabelle - behält das älteste Image, löscht die restlichen
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
import sys
import os
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.database_service_production import DatabaseService
from backend.core.data_models import ImageModel

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageDuplicateCleanup:
    def __init__(self):
        # Get environment variables
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        
        self.database_service = DatabaseService(supabase_url, supabase_key)
        self.cleaned_count = 0
        self.deleted_count = 0
        
    async def connect(self):
        """Connect to database"""
        await self.database_service.connect()
        logger.info("Connected to database")
    
    async def find_image_duplicates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Find all image duplicates grouped by file_hash"""
        logger.info("🔍 Searching for image duplicates...")
        
        try:
            # Get all images with their hashes
            result = self.database_service.client.table('vw_images').select('id, file_hash, filename, created_at, document_id').execute()
            
            if not result.data:
                logger.info("No images found in database")
                return {}
            
            # Group by file_hash
            hash_groups = {}
            for image in result.data:
                file_hash = image['file_hash']
                if file_hash not in hash_groups:
                    hash_groups[file_hash] = []
                hash_groups[file_hash].append(image)
            
            # Filter groups with duplicates
            duplicates = {hash_val: images for hash_val, images in hash_groups.items() if len(images) > 1}
            
            logger.info(f"📊 Found {len(duplicates)} groups of duplicate images")
            for hash_val, images in duplicates.items():
                logger.info(f"  Hash {hash_val[:16]}...: {len(images)} duplicates")
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Failed to find image duplicates: {e}")
            return {}
    
    async def cleanup_image_duplicates(self, duplicates: Dict[str, List[Dict[str, Any]]]):
        """Clean up image duplicates - keep oldest, delete rest"""
        logger.info(f"🧹 Starting cleanup of {len(duplicates)} duplicate groups...")
        
        for file_hash, images in duplicates.items():
            try:
                # Sort by created_at (oldest first)
                images_sorted = sorted(images, key=lambda x: x['created_at'])
                keep_image = images_sorted[0]  # Keep the oldest
                delete_images = images_sorted[1:]  # Delete the rest
                
                logger.info(f"📸 Hash {file_hash[:16]}...: Keeping {keep_image['id']} (oldest), deleting {len(delete_images)} duplicates")
                
                # Delete duplicate images
                for image in delete_images:
                    try:
                        # Delete from database
                        delete_result = self.database_service.client.table('vw_images').delete().eq('id', image['id']).execute()
                        
                        if delete_result.data:
                            self.deleted_count += 1
                            logger.info(f"  ✅ Deleted image {image['id']}")
                        else:
                            logger.warning(f"  ⚠️ Failed to delete image {image['id']}")
                            
                    except Exception as e:
                        logger.error(f"  ❌ Error deleting image {image['id']}: {e}")
                
                self.cleaned_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing duplicate group {file_hash[:16]}...: {e}")
        
        logger.info(f"🎉 Cleanup completed: {self.cleaned_count} groups cleaned, {self.deleted_count} images deleted")
    
    async def verify_cleanup(self):
        """Verify that cleanup was successful"""
        logger.info("🔍 Verifying cleanup...")
        
        try:
            # Check for remaining duplicates
            result = self.database_service.client.table('vw_images').select('file_hash').execute()
            
            if not result.data:
                logger.info("No images remaining")
                return True
            
            # Count by hash
            hash_counts = {}
            for image in result.data:
                file_hash = image['file_hash']
                hash_counts[file_hash] = hash_counts.get(file_hash, 0) + 1
            
            # Check for duplicates
            duplicates_found = sum(1 for count in hash_counts.values() if count > 1)
            
            if duplicates_found == 0:
                logger.info("✅ No duplicates found - cleanup successful!")
                return True
            else:
                logger.warning(f"⚠️ Found {duplicates_found} hash values still duplicated")
                return False
                
        except Exception as e:
            logger.error(f"Failed to verify cleanup: {e}")
            return False

async def main():
    """Main cleanup function"""
    logger.info("🚀 Starting Image Duplicate Cleanup")
    
    cleanup = ImageDuplicateCleanup()
    
    try:
        await cleanup.connect()
        
        # Find duplicates
        duplicates = await cleanup.find_image_duplicates()
        
        if not duplicates:
            logger.info("✅ No image duplicates found - database is clean!")
            return
        
        # Show summary
        total_duplicates = sum(len(images) - 1 for images in duplicates.values())
        logger.info(f"📊 Found {len(duplicates)} duplicate groups with {total_duplicates} duplicate images")
        
        # Ask for confirmation
        response = input(f"\n🗑️ Delete {total_duplicates} duplicate images? (y/N): ").strip().lower()
        if response != 'y':
            logger.info("❌ Cleanup cancelled by user")
            return
        
        # Cleanup
        await cleanup.cleanup_image_duplicates(duplicates)
        
        # Verify
        success = await cleanup.verify_cleanup()
        
        if success:
            logger.info("🎉 Image duplicate cleanup completed successfully!")
        else:
            logger.warning("⚠️ Cleanup completed but verification found issues")
            
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
    finally:
        # DatabaseService doesn't have disconnect method
        pass

if __name__ == "__main__":
    asyncio.run(main())
