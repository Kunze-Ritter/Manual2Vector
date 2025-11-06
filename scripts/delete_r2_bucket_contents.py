"""
Object Storage Bucket Bulk Delete Script

Delete ALL objects from a specific storage bucket.
Useful when you want to delete a bucket but it contains too many files.

Cloudflare UI limits: 25 objects per delete
This script: Unlimited (uses batch delete API - 1000 per batch)

Usage:
    # With .env credentials (EU/default account)
    python delete_r2_bucket_contents.py --bucket ai-technik-agent --dry-run
    python delete_r2_bucket_contents.py --bucket ai-technik-agent --delete
    
    # With custom credentials (USA account / different account)
    python delete_r2_bucket_contents.py --bucket ai-technik-agent --delete \
        --access-key YOUR_KEY \
        --secret-key YOUR_SECRET \
        --endpoint https://YOUR_ACCOUNT.storage.example.com

Getting Credentials:
    1. Go to your storage provider dashboard
    2. Select the account where bucket is located
    3. Find API tokens/credentials section
    4. Create new token with Read & Write permissions
    5. Copy Access Key ID, Secret Access Key, and endpoint URL

Safety:
    - Dry-run by default
    - Requires explicit --delete flag
    - Shows preview before deletion
    - Requires typing bucket name + "DELETE ALL" to confirm
"""

import os
import sys
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda: None  # Fallback
import argparse

# Load environment
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

import boto3
from botocore.client import Config


