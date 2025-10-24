"""
Cleanup internal sprite codes from database
Removes APCM_*, IM_*, Controller_* etc.
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("=" * 80)
print("CLEANUP: Internal Sprite Codes")
print("=" * 80)

# Patterns to delete
patterns = ['APCM_%', 'IM_%', 'Controller_%', 'VI-515_%', 'IC-320S%']

for pattern in patterns:
    print(f"\nDeleting products matching: {pattern}")
    
    # Get products to delete
    products = supabase.table('vw_products').select('id, model_number').like('model_number', pattern).execute()
    
    if products.data:
        print(f"  Found {len(products.data)} products to delete:")
        for p in products.data[:10]:
            print(f"    - {p['model_number']}")
        if len(products.data) > 10:
            print(f"    ... and {len(products.data) - 10} more")
        
        # Delete product_accessories links first
        for p in products.data:
            try:
                supabase.schema('krai_core').table('product_accessories').delete().eq('product_id', p['id']).execute()
                supabase.schema('krai_core').table('product_accessories').delete().eq('accessory_id', p['id']).execute()
            except:
                pass
        
        # Delete products
        for p in products.data:
            try:
                supabase.table('vw_products').delete().eq('id', p['id']).execute()
            except Exception as e:
                print(f"    ⚠️ Could not delete {p['model_number']}: {e}")
        
        print(f"  ✅ Deleted {len(products.data)} products")
    else:
        print(f"  No products found")

print(f"\n{'=' * 80}")
print("CLEANUP COMPLETE")
print("=" * 80)
