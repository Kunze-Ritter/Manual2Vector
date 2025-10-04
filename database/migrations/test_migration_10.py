"""
Test Migration 10: Check if stage_status tracking is working

Verifies:
1. stage_status column exists
2. Helper functions exist
3. Views exist
4. Can track stages
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv()


def test_migration():
    """Test if migration 10 was applied successfully"""
    
    print("="*80)
    print("  Testing Migration 10: Per-Stage Status Tracking")
    print("="*80)
    
    # Connect
    print("\n🔌 Connecting to Supabase...")
    try:
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    all_tests_passed = True
    
    # Test 1: Check if stage_status column exists
    print("\n" + "-"*80)
    print("TEST 1: Check stage_status column")
    print("-"*80)
    
    try:
        result = supabase.table("documents").select("stage_status").limit(1).execute()
        print("   ✅ PASS: stage_status column exists")
    except Exception as e:
        print(f"   ❌ FAIL: stage_status column not found")
        print(f"      Error: {e}")
        all_tests_passed = False
    
    # Test 2: Check if helper functions exist
    print("\n" + "-"*80)
    print("TEST 2: Check helper functions")
    print("-"*80)
    
    functions_to_test = [
        'start_stage',
        'update_stage_progress',
        'complete_stage',
        'fail_stage',
        'skip_stage',
        'get_document_progress',
        'get_current_stage',
        'can_start_stage'
    ]
    
    for func_name in functions_to_test:
        try:
            # Try to call function with dummy values
            # This will fail but proves function exists
            supabase.rpc(func_name, {}).execute()
            print(f"   ✅ {func_name}() exists")
        except Exception as e:
            error_msg = str(e)
            if "function" in error_msg.lower() and "does not exist" in error_msg.lower():
                print(f"   ❌ {func_name}() NOT FOUND")
                all_tests_passed = False
            else:
                # Function exists but failed for other reason (expected)
                print(f"   ✅ {func_name}() exists")
    
    # Test 3: Check if views exist
    print("\n" + "-"*80)
    print("TEST 3: Check views")
    print("-"*80)
    
    views_to_test = [
        'vw_documents_by_stage',
        'vw_stage_statistics'
    ]
    
    for view_name in views_to_test:
        try:
            result = supabase.table(view_name).select("*").limit(1).execute()
            print(f"   ✅ {view_name} exists")
        except Exception as e:
            print(f"   ❌ {view_name} NOT FOUND")
            print(f"      Error: {e}")
            all_tests_passed = False
    
    # Test 4: Try to use stage tracking (if documents exist)
    print("\n" + "-"*80)
    print("TEST 4: Functional test")
    print("-"*80)
    
    try:
        # Get first document
        docs = supabase.table("documents").select("id, stage_status").limit(1).execute()
        
        if docs.data and len(docs.data) > 0:
            doc_id = docs.data[0]['id']
            stage_status = docs.data[0].get('stage_status')
            
            print(f"\n   Found document: {doc_id}")
            
            if stage_status:
                print(f"   ✅ Has stage_status data")
                print(f"\n   Stage Status Sample:")
                for stage, status in list(stage_status.items())[:2]:
                    print(f"      {stage}: {status.get('status', 'unknown')}")
            else:
                print(f"   ⚠️  No stage_status data yet (will be added on next upload)")
            
            # Try to get progress
            try:
                progress_result = supabase.rpc('get_document_progress', {
                    'p_document_id': doc_id
                }).execute()
                
                if progress_result.data is not None:
                    print(f"\n   ✅ get_document_progress() works: {progress_result.data}%")
                else:
                    print(f"\n   ⚠️  get_document_progress() returned None")
            except Exception as e:
                print(f"\n   ❌ get_document_progress() failed: {e}")
                all_tests_passed = False
            
            # Try to get current stage
            try:
                stage_result = supabase.rpc('get_current_stage', {
                    'p_document_id': doc_id
                }).execute()
                
                if stage_result.data:
                    print(f"   ✅ get_current_stage() works: {stage_result.data}")
                else:
                    print(f"   ⚠️  get_current_stage() returned None")
            except Exception as e:
                print(f"   ❌ get_current_stage() failed: {e}")
                all_tests_passed = False
            
        else:
            print("   ⚠️  No documents found (upload one to test fully)")
    
    except Exception as e:
        print(f"   ❌ Functional test failed: {e}")
        all_tests_passed = False
    
    # Summary
    print("\n" + "="*80)
    if all_tests_passed:
        print("  ✅ ALL TESTS PASSED!")
        print("="*80)
        print("\n  Migration 10 is successfully applied!")
        print("\n  Next steps:")
        print("  1. Upload a document to test stage tracking")
        print("  2. Check stage_status in API: GET /status/{document_id}")
        print("  3. View statistics: GET /stages/statistics")
    else:
        print("  ❌ SOME TESTS FAILED!")
        print("="*80)
        print("\n  Migration 10 may not be fully applied.")
        print("\n  Please apply the migration manually:")
        print("  1. Open Supabase Dashboard → SQL Editor")
        print("  2. Copy content from: 10_stage_status_tracking.sql")
        print("  3. Paste and Run")
    
    print("\n")
    
    return all_tests_passed


if __name__ == "__main__":
    test_migration()
