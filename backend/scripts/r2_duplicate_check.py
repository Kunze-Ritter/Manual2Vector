#!/usr/bin/env python3
"""
R2 Management Script
R2 Object Storage Management mit Optionen für:
- Duplikat-Check
- Bucket-Auflistung
- Bucket-Löschung
"""

import asyncio
import logging
from typing import Dict, List, Any
import sys
import os
from dotenv import load_dotenv
import hashlib
from collections import defaultdict

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class R2Manager:
    def __init__(self):
        # Get environment variables
        r2_access_key = os.getenv('R2_ACCESS_KEY_ID')
        r2_secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
        r2_endpoint_url = os.getenv('R2_ENDPOINT_URL')
        r2_public_url_documents = os.getenv('R2_PUBLIC_URL_DOCUMENTS')
        r2_public_url_error = os.getenv('R2_PUBLIC_URL_ERROR')
        r2_public_url_parts = os.getenv('R2_PUBLIC_URL_PARTS')
        
        if not all([r2_access_key, r2_secret_key, r2_endpoint_url, r2_public_url_documents, r2_public_url_error, r2_public_url_parts]):
            raise ValueError("R2 credentials must be set in environment variables")
        
        # Initialize boto3 client for R2
        self.s3_client = boto3.client(
            's3',
            endpoint_url=r2_endpoint_url,
            aws_access_key_id=r2_access_key,
            aws_secret_access_key=r2_secret_key,
            region_name='auto'
        )
        
        self.duplicate_groups = defaultdict(list)
        self.total_files = 0
        self.total_duplicates = 0
        self.buckets = {}
        
    def connect(self):
        """Connect to R2 (synchronous for boto3)"""
        logger.info("Connected to R2 storage")
    
    def list_all_objects(self) -> List[Dict[str, Any]]:
        """List all objects in the bucket with pagination"""
        logger.info("Listing all objects in R2 bucket...")
        
        try:
            objects = []
            bucket_name = 'krai-documents-images'  # Direct bucket name
            logger.info(f"Using bucket: {bucket_name}")
            
            # Use paginator to get ALL objects
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_count = 0
            
            for page in paginator.paginate(Bucket=bucket_name):
                page_count += 1
                logger.info(f"Processing page {page_count}...")
                
                if 'Contents' in page:
                    for obj in page['Contents']:
                        objects.append({
                            'name': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat(),
                            'etag': obj['ETag']
                        })
                    
                    logger.info(f"Found {len(objects)} objects so far...")
            
            logger.info(f"Found {len(objects)} objects in bucket (processed {page_count} pages)")
            return objects
        except Exception as e:
            logger.error(f"Failed to list objects: {e}")
            return []
    
    def analyze_duplicates(self, objects: List[Dict[str, Any]]):
        """Analyze objects for duplicates based on hash"""
        logger.info("🔍 Analyzing objects for duplicates...")
        
        self.total_files = len(objects)
        
        # Group objects by hash (from metadata or filename)
        hash_groups = defaultdict(list)
        
        for obj in objects:
            try:
                # Try to get hash from metadata
                metadata = obj.get('metadata', {})
                file_hash = metadata.get('hash') or metadata.get('file_hash')
                
                # If no hash in metadata, try to extract from filename
                if not file_hash:
                    filename = obj.get('name', '')
                    # Extract hash from filename (assuming format: hash_originalname)
                    if '_' in filename:
                        file_hash = filename.split('_')[0]
                
                # If still no hash, use filename as identifier
                if not file_hash:
                    file_hash = filename
                
                hash_groups[file_hash].append(obj)
                
            except Exception as e:
                logger.warning(f"Error processing object {obj.get('name', 'unknown')}: {e}")
        
        # Find duplicates
        for file_hash, objects_list in hash_groups.items():
            if len(objects_list) > 1:
                self.duplicate_groups[file_hash] = objects_list
                self.total_duplicates += len(objects_list) - 1  # -1 because we keep one
        
        logger.info(f"📊 Analysis complete:")
        logger.info(f"  Total files: {self.total_files}")
        logger.info(f"  Duplicate groups: {len(self.duplicate_groups)}")
        logger.info(f"  Total duplicate files: {self.total_duplicates}")
    
    def print_duplicate_summary(self):
        """Print summary of duplicates found"""
        if not self.duplicate_groups:
            logger.info("✅ No duplicates found in R2 - storage is clean!")
            return
        
        logger.info(f"\n📋 DUPLICATE SUMMARY:")
        logger.info(f"{'='*60}")
        
        for file_hash, objects in self.duplicate_groups.items():
            logger.info(f"\n🔗 Hash: {file_hash[:16]}...")
            logger.info(f"   Duplicates: {len(objects)}")
            
            for i, obj in enumerate(objects):
                size_mb = obj.get('size', 0) / (1024 * 1024)
                last_modified = obj.get('last_modified', 'Unknown')
                status = "KEEP" if i == 0 else "DELETE"
                logger.info(f"   [{status}] {obj.get('name', 'unknown')} ({size_mb:.1f}MB, {last_modified})")
    
    def cleanup_duplicates(self):
        """Clean up duplicates - keep newest, delete rest"""
        if not self.duplicate_groups:
            logger.info("No duplicates to clean up")
            return
        
        logger.info(f"🧹 Starting cleanup of {len(self.duplicate_groups)} duplicate groups...")
        
        deleted_count = 0
        
        for file_hash, objects in self.duplicate_groups.items():
            try:
                # Sort by last_modified (newest first)
                objects_sorted = sorted(objects, 
                                      key=lambda x: x.get('last_modified', ''), 
                                      reverse=True)
                
                keep_object = objects_sorted[0]  # Keep the newest
                delete_objects = objects_sorted[1:]  # Delete the rest
                
                logger.info(f"🔗 Hash {file_hash[:16]}...: Keeping newest, deleting {len(delete_objects)} duplicates")
                
                # Delete duplicate objects
                for obj in delete_objects:
                    try:
                        object_name = obj.get('name')
                        if object_name:
                            bucket_name = 'krai-documents-images'  # Direct bucket name
                            self.s3_client.delete_object(Bucket=bucket_name, Key=object_name)
                            deleted_count += 1
                            logger.info(f"  ✅ Deleted: {object_name}")
                        else:
                            logger.warning(f"  ⚠️ Cannot delete object without name")
                            
                    except Exception as e:
                        logger.error(f"  ❌ Error deleting {obj.get('name', 'unknown')}: {e}")
                
            except Exception as e:
                logger.error(f"❌ Error processing duplicate group {file_hash[:16]}...: {e}")
        
        logger.info(f"🎉 Cleanup completed: {deleted_count} duplicate files deleted")
    
    def verify_cleanup(self):
        """Verify that cleanup was successful"""
        logger.info("🔍 Verifying cleanup...")
        
        try:
            # Re-analyze after cleanup
            objects = self.list_all_objects()
            
            # Quick check for remaining duplicates
            hash_counts = defaultdict(int)
            for obj in objects:
                filename = obj.get('name', '')
                if '_' in filename:
                    file_hash = filename.split('_')[0]
                    hash_counts[file_hash] += 1
            
            remaining_duplicates = sum(1 for count in hash_counts.values() if count > 1)
            
            if remaining_duplicates == 0:
                logger.info("✅ No duplicates found after cleanup - verification successful!")
                return True
            else:
                logger.warning(f"⚠️ Found {remaining_duplicates} hash values still duplicated")
                return False
                
        except Exception as e:
            logger.error(f"Failed to verify cleanup: {e}")
            return False
    
    def list_all_buckets(self):
        """List all R2 buckets with details"""
        logger.info("Listing all R2 buckets...")
        
        try:
            response = self.s3_client.list_buckets()
            buckets = response['Buckets']
            
            logger.info(f"Found {len(buckets)} buckets:")
            logger.info("=" * 60)
            
            # Debug: Print all bucket names first
            bucket_names = [bucket['Name'] for bucket in buckets]
            logger.info(f"DEBUG: All bucket names: {bucket_names}")
            
            for bucket in buckets:
                bucket_name = bucket['Name']
                creation_date = bucket['CreationDate']
                
                logger.info(f"Processing bucket: {bucket_name}")
                
                try:
                    # Get bucket size and object count using pagination
                    object_count = 0
                    total_size = 0
                    continuation_token = None
                    
                    logger.info(f"   Counting objects with pagination...")
                    
                    while True:
                        if continuation_token:
                            objects = self.s3_client.list_objects_v2(
                                Bucket=bucket_name,
                                ContinuationToken=continuation_token
                            )
                        else:
                            objects = self.s3_client.list_objects_v2(Bucket=bucket_name)
                        
                        if 'Contents' in objects:
                            object_count += len(objects['Contents'])
                            for obj in objects['Contents']:
                                total_size += obj['Size']
                        
                        # Check if there are more objects
                        if objects.get('IsTruncated', False):
                            continuation_token = objects.get('NextContinuationToken')
                            logger.info(f"   Found {object_count} objects so far, continuing...")
                        else:
                            break
                    
                    size_mb = total_size / (1024 * 1024)
                    
                    logger.info(f"Bucket: {bucket_name}")
                    logger.info(f"   Created: {creation_date}")
                    logger.info(f"   Objects: {object_count:,}")
                    logger.info(f"   Size: {size_mb:.2f} MB")
                    logger.info("")
                    
                    self.buckets[bucket_name] = {
                        'creation_date': creation_date,
                        'object_count': object_count,
                        'size_mb': size_mb
                    }
                    
                except ClientError as e:
                    logger.warning(f"Bucket: {bucket_name}")
                    logger.warning(f"   Created: {creation_date}")
                    logger.warning(f"   Error accessing: {e}")
                    logger.warning("")
                    
                    # Still add to buckets dict even if we can't access contents
                    self.buckets[bucket_name] = {
                        'creation_date': creation_date,
                        'object_count': 'ERROR',
                        'size_mb': 'ERROR'
                    }
                except Exception as e:
                    logger.error(f"Unexpected error processing bucket {bucket_name}: {e}")
                    # Still add to buckets dict
                    self.buckets[bucket_name] = {
                        'creation_date': creation_date,
                        'object_count': 'ERROR',
                        'size_mb': 'ERROR'
                    }
            
            logger.info(f"Successfully processed {len(self.buckets)} buckets")
            return self.buckets
                
        except Exception as e:
            logger.error(f"Failed to list buckets: {e}")
            return {}
    
    def delete_bucket(self, bucket_name: str, force: bool = False):
        """Delete a bucket and all its contents"""
        logger.info(f"Deleting bucket: {bucket_name}")
        
        try:
            # First, list all objects in the bucket
            objects = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        objects.append(obj['Key'])
            
            if objects:
                logger.info(f"Found {len(objects)} objects in bucket")
                
                if not force:
                    response = input(f"Delete bucket '{bucket_name}' with {len(objects)} objects? (y/N): ").strip().lower()
                    if response != 'y':
                        logger.info("Bucket deletion cancelled by user")
                        return False
                
                # Delete all objects first
                logger.info("Deleting all objects...")
                for obj_key in objects:
                    try:
                        self.s3_client.delete_object(Bucket=bucket_name, Key=obj_key)
                    except Exception as e:
                        logger.error(f"Failed to delete object {obj_key}: {e}")
                        return False
                
                logger.info("All objects deleted")
            
            # Delete the bucket
            self.s3_client.delete_bucket(Bucket=bucket_name)
            logger.info(f"Bucket '{bucket_name}' deleted successfully")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                logger.error(f"Bucket '{bucket_name}' does not exist")
            else:
                logger.error(f"Failed to delete bucket '{bucket_name}': {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete bucket '{bucket_name}': {e}")
            return False
    
    def delete_multiple_buckets(self, bucket_names: List[str]):
        """Delete multiple buckets"""
        logger.info(f"Deleting {len(bucket_names)} buckets...")
        
        success_count = 0
        for bucket_name in bucket_names:
            if self.delete_bucket(bucket_name, force=True):
                success_count += 1
        
        logger.info(f"Successfully deleted {success_count}/{len(bucket_names)} buckets")
        return success_count == len(bucket_names)

