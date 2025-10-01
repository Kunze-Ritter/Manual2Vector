#!/usr/bin/env python3
"""
Debug R2 Connection Script
Analysiert die R2-Verbindung und zeigt alle verfügbaren Informationen
"""

import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

def main():
    print("=== R2 CONNECTION DEBUG ===")
    
    # Get environment variables
    r2_access_key = os.getenv('R2_ACCESS_KEY_ID')
    r2_secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
    r2_endpoint_url = os.getenv('R2_ENDPOINT_URL')
    
    print(f"R2 Access Key: {r2_access_key[:10]}..." if r2_access_key else "NOT SET")
    print(f"R2 Secret Key: {r2_secret_key[:10]}..." if r2_secret_key else "NOT SET")
    print(f"R2 Endpoint: {r2_endpoint_url}")
    
    if not all([r2_access_key, r2_secret_key, r2_endpoint_url]):
        print("ERROR: R2 credentials missing!")
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
        
        print("\n=== TESTING CONNECTION ===")
        
        # Test connection with list_buckets
        try:
            response = s3_client.list_buckets()
            print("[OK] Connection successful!")
            
            buckets = response['Buckets']
            print(f"\n=== FOUND {len(buckets)} BUCKETS ===")
            
            for bucket in buckets:
                bucket_name = bucket['Name']
                creation_date = bucket['CreationDate']
                print(f"Bucket: {bucket_name}")
                print(f"   Created: {creation_date}")
                
                # Try to get bucket location
                try:
                    location = s3_client.get_bucket_location(Bucket=bucket_name)
                    print(f"   Location: {location.get('LocationConstraint', 'us-east-1')}")
                except Exception as e:
                    print(f"   Location: Error - {e}")
                
                # Try to get bucket info
                try:
                    bucket_info = s3_client.head_bucket(Bucket=bucket_name)
                    print(f"   Status: Available")
                except Exception as e:
                    print(f"   Status: Error - {e}")
                
                print()
            
            # Test if we can access the specific bucket
            test_bucket = 'ai-technik-agent'
            print(f"\n=== TESTING SPECIFIC BUCKET: {test_bucket} ===")
            
            try:
                # Try to list objects in ai-technik-agent
                objects = s3_client.list_objects_v2(Bucket=test_bucket, MaxKeys=1)
                if 'Contents' in objects:
                    print(f"[OK] Bucket '{test_bucket}' exists and has objects!")
                    print(f"   First object: {objects['Contents'][0]['Key']}")
                else:
                    print(f"[WARN] Bucket '{test_bucket}' exists but is empty")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'NoSuchBucket':
                    print(f"[ERROR] Bucket '{test_bucket}' does not exist")
                elif error_code == 'AccessDenied':
                    print(f"[WARN] Bucket '{test_bucket}' exists but access denied")
                else:
                    print(f"[ERROR] Error accessing bucket '{test_bucket}': {e}")
            
            # Try different bucket name variations
            print(f"\n=== TESTING BUCKET VARIATIONS ===")
            variations = ['ai-technik-agent', 'ai-agent', 'technik-agent', 'ai-technik', 'agent']
            
            for variation in variations:
                try:
                    objects = s3_client.list_objects_v2(Bucket=variation, MaxKeys=1)
                    if 'Contents' in objects:
                        print(f"[OK] Found bucket: {variation}")
                        print(f"   First object: {objects['Contents'][0]['Key']}")
                    else:
                        print(f"[WARN] Empty bucket: {variation}")
                except ClientError as e:
                    if e.response['Error']['Code'] != 'NoSuchBucket':
                        print(f"[WARN] Bucket {variation}: {e.response['Error']['Code']}")
                    # Don't print for NoSuchBucket (bucket doesn't exist)
                except Exception as e:
                    print(f"[ERROR] Error testing {variation}: {e}")
            
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            
            # Try to get more detailed error info
            if hasattr(e, 'response'):
                print(f"Error Response: {e.response}")
            
    except Exception as e:
        print(f"[ERROR] Failed to initialize client: {e}")

if __name__ == "__main__":
    main()
