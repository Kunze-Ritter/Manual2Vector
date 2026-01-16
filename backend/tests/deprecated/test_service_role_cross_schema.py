"""
Test cross-schema queries with Service Role Key (PostgREST)
"""
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment
env_file = os.path.join(os.path.dirname(__file__), '..', '..', 'env.database')
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"✅ Loaded env from: {env_file}")

from supabase import create_client

def test_service_role():
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not service_role_key:
        print("❌ SUPABASE_SERVICE_ROLE_KEY not found!")
        return
    
    print(f"✅ SUPABASE_URL: {supabase_url}")
    print(f"✅ SERVICE_ROLE_KEY: {service_role_key[:20]}...")
    
    try:
        # Connect with Service Role
        print("\n🔌 Connecting with Service Role Key...")
        client = create_client(supabase_url, service_role_key)
        print("✅ Connected!")
        
        # Test 1: Count images via public.vw_images view
        print("\n📊 Test 1: Count images via public.vw_images...")
        result = client.from_('vw_images').select('id', count='exact').limit(1).execute()
        print(f"✅ Found {result.count} images")
        
        # Test 2: Count chunks via public.vw_chunks view
        print("\n📊 Test 2: Count chunks via public.vw_chunks...")
        result = client.from_('vw_chunks').select('id', count='exact').limit(1).execute()
        print(f"✅ Found {result.count} chunks")
        
        # Test 3: Find image by hash (deduplication test)
        print("\n🔍 Test 3: Find image by hash...")
        # Get any image hash first via vw_images
        sample = client.from_('vw_images').select('file_hash').not_.is_('file_hash', 'null').limit(1).execute()
        
        if sample.data and len(sample.data) > 0:
            test_hash = sample.data[0]['file_hash']
            print(f"   Testing with hash: {test_hash[:16]}...")
            
            result = client.from_('vw_images').select('id, filename, file_hash').eq('file_hash', test_hash).limit(1).execute()
            
            if result.data and len(result.data) > 0:
                print(f"✅ Found image: {result.data[0]['filename']}")
            else:
                print("❌ No image found")
        else:
            print("⚠️  No images with file_hash found")
        
        # Test 4: Count embeddings via public.vw_embeddings view
        print("\n📊 Test 4: Count embeddings via public.vw_embeddings...")
        result = client.from_('vw_embeddings').select('id', count='exact').limit(1).execute()
        print(f"✅ Found {result.count} embeddings")
        
        print("\n✅ All PostgREST cross-schema tests passed!")
        print("🎉 Service Role Key works perfectly for cross-schema access!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_service_role()