def show_menu():
    """Show the main menu"""
    print("\n" + "="*60)
    print("R2 MANAGEMENT TOOL")
    print("="*60)
    print("1. Duplikat-Check")
    print("2. Bucket auflisten")
    print("3. Bucket löschen")
    print("4. Alle KRAI Buckets löschen")
    print("5. Beenden")
    print("="*60)

def main():
    """Main R2 management function"""
    logger.info("Starting R2 Management Tool")
    
    manager = R2Manager()
    
    try:
        manager.connect()
        
        while True:
            show_menu()
            choice = input("Wählen Sie eine Option (1-5): ").strip()
            
            if choice == '1':
                # Duplikat-Check
                logger.info("\n=== DUPLIKAT-CHECK ===")
                objects = manager.list_all_objects()
                
                if not objects:
                    logger.info("No objects found in R2 bucket")
                    continue
                
                manager.analyze_duplicates(objects)
                manager.print_duplicate_summary()
                
                if manager.duplicate_groups:
                    response = input(f"\nDelete {manager.total_duplicates} duplicate files? (y/N): ").strip().lower()
                    if response == 'y':
                        manager.cleanup_duplicates()
                        manager.verify_cleanup()
                else:
                    logger.info("No duplicates found - R2 storage is clean!")
            
            elif choice == '2':
                # Bucket auflisten
                logger.info("\n=== BUCKET-AUFLISTUNG ===")
                buckets = manager.list_all_buckets()
                
                if buckets:
                    logger.info(f"Total buckets found: {len(buckets)}")
                else:
                    logger.info("No buckets found")
            
            elif choice == '3':
                # Einzelnen Bucket löschen
                logger.info("\n=== BUCKET LÖSCHEN ===")
                
                # First list buckets
                buckets = manager.list_all_buckets()
                if not buckets:
                    logger.info("No buckets to delete")
                    continue
                
                print("\nAvailable buckets:")
                bucket_names = list(buckets.keys())
                for i, name in enumerate(bucket_names, 1):
                    print(f"{i}. {name}")
                
                try:
                    selection = input(f"\nSelect bucket to delete (1-{len(bucket_names)}) or 'cancel': ").strip()
                    
                    if selection.lower() == 'cancel':
                        continue
                    
                    bucket_index = int(selection) - 1
                    if 0 <= bucket_index < len(bucket_names):
                        bucket_name = bucket_names[bucket_index]
                        manager.delete_bucket(bucket_name)
                    else:
                        logger.error("Invalid selection")
                        
                except ValueError:
                    logger.error("Invalid input")
            
            elif choice == '4':
                # Alle KRAI Buckets löschen
                logger.info("\n=== ALLE KRAI BUCKETS LÖSCHEN ===")
                
                buckets = manager.list_all_buckets()
                krai_buckets = [name for name in buckets.keys() if name.startswith('krai-')]
                
                if not krai_buckets:
                    logger.info("No KRAI buckets found")
                    continue
                
                logger.info(f"Found KRAI buckets: {krai_buckets}")
                
                response = input(f"Delete all {len(krai_buckets)} KRAI buckets? (y/N): ").strip().lower()
                if response == 'y':
                    manager.delete_multiple_buckets(krai_buckets)
                else:
                    logger.info("KRAI bucket deletion cancelled")
            
            elif choice == '5':
                # Beenden
                logger.info("Goodbye!")
                break
            
            else:
                logger.warning("Invalid option. Please choose 1-5.")
            
            # Pause before showing menu again
            input("\nPress Enter to continue...")
            
    except Exception as e:
        logger.error(f"R2 management failed: {e}")

if __name__ == "__main__":
    main()
