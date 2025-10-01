#!/usr/bin/env python3
"""
Test Script for R2 Bucket Listing
Testet nur die Bucket-Auflistung ohne Menü
"""

import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

def main():
    print("Testing R2 Bucket Listing...")
    
    # Get environment variables
    r2_access_key = os.getenv('R2_ACCESS_KEY_ID')
    r2_secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
    r2_endpoint_url = os.getenv('R2_ENDPOINT_URL')
    
    if not all([r2_access_key, r2_secret_key, r2_endpoint_url]):
        print("ERROR: R2 credentials must be set in environment variables")
        return
    
    try:
        # Initialize boto3 client for R2
        s3_client = boto3.client(
            's3',
            endpoint_url=r2_endpoint_url,
            aws_access_key_id=r2_access_key,
            aws_secret_access_key=r2_secret_key,
            region_name='auto'
        )
        
        # List all buckets
        response = s3_client.list_buckets()
        buckets = response['Buckets']
        
        print(f"\nFound {len(buckets)} buckets:")
        print("=" * 60)
        
        # Debug: Print all bucket names first
        bucket_names = [bucket['Name'] for bucket in buckets]
        print(f"DEBUG: All bucket names: {bucket_names}")
        
        for bucket in buckets:
            bucket_name = bucket['Name']
            creation_date = bucket['CreationDate']
            
            print(f"\nProcessing bucket: {bucket_name}")
            
            try:
                # Get bucket size and object count using pagination
                object_count = 0
                total_size = 0
                continuation_token = None
                
                print(f"   Counting objects with pagination...")
                
                while True:
                    if continuation_token:
                        objects = s3_client.list_objects_v2(
                            Bucket=bucket_name,
                            ContinuationToken=continuation_token
                        )
                    else:
                        objects = s3_client.list_objects_v2(Bucket=bucket_name)
                    
                    if 'Contents' in objects:
                        object_count += len(objects['Contents'])
                        for obj in objects['Contents']:
                            total_size += obj['Size']
                    
                    # Check if there are more objects
                    if objects.get('IsTruncated', False):
                        continuation_token = objects.get('NextContinuationToken')
                        print(f"   Found {object_count} objects so far, continuing...")
                    else:
                        break
                
                size_mb = total_size / (1024 * 1024)
                
                print(f"Bucket: {bucket_name}")
                print(f"   Created: {creation_date}")
                print(f"   Objects: {object_count:,}")
                print(f"   Size: {size_mb:.2f} MB")
                
            except ClientError as e:
                print(f"Bucket: {bucket_name}")
                print(f"   Created: {creation_date}")
                print(f"   Error accessing: {e}")
            except Exception as e:
                print(f"Unexpected error processing bucket {bucket_name}: {e}")
        
        print(f"\nSuccessfully processed {len(buckets)} buckets")
        
    except Exception as e:
        print(f"ERROR: Failed to list buckets: {e}")

if __name__ == "__main__":
    main()
