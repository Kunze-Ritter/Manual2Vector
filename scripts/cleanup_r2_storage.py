#!/usr/bin/env python3
"""
Cloudflare R2 Storage Cleanup Script
Deletes ALL objects from R2 buckets (individually, as R2 doesn't support bulk delete)

Usage:
    python cleanup_r2_storage.py --all           # Delete from all buckets
    python cleanup_r2_storage.py --bucket NAME   # Delete from specific bucket
    python cleanup_r2_storage.py --dry-run       # Show what would be deleted
"""

import boto3
import os
import sys
from typing import List, Optional
import argparse
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================

# Load .env file from parent directory
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Get from environment variables or .env file
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_ENDPOINT = os.getenv('R2_ENDPOINT_URL')  # Use endpoint from .env

if not R2_ENDPOINT:
    # Fallback: extract from access key or use default
    print("⚠️  R2_ENDPOINT_URL not found in .env, using hardcoded endpoint")
    R2_ENDPOINT = 'https://a88f92c913c232559845adb9001a5d14.eu.r2.cloudflarestorage.com'

# Bucket names (from your .env)
BUCKETS = [
    'krai-documents-images',  # Your actual bucket
]

# ============================================
# FUNCTIONS
# ============================================

def get_r2_client():
    """Initialize R2 client (S3-compatible)"""
    if not all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        print("❌ ERROR: Missing R2 credentials!")
        print("\nMissing values:")
        if not R2_ENDPOINT:
            print("  - R2_ENDPOINT_URL")
        if not R2_ACCESS_KEY_ID:
            print("  - R2_ACCESS_KEY_ID")
        if not R2_SECRET_ACCESS_KEY:
            print("  - R2_SECRET_ACCESS_KEY")
        print("\nMake sure .env file exists in project root with these values")
        sys.exit(1)
    
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto'  # R2 uses 'auto' region
    )

def list_all_buckets(client) -> List[str]:
    """List all R2 buckets"""
    try:
        response = client.list_buckets()
        return [bucket['Name'] for bucket in response.get('Buckets', [])]
    except Exception as e:
        print(f"❌ Error listing buckets: {e}")
        return []

def count_objects_in_bucket(client, bucket_name: str) -> int:
    """Count total objects in bucket"""
    try:
        paginator = client.get_paginator('list_objects_v2')
        count = 0
        for page in paginator.paginate(Bucket=bucket_name):
            count += len(page.get('Contents', []))
        return count
    except client.exceptions.NoSuchBucket:
        print(f"⚠️  Bucket '{bucket_name}' does not exist")
        return 0
    except Exception as e:
        print(f"❌ Error counting objects in '{bucket_name}': {e}")
        return 0

def delete_all_objects_in_bucket(client, bucket_name: str, dry_run: bool = False) -> tuple:
    """
    Delete all objects from a bucket
    Returns: (deleted_count, failed_count)
    """
    deleted = 0
    failed = 0
    
    try:
        # List all objects (paginated)
        paginator = client.get_paginator('list_objects_v2')
        
        print(f"\n🗑️  Processing bucket: {bucket_name}")
        
        for page in paginator.paginate(Bucket=bucket_name):
            objects = page.get('Contents', [])
            
            if not objects:
                print(f"   ✅ Bucket is empty")
                break
            
            print(f"   Found {len(objects)} objects in this page...")
            
            # Delete objects in batches (R2 supports delete_objects API)
            delete_keys = [{'Key': obj['Key']} for obj in objects]
            
            if dry_run:
                print(f"   [DRY RUN] Would delete {len(delete_keys)} objects")
                for obj in objects[:5]:  # Show first 5
                    print(f"      - {obj['Key']} ({obj['Size']} bytes)")
                if len(objects) > 5:
                    print(f"      ... and {len(objects) - 5} more")
                deleted += len(delete_keys)
            else:
                try:
                    response = client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': delete_keys}
                    )
                    
                    deleted_objs = response.get('Deleted', [])
                    error_objs = response.get('Errors', [])
                    
                    deleted += len(deleted_objs)
                    failed += len(error_objs)
                    
                    print(f"   ✅ Deleted {len(deleted_objs)} objects")
                    
                    if error_objs:
                        print(f"   ❌ Failed to delete {len(error_objs)} objects:")
                        for err in error_objs[:3]:
                            print(f"      - {err['Key']}: {err['Message']}")
                
                except Exception as e:
                    print(f"   ❌ Error deleting batch: {e}")
                    failed += len(delete_keys)
        
        return deleted, failed
    
    except client.exceptions.NoSuchBucket:
        print(f"   ⚠️  Bucket does not exist")
        return 0, 0
    except Exception as e:
        print(f"   ❌ Error processing bucket: {e}")
        return deleted, failed

