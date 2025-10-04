"""
Test only the helper functions (they access krai_core directly)
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

print("="*80)
print("  Testing Migration 10: Helper Functions (krai_core)")
print("="*80)

# Get a document ID from public view (which accesses krai_core)
print("\n📋 Finding a document to test with...")
try:
    docs = supabase.table("documents").select("id").limit(1).execute()
    
    if not docs.data or len(docs.data) == 0:
        print("❌ No documents found. Upload a document first!")
        exit(1)
    
    doc_id = docs.data[0]['id']
    print(f"✅ Found document: {doc_id}")
    
except Exception as e:
    print(f"❌ Could not find document: {e}")
    exit(1)

# Test the helper functions
all_passed = True

print("\n" + "-"*80)
print("TEST: Helper Functions")
print("-"*80)

# Test 1: start_stage
print("\n1. Testing start_stage()...")
try:
    result = supabase.rpc('start_stage', {
        'p_document_id': doc_id,
        'p_stage_name': 'text_extraction'
    }).execute()
    print("   ✅ start_stage() works!")
except Exception as e:
    print(f"   ❌ start_stage() failed: {e}")
    all_passed = False

# Test 2: update_stage_progress
print("\n2. Testing update_stage_progress()...")
try:
    result = supabase.rpc('update_stage_progress', {
        'p_document_id': doc_id,
        'p_stage_name': 'text_extraction',
        'p_progress': 50.0,
        'p_metadata': {'test': 'value'}
    }).execute()
    print("   ✅ update_stage_progress() works!")
except Exception as e:
    print(f"   ❌ update_stage_progress() failed: {e}")
    all_passed = False

# Test 3: get_document_progress
print("\n3. Testing get_document_progress()...")
try:
    result = supabase.rpc('get_document_progress', {
        'p_document_id': doc_id
    }).execute()
    
    if result.data is not None:
        print(f"   ✅ get_document_progress() works: {result.data}%")
    else:
        print("   ⚠️  Returns None (maybe column doesn't exist yet?)")
        all_passed = False
except Exception as e:
    print(f"   ❌ get_document_progress() failed: {e}")
    all_passed = False

# Test 4: get_current_stage
print("\n4. Testing get_current_stage()...")
try:
    result = supabase.rpc('get_current_stage', {
        'p_document_id': doc_id
    }).execute()
    
    if result.data:
        print(f"   ✅ get_current_stage() works: {result.data}")
    else:
        print("   ⚠️  Returns None (maybe column doesn't exist yet?)")
        all_passed = False
except Exception as e:
    print(f"   ❌ get_current_stage() failed: {e}")
    all_passed = False

# Test 5: complete_stage
print("\n5. Testing complete_stage()...")
try:
    result = supabase.rpc('complete_stage', {
        'p_document_id': doc_id,
        'p_stage_name': 'text_extraction',
        'p_metadata': {'completed': True}
    }).execute()
    print("   ✅ complete_stage() works!")
except Exception as e:
    print(f"   ❌ complete_stage() failed: {e}")
    all_passed = False

# Test 6: can_start_stage
print("\n6. Testing can_start_stage()...")
try:
    result = supabase.rpc('can_start_stage', {
        'p_document_id': doc_id,
        'p_stage_name': 'embedding'
    }).execute()
    
    if result.data is not None:
        print(f"   ✅ can_start_stage() works: {result.data}")
    else:
        print("   ⚠️  Returns None")
        all_passed = False
except Exception as e:
    print(f"   ❌ can_start_stage() failed: {e}")
    all_passed = False

# Summary
print("\n" + "="*80)
if all_passed:
    print("  ✅ ALL FUNCTION TESTS PASSED!")
    print("="*80)
    print("\n  The functions work and can access krai_core.documents!")
    print("  Migration 10 is successfully applied!")
else:
    print("  ⚠️  SOME TESTS HAD ISSUES")
    print("="*80)
    print("\n  If functions exist but return errors about missing column,")
    print("  then stage_status column needs to be added to krai_core.documents")
    print("\n  Run this in Supabase SQL Editor:")
    print("  ALTER TABLE krai_core.documents ADD COLUMN stage_status JSONB;")

print("\n")
