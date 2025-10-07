"""
R2 Image Cleanup Script - DELETE OLD IMAGES

This script simply deletes ALL images from R2 bucket.
New images with hash-based naming will be uploaded on next processing run.

What it does:
1. Lists all images in R2 bucket
2. Deletes them
3. That's it!

Usage:
    python cleanup_r2_images_with_hashes.py --dry-run  # Preview only
    python cleanup_r2_images_with_hashes.py --delete   # Delete all images

Safety:
    - Dry-run mode by default
    - Requires explicit --delete flag
    - Shows preview before deletion
"""

import os
import sys
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda: None  # Fallback
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

import boto3
from botocore.client import Config


class R2ImageCleanup:
    """Delete all old images from R2 bucket"""
    
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        
        # R2 Configuration
        self.access_key = os.getenv('R2_ACCESS_KEY_ID')
        self.secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
        self.endpoint_url = os.getenv('R2_ENDPOINT_URL')
        self.bucket_name = os.getenv('R2_BUCKET_NAME_DOCUMENTS')
        
        # Initialize R2 client
        self.r2_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )
        
        # Stats
        self.stats = {
            'total_images': 0,
            'deleted': 0,
            'failed': 0,
            'errors': []
        }
        
        print(f"\n{'='*80}")
        print(f"  R2 IMAGE CLEANUP - DELETE ALL IMAGES")
        print(f"{'='*80}")
        print(f"\nMode: {'DRY RUN (preview only)' if dry_run else 'DELETE MODE (will delete all images!)'}")
        print(f"Bucket: {self.bucket_name}")
        print(f"Endpoint: {self.endpoint_url}")
    
    def list_all_images(self):
        """List all images in R2 bucket"""
        print(f"\n📋 Listing all images in R2...")
        
        images = []
        paginator = self.r2_client.get_paginator('list_objects_v2')
        
        for page in paginator.paginate(Bucket=self.bucket_name):
            if 'Contents' in page:
                for obj in page['Contents']:
                    # Only process image files
                    key = obj['Key']
                    if any(key.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                        images.append({
                            'key': key,
                            'size': obj['Size'],
                            'last_modified': obj['LastModified']
                        })
        
        self.stats['total_images'] = len(images)
        print(f"✅ Found {len(images)} images")
        return images
    
    def delete_image(self, image_info):
        """Delete single image from R2"""
        key = image_info['key']
        
        try:
            if not self.dry_run:
                # Delete from R2
                self.r2_client.delete_object(Bucket=self.bucket_name, Key=key)
                self.stats['deleted'] += 1
                print(f"🗑️  Deleted: {key}")
            else:
                print(f"[DRY RUN] Would delete: {key}")
            
            return True
                
        except Exception as e:
            print(f"❌ Failed to delete {key}: {e}")
            self.stats['failed'] += 1
            self.stats['errors'].append({
                'image': key,
                'error': str(e)
            })
            return False
    
    def run(self):
        """Execute cleanup"""
        
        # List all images
        images = self.list_all_images()
        
        if not images:
            print("\n✅ No images found in bucket!")
            return
        
        # Confirm if not dry run
        if not self.dry_run:
            print(f"\n⚠️  WARNING: This will DELETE {len(images)} images!")
            print(f"   They will be re-uploaded with hashes on next processing run.")
            response = input("\n   Type 'DELETE ALL' to proceed: ")
            if response != 'DELETE ALL':
                print("\n❌ Aborted by user")
                return
        
        # Delete each image
        print(f"\n🗑️  Deleting {len(images)} images...\n")
        
        for idx, image in enumerate(images, 1):
            if idx % 50 == 0 or idx == 1:
                print(f"\n[{idx}/{len(images)}] ({idx/len(images)*100:.1f}%)")
            
            self.delete_image(image)
            
            # Progress update
            if idx % 100 == 0:
                print(f"\n📊 Progress: {idx}/{len(images)}")
                print(f"   Deleted: {self.stats['deleted']}")
                print(f"   Failed: {self.stats['failed']}")
        
        # Final stats
        self.print_summary()
    
    def print_summary(self):
        """Print final summary"""
        print(f"\n{'='*80}")
        print(f"  CLEANUP SUMMARY")
        print(f"{'='*80}")
        print(f"\n📊 Statistics:")
        print(f"   Total Images: {self.stats['total_images']}")
        print(f"   Deleted: {self.stats['deleted']}")
        print(f"   Failed: {self.stats['failed']}")
        
        if self.stats['errors']:
            print(f"\n❌ Errors: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:10]:  # Show first 10
                print(f"   - {error['image']}: {error['error']}")
        
        if self.dry_run:
            print(f"\n💡 This was a DRY RUN - no changes were made!")
            print(f"   Run with --delete to execute cleanup")
        else:
            print(f"\n✅ CLEANUP COMPLETE!")
            print(f"   All old images deleted from R2")
            print(f"   New images with hashes will be uploaded on next processing run")
        
        print(f"\n{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description='R2 Image Cleanup - Delete All Images')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Preview only, no changes (default)')
    parser.add_argument('--delete', action='store_true',
                       help='Execute deletion (removes --dry-run)')
    
    args = parser.parse_args()
    
    # If --delete is set, disable dry-run
    dry_run = not args.delete
    
    cleanup = R2ImageCleanup(dry_run=dry_run)
    cleanup.run()


if __name__ == "__main__":
    main()