def delete_bucket(client, bucket_name: str, dry_run: bool = False) -> bool:
    """Delete the bucket itself (must be empty first!)"""
    try:
        if dry_run:
            print(f"   [DRY RUN] Would delete bucket: {bucket_name}")
            return True
        
        client.delete_bucket(Bucket=bucket_name)
        print(f"   ✅ Deleted bucket: {bucket_name}")
        return True
    except client.exceptions.NoSuchBucket:
        print(f"   ⚠️  Bucket '{bucket_name}' does not exist")
        return False
    except Exception as e:
        print(f"   ❌ Error deleting bucket: {e}")
        return False

# ============================================
# MAIN
# ============================================

def main():
    parser = argparse.ArgumentParser(
        description='Cleanup Cloudflare R2 Storage',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--all', action='store_true',
                       help='Delete from all configured buckets')
    parser.add_argument('--bucket', type=str,
                       help='Delete from specific bucket only')
    parser.add_argument('--delete-buckets', action='store_true',
                       help='Delete the buckets themselves (after emptying)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--list', action='store_true',
                       help='List all buckets and their object counts')
    
    args = parser.parse_args()
    
    # Initialize client
    print("🔌 Connecting to Cloudflare R2...")
    client = get_r2_client()
    print("✅ Connected!")
    
    # List mode
    if args.list:
        print("\n📋 Listing all buckets:")
        all_buckets = list_all_buckets(client)
        
        if not all_buckets:
            print("   No buckets found")
        else:
            total_objects = 0
            for bucket in all_buckets:
                count = count_objects_in_bucket(client, bucket)
                total_objects += count
                print(f"   - {bucket}: {count:,} objects")
            print(f"\n   Total: {total_objects:,} objects across {len(all_buckets)} buckets")
        return
    
    # Determine which buckets to process
    if args.bucket:
        buckets_to_process = [args.bucket]
    elif args.all:
        buckets_to_process = BUCKETS
    else:
        print("❌ Error: Must specify --all or --bucket NAME")
        print("   Or use --list to see available buckets")
        sys.exit(1)
    
    # Confirmation
    if not args.dry_run:
        print(f"\n⚠️  WARNING: This will DELETE ALL objects from:")
        for bucket in buckets_to_process:
            count = count_objects_in_bucket(client, bucket)
            print(f"   - {bucket} ({count:,} objects)")
        
        if args.delete_buckets:
            print(f"\n   AND delete the buckets themselves!")
        
        response = input("\n❓ Are you sure? Type 'yes' to continue: ")
        if response.lower() != 'yes':
            print("❌ Cancelled")
            sys.exit(0)
    else:
        print("\n🧪 DRY RUN MODE - Nothing will be deleted")
    
    # Process buckets
    print(f"\n{'='*60}")
    print(f"Starting cleanup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    total_deleted = 0
    total_failed = 0
    
    for bucket in buckets_to_process:
        deleted, failed = delete_all_objects_in_bucket(client, bucket, args.dry_run)
        total_deleted += deleted
        total_failed += failed
        
        # Delete bucket itself if requested
        if args.delete_buckets and deleted > 0 and failed == 0:
            delete_bucket(client, bucket, args.dry_run)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Cleanup completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"✅ Deleted: {total_deleted:,} objects")
    if total_failed > 0:
        print(f"❌ Failed:  {total_failed:,} objects")
    print()

if __name__ == '__main__':
    main()
