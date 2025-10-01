#!/usr/bin/env python3
"""
List R2 Buckets Script
Listet alle verfügbaren R2 Buckets auf
"""

import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

def main():
    print("Starting R2 Buckets Listing")
    
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
        
        print(f"\nFound {len(response['Buckets'])} buckets:")
        print("=" * 50)
        
        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            creation_date = bucket['CreationDate']
            
            # Get bucket size and object count
            try:
                objects = s3_client.list_objects_v2(Bucket=bucket_name)
                object_count = objects.get('KeyCount', 0)
                
                # Calculate total size
                total_size = 0
                if 'Contents' in objects:
                    for obj in objects['Contents']:
                        total_size += obj['Size']
                
                size_mb = total_size / (1024 * 1024)
                
                print(f"Bucket: {bucket_name}")
                print(f"   Created: {creation_date}")
                print(f"   Objects: {object_count}")
                print(f"   Size: {size_mb:.2f} MB")
                print()
                
            except ClientError as e:
                print(f"Bucket: {bucket_name}")
                print(f"   Created: {creation_date}")
                print(f"   Error accessing: {e}")
                print()
        
    except Exception as e:
        print(f"ERROR: Error listing buckets: {e}")

if __name__ == "__main__":
    main()
