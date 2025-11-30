"""
Analyze ALL Foliant PDFs to build comprehensive compatibility matrix
"""
import PyPDF2
import json
import re
from pathlib import Path
from collections import defaultdict

def extract_sprites_from_pdf(pdf_path):
    """Extract all Sprite_ fields from PDF"""
    sprites = []
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            catalog = pdf.trailer["/Root"]
            if hasattr(catalog, 'get_object'):
                catalog = catalog.get_object()
            
            acroform = catalog["/AcroForm"]
            if hasattr(acroform, 'get_object'):
                acroform = acroform.get_object()
            
            fields = acroform["/Fields"]
            
            for field_ref in fields:
                field = field_ref.get_object()
                field_name = field.get("/T", "")
                
                if field_name.startswith("Sprite_"):
                    option_name = field_name.replace("Sprite_", "")
                    sprites.append(option_name)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []
    
    return sprites

def categorize_sprite(sprite):
    """Categorize sprite by mounting position"""
    if re.match(r'C\d{3}[ie]', sprite) or sprite.startswith('AP'):
        return 'main_product'
    elif sprite.startswith('DF-'):
        return 'top'
    elif sprite.startswith(('FS-', 'LU-', 'JS-', 'RU-', 'SD-')):
        return 'side'
    elif sprite.startswith(('PC-', 'DK-', 'WT-')):
        return 'bottom'
    elif sprite.startswith(('CU-', 'EK-', 'IC-', 'AU-', 'UK-', 'FK-', 'SX-', 'IQ-', 'MIC-')):
        return 'internal'
    else:
        return 'accessory'

def analyze_all_pdfs():
    """Analyze all PDFs in input_foliant directory"""
    
    input_dir = Path("input_foliant")
    pdf_files = list(input_dir.glob("*.pdf"))
    
    # Also check processed directory
    processed_dir = input_dir / "processed"
    pdf_files.extend(list(processed_dir.glob("*.pdf")))
    
    print("=" * 80)
    print(f"ANALYZING {len(pdf_files)} FOLIANT PDFs")
    print("=" * 80)
    
    all_results = []
    all_sprites = set()
    by_position = defaultdict(set)
    by_product_series = defaultdict(lambda: defaultdict(set))
    
    for pdf_file in sorted(pdf_files):
        print(f"\n{'=' * 80}")
        print(f"Processing: {pdf_file.name}")
        print("=" * 80)
        
        sprites = extract_sprites_from_pdf(pdf_file)
        
        if not sprites:
            print("  ⚠️ No sprites found")
            continue
        
        print(f"  ✅ Found {len(sprites)} sprites")
        
        # Categorize
        main_products = []
        categories = defaultdict(list)
        
        for sprite in sprites:
            category = categorize_sprite(sprite)
            categories[category].append(sprite)
            all_sprites.add(sprite)
            by_position[category].add(sprite)
            
            if category == 'main_product':
                main_products.append(sprite)
        
        # Determine product series
        series_name = "Unknown"
        if "bizhub" in pdf_file.name.lower():
            series_name = "bizhub"
        elif "accurio" in pdf_file.name.lower():
            series_name = "AccurioPress"
        
        # Store by series
        for position, items in categories.items():
            for item in items:
                by_product_series[series_name][position].add(item)
        
        # Print summary
        print(f"\n  Main Products ({len(main_products)}):")
        for prod in sorted(main_products)[:10]:
            print(f"    - {prod}")
        if len(main_products) > 10:
            print(f"    ... and {len(main_products) - 10} more")
        
        for position in ['top', 'side', 'bottom', 'internal', 'accessory']:
            if position in categories:
                items = categories[position]
                print(f"  {position.upper()} ({len(items)}): {', '.join(sorted(items)[:5])}" + 
                      (f" ... +{len(items)-5}" if len(items) > 5 else ""))
        
        all_results.append({
            'pdf': pdf_file.name,
            'series': series_name,
            'main_products': main_products,
            'sprites': sprites,
            'categories': {k: list(v) for k, v in categories.items()}
        })
    
    # Summary
    print(f"\n\n{'=' * 80}")
    print("GLOBAL SUMMARY")
    print("=" * 80)
    
    print(f"\nTotal unique sprites across all PDFs: {len(all_sprites)}")
    
    print(f"\n📊 BY MOUNTING POSITION:")
    for position in ['main_product', 'top', 'side', 'bottom', 'internal', 'accessory']:
        if position in by_position:
            items = by_position[position]
            print(f"\n  {position.upper()} ({len(items)} unique):")
            for item in sorted(items)[:20]:
                print(f"    - {item}")
            if len(items) > 20:
                print(f"    ... and {len(items) - 20} more")
    
    print(f"\n\n📊 BY PRODUCT SERIES:")
    for series, positions in sorted(by_product_series.items()):
        print(f"\n  {series}:")
        for position in ['top', 'side', 'bottom', 'internal', 'accessory']:
            if position in positions:
                items = positions[position]
                print(f"    {position.upper()}: {len(items)} options")
    
    # Find common accessories (appear in multiple series)
    print(f"\n\n🔗 COMMON ACCESSORIES (across series):")
    accessory_count = defaultdict(set)
    for result in all_results:
        series = result['series']
        for sprite in result['sprites']:
            if categorize_sprite(sprite) != 'main_product':
                accessory_count[sprite].add(series)
    
    common = [(acc, series) for acc, series in accessory_count.items() if len(series) > 1]
    common.sort(key=lambda x: len(x[1]), reverse=True)
    
    for acc, series in common[:30]:
        print(f"  {acc:20} → {', '.join(sorted(series))}")
    
    # Save results
    output = {
        'total_pdfs': len(pdf_files),
        'total_sprites': len(all_sprites),
        'by_position': {k: sorted(list(v)) for k, v in by_position.items()},
        'by_series': {k: {pos: sorted(list(items)) for pos, items in positions.items()} 
                      for k, positions in by_product_series.items()},
        'common_accessories': [(acc, sorted(list(series))) for acc, series in common],
        'pdf_results': all_results
    }
    
    with open('foliant_all_pdfs_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n{'=' * 80}")
    print("✅ SAVED: foliant_all_pdfs_analysis.json")
    print("=" * 80)
    
    return output

if __name__ == "__main__":
    results = analyze_all_pdfs()
    
    print(f"\n\n{'=' * 80}")
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("""
Based on this analysis, we can now:

1. ✅ Build a UNIVERSAL compatibility matrix
   - Common accessories work across multiple series
   - Series-specific accessories are clearly identified

2. ✅ Define mounting position rules globally
   - TOP: Document feeders (DF-*)
   - SIDE: Finishers (FS-*, SD-*), Large Capacity (LU-*)
   - BOTTOM: Cabinets (PC-*, DK-*), Working Tables (WT-*)
   - INTERNAL: Controllers (CU-*, EK-*, IQ-*), Auth (AU-*, UK-*)
   - ACCESSORY: Kits (MK-*, PK-*, HT-*)

3. ✅ Import all data to database
   - Create product_accessories entries for all combinations
   - Use mounting_position and slot_number from Migration 111

4. ✅ Agent can now answer:
   - "Which accessories work with bizhub C257i?"
   - "Is FS-539 compatible with AccurioPress 7136?"
   - "What's the difference between C257i and C751i accessories?"
""")
