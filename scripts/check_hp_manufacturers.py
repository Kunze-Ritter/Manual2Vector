"""
Check HP manufacturer entries in database
"""
import sys
import os
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))
from utils.manufacturer_normalizer import normalize_manufacturer

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("=" * 80)
print("HP MANUFACTURER CHECK")
print("=" * 80)

# Test normalization
test_names = ['HP Inc', 'HP Inc.', 'hp', 'Hewlett Packard', 'Hewlett-Packard', 'HP']
print("\n1. Testing normalization:")
for name in test_names:
    normalized = normalize_manufacturer(name)
    print(f"   '{name}' → '{normalized}'")

# Check DB for HP manufacturers
print("\n2. Checking database for HP-related manufacturers:")
result = supabase.table('vw_manufacturers').select('id, name').execute()

hp_manufacturers = []
for mfr in result.data:
    name_lower = mfr['name'].lower()
    if 'hp' in name_lower or 'hewlett' in name_lower or 'packard' in name_lower:
        hp_manufacturers.append(mfr)
        print(f"   ✓ Found: {mfr['name']} (ID: {mfr['id']})")

if not hp_manufacturers:
    print("   ⚠️ No HP manufacturers found in database!")
elif len(hp_manufacturers) > 1:
    print(f"\n   ⚠️ WARNING: Found {len(hp_manufacturers)} HP manufacturers!")
    print("   This can cause product detection issues!")

# Check products for each HP manufacturer
print("\n3. Checking products per HP manufacturer:")
for mfr in hp_manufacturers:
    products = supabase.table('vw_products').select('id, model_number').eq('manufacturer_id', mfr['id']).limit(5).execute()
    print(f"\n   {mfr['name']} (ID: {mfr['id']}):")
    print(f"   Products: {len(products.data)}")
    if products.data:
        print("   Examples:")
        for p in products.data[:5]:
            print(f"      - {p['model_number']}")

print("\n" + "=" * 80)
print("RECOMMENDATION:")
print("=" * 80)

if len(hp_manufacturers) > 1:
    print("⚠️ Multiple HP manufacturers found!")
    print("   Solution: Merge all into one canonical 'Hewlett Packard' entry")
    print("   1. Pick one ID as canonical (e.g., oldest)")
    print("   2. Update all products to use that ID")
    print("   3. Delete duplicate manufacturer entries")
elif len(hp_manufacturers) == 1:
    canonical = normalize_manufacturer('HP Inc')
    if hp_manufacturers[0]['name'] != canonical:
        print(f"⚠️ Manufacturer name mismatch!")
        print(f"   DB has: '{hp_manufacturers[0]['name']}'")
        print(f"   Expected: '{canonical}'")
        print(f"   Solution: Rename manufacturer to '{canonical}'")
    else:
        print("✅ Everything looks good!")
else:
    print("⚠️ No HP manufacturer found - will be created on first document")