class ObjectStorageBucketCleaner:
    """Delete all objects from storage bucket"""
    
    def __init__(self, bucket_name: str, dry_run=True, access_key=None, secret_key=None, endpoint_url=None):
        self.bucket_name = bucket_name
        self.dry_run = dry_run
        
        # Helper function to get env var with fallback and deprecation warning
        def get_env_var(new_var: str, old_var: str, default: str = None) -> str:
            value = os.getenv(new_var) or os.getenv(old_var) or default
            if not os.getenv(new_var) and os.getenv(old_var):
                print(f"⚠️  Environment variable {old_var} is deprecated. Use {new_var} instead.")
            return value
        
        # Storage Configuration - use provided or fall back to .env
        self.access_key = access_key or get_env_var('OBJECT_STORAGE_ACCESS_KEY', 'R2_ACCESS_KEY_ID')
        self.secret_key = secret_key or get_env_var('OBJECT_STORAGE_SECRET_KEY', 'R2_SECRET_ACCESS_KEY')
        self.endpoint_url = endpoint_url or get_env_var('OBJECT_STORAGE_ENDPOINT', 'R2_ENDPOINT_URL')
        
        if not all([self.access_key, self.secret_key, self.endpoint_url]):
            raise ValueError("Missing storage credentials. Provide via arguments or .env file")
        
        # Initialize storage client
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
            'total_objects': 0,
            'deleted': 0,
            'failed': 0,
            'batches': 0
        }
        
        print(f"\n{'='*80}")
        print(f"  OBJECT STORAGE BUCKET BULK DELETE")
        print(f"{'='*80}")
        print(f"\nBucket: {self.bucket_name}")
        print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'DELETE MODE'}")
        print(f"Endpoint: {self.endpoint_url}")
    
    def list_all_objects(self):
        """List all objects in bucket"""
        print(f"\n📋 Listing all objects...")
        
        objects = []
        paginator = self.r2_client.get_paginator('list_objects_v2')
        
        try:
            for page in paginator.paginate(Bucket=self.bucket_name):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        objects.append({
                            'Key': obj['Key'],
                            'Size': obj['Size']
                        })
                        
                        # Progress indicator
                        if len(objects) % 500 == 0:
                            print(f"   Found {len(objects)} objects so far...")
        except Exception as e:
            print(f"❌ Error listing objects: {e}")
            return []
        
        self.stats['total_objects'] = len(objects)
        print(f"✅ Found {len(objects)} objects")
        
        # Calculate total size
        total_size_mb = sum(obj['Size'] for obj in objects) / 1024 / 1024
        print(f"   Total Size: {total_size_mb:.2f} MB")
        
        return objects
    
    def delete_batch(self, objects_batch):
        """Delete a batch of objects (max 1000 per AWS S3 API limit)"""
        if not objects_batch:
            return 0
        
        try:
            # Prepare delete request
            delete_request = {
                'Objects': [{'Key': obj['Key']} for obj in objects_batch],
                'Quiet': True  # Only return errors
            }
            
            if not self.dry_run:
                # Execute delete
                response = self.r2_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete=delete_request
                )
                
                # Check for errors
                if 'Errors' in response and response['Errors']:
                    self.stats['failed'] += len(response['Errors'])
                    for error in response['Errors'][:5]:  # Show first 5 errors
                        print(f"   ❌ Failed: {error['Key']} - {error['Message']}")
                    return len(objects_batch) - len(response['Errors'])
                
                return len(objects_batch)
            else:
                # Dry run - just count
                return len(objects_batch)
                
        except Exception as e:
            print(f"❌ Batch delete error: {e}")
            self.stats['failed'] += len(objects_batch)
            return 0
    
    def delete_all_objects(self, objects):
        """Delete all objects in batches"""
        if not objects:
            print("\n✅ No objects to delete!")
            return
        
        print(f"\n🗑️  Deleting {len(objects)} objects in batches of 1000...")
        
        batch_size = 1000  # AWS S3 API limit
        total_batches = (len(objects) + batch_size - 1) // batch_size
        
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"\n[Batch {batch_num}/{total_batches}] Deleting {len(batch)} objects...")
            
            deleted = self.delete_batch(batch)
            self.stats['deleted'] += deleted
            self.stats['batches'] += 1
            
            if not self.dry_run:
                print(f"   ✅ Deleted {deleted}/{len(batch)} objects")
            else:
                print(f"   [DRY RUN] Would delete {len(batch)} objects")
    
    def run(self):
        """Execute cleanup"""
        
        # List all objects
        objects = self.list_all_objects()
        
        if not objects:
            print("\n✅ Bucket is already empty!")
            return
        
        # Confirm if not dry run
        if not self.dry_run:
            print(f"\n{'='*80}")
            print(f"  ⚠️  WARNING: DESTRUCTIVE OPERATION")
            print(f"{'='*80}")
            print(f"\nThis will DELETE ALL {len(objects)} objects from:")
            print(f"   Bucket: {self.bucket_name}")
            print(f"\n⚠️  THIS CANNOT BE UNDONE!")
            
            print(f"\nTo confirm, type the bucket name: {self.bucket_name}")
            response = input("   Bucket name: ")
            
            if response != self.bucket_name:
                print("\n❌ Bucket name doesn't match - Aborted")
                return
            
            print(f"\nType 'DELETE ALL' to proceed:")
            confirm = input("   Confirmation: ")
            
            if confirm != 'DELETE ALL':
                print("\n❌ Confirmation failed - Aborted")
                return
        
        # Delete all objects
        self.delete_all_objects(objects)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print final summary"""
        print(f"\n{'='*80}")
        print(f"  CLEANUP SUMMARY")
        print(f"{'='*80}")
        print(f"\n📊 Statistics:")
        print(f"   Bucket: {self.bucket_name}")
        print(f"   Total Objects: {self.stats['total_objects']}")
        print(f"   Deleted: {self.stats['deleted']}")
        print(f"   Failed: {self.stats['failed']}")
        print(f"   Batches: {self.stats['batches']}")
        
        if self.dry_run:
            print(f"\n💡 This was a DRY RUN - no changes were made!")
            print(f"   Run with --delete to execute cleanup")
        else:
            print(f"\n✅ CLEANUP COMPLETE!")
            print(f"   Bucket '{self.bucket_name}' is now empty")
            print(f"   You can now delete the bucket via Cloudflare dashboard")
        
        print(f"\n{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Object Storage Bucket Bulk Delete - Delete all objects from bucket',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview (uses credentials from .env)
  python delete_r2_bucket_contents.py --bucket ai-technik-agent --dry-run
  
  # Delete with custom endpoint (USA account)
  python delete_r2_bucket_contents.py --bucket ai-technik-agent --delete \\
    --access-key YOUR_KEY \\
    --secret-key YOUR_SECRET \\
    --endpoint https://YOUR_ACCOUNT.storage.example.com
  
  # Delete with .env credentials
  python delete_r2_bucket_contents.py --bucket ai-technik-agent --delete
        """
    )
    
    parser.add_argument('--bucket', required=True,
                       help='Object Storage bucket name to clean')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Preview only, no changes (default)')
    parser.add_argument('--delete', action='store_true',
                       help='Execute deletion (removes --dry-run)')
    
    # Optional credentials (if different from .env)
    parser.add_argument('--access-key',
                       help='Storage Access Key ID (defaults to OBJECT_STORAGE_ACCESS_KEY from .env)')
    parser.add_argument('--secret-key',
                       help='Storage Secret Access Key (defaults to OBJECT_STORAGE_SECRET_KEY from .env)')
    parser.add_argument('--endpoint',
                       help='Storage Endpoint URL (defaults to OBJECT_STORAGE_ENDPOINT from .env)')
    
    args = parser.parse_args()
    
    # If --delete is set, disable dry-run
    dry_run = not args.delete
    
    try:
        cleaner = ObjectStorageBucketCleaner(
            bucket_name=args.bucket,
            dry_run=dry_run,
            access_key=args.access_key,
            secret_key=args.secret_key,
            endpoint_url=args.endpoint
        )
        cleaner.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
