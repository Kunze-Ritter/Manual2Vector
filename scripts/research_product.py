"""
Product Research CLI
====================

Command-line tool for researching products online

Usage:
    # Research single product
    python scripts/research_product.py "Konica Minolta" "C750i"
    
    # Batch research products without specs
    python scripts/research_product.py --batch --limit 50
    
    # Force refresh cached research
    python scripts/research_product.py "HP" "LaserJet Pro M454dw" --force
    
    # Verify research results
    python scripts/research_product.py --verify
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv
from backend.research.product_researcher import ProductResearcher
from backend.research.research_integration import ResearchIntegration

# Load environment variables
project_root = Path(__file__).parent.parent
env_files = ['.env', '.env.database', '.env.external', '.env.ai']
print("Loading environment variables...")
for env_file in env_files:
    env_path = project_root / env_file
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"  ✓ Loaded: {env_file}")

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n❌ Error: SUPABASE credentials not found")
    sys.exit(1)

print(f"✓ Connected to Supabase: {SUPABASE_URL}\n")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def research_single_product(manufacturer: str, model: str, force: bool = False):
    """Research a single product"""
    print("=" * 80)
    print(f"Researching: {manufacturer} {model}")
    print("=" * 80)
    
    researcher = ProductResearcher(supabase=supabase)
    result = researcher.research_product(manufacturer, model, force_refresh=force)
    
    if result:
        print(f"\n✅ Research successful!")
        print(f"Confidence: {result.get('confidence', 0):.2f}")
        print(f"\n📋 Series: {result.get('series_name')}")
        print(f"Type: {result.get('product_type')}")
        
        if result.get('specifications'):
            print(f"\n📊 Specifications:")
            print(json.dumps(result['specifications'], indent=2))
        
        if result.get('oem_manufacturer'):
            print(f"\n🔄 OEM: {result['oem_manufacturer']}")
            if result.get('oem_notes'):
                print(f"   Notes: {result['oem_notes']}")
        
        if result.get('source_urls'):
            print(f"\n🔗 Sources:")
            for url in result['source_urls'][:3]:
                print(f"   - {url}")
    else:
        print(f"\n❌ Research failed")
        print(f"   Check logs for details")


def batch_research(limit: int = 50):
    """Batch research products without specs"""
    print("=" * 80)
    print(f"Batch Research (limit: {limit})")
    print("=" * 80)
    
    integration = ResearchIntegration(supabase=supabase, enabled=True)
    stats = integration.batch_enrich_products(limit=limit)
    
    print(f"\n✅ Batch research complete:")
    print(f"   Enriched: {stats['enriched']}")
    print(f"   Skipped: {stats['skipped']}")
    print(f"   Failed: {stats['failed']}")


def verify_research():
    """Show unverified research results for manual verification"""
    print("=" * 80)
    print("Unverified Research Results")
    print("=" * 80)
    
    try:
        results = supabase.table('product_research_cache').select(
            'manufacturer,model_number,series_name,product_type,confidence,source_urls'
        ).eq('verified', False).order('confidence', desc=True).limit(20).execute()
        
        if not results.data:
            print("\n✅ No unverified results")
            return
        
        print(f"\nFound {len(results.data)} unverified results:\n")
        
        for i, result in enumerate(results.data, 1):
            print(f"{i}. {result['manufacturer']} {result['model_number']}")
            print(f"   Series: {result.get('series_name', 'N/A')}")
            print(f"   Type: {result.get('product_type', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
            print(f"   Sources: {len(result.get('source_urls', []))} URLs")
            print()
        
        print("\nTo verify a result:")
        print("  python scripts/verify_research.py <manufacturer> <model>")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Research products online')
    parser.add_argument('manufacturer', nargs='?', help='Manufacturer name')
    parser.add_argument('model', nargs='?', help='Model number')
    parser.add_argument('--force', action='store_true', help='Force refresh cache')
    parser.add_argument('--batch', action='store_true', help='Batch research products')
    parser.add_argument('--limit', type=int, default=50, help='Batch limit')
    parser.add_argument('--verify', action='store_true', help='Show unverified results')
    
    args = parser.parse_args()
    
    if args.verify:
        verify_research()
    elif args.batch:
        batch_research(limit=args.limit)
    elif args.manufacturer and args.model:
        research_single_product(args.manufacturer, args.model, force=args.force)
    else:
        parser.print_help()
        print("\nExamples:")
        print('  python scripts/research_product.py "Konica Minolta" "C750i"')
        print('  python scripts/research_product.py --batch --limit 20')
        print('  python scripts/research_product.py --verify')


if __name__ == '__main__':
    main()
