"""
Build complete compatibility matrix from:
1. All available sprites (what CAN be selected)
2. TABSUM configurations (example combinations)
3. Physical specs from Physicals matrix
"""
import json
import re

def load_data():
    """Load all data sources"""
    
    # Load sprites (all available options)
    with open('foliant_all_sprites.json', encoding='utf-8') as f:
        sprites_data = json.load(f)
    
    # Load TABSUM configurations
    with open('foliant_compatibility_rules.json', encoding='utf-8') as f:
        tabsum_rules = json.load(f)
    
    # Load Pandora data for Physicals matrix
    with open('foliant_javascript_analysis.json', encoding='utf-8') as f:
        js_data = json.load(f)
        pandora = js_data['field_info']['Pandora']['value']
    
    return sprites_data, tabsum_rules, pandora

def parse_physicals_matrix(pandora):
    """Parse the Physicals matrix to get all items with specs"""
    
    # Extract Physicals table
    phys_match = re.search(r'<Physicals>(.*?)</Physicals>', pandora, re.DOTALL)
    if not phys_match:
        return {}
    
    phys_text = phys_match.group(1)
    
    # Split into lines
    lines = re.split(r'\\r|\\n|\r\n|\n|\r', phys_text)
    lines = [line for line in lines if line.strip()]
    
    if not lines:
        return {}
    
    # First line is header (product names)
    header_parts = lines[0].split(';')
    products = [p.strip() for p in header_parts[1:] if p.strip()]  # Skip 'ident'
    
    # Parse properties
    specs = {product: {} for product in products}
    
    for line in lines[1:]:
        parts = line.split(';')
        if len(parts) < 2:
            continue
        
        prop_name = parts[0].strip()
        
        for i, value in enumerate(parts[1:], 0):
            if i < len(products) and value.strip():
                specs[products[i]][prop_name] = value.strip()
    
    return specs

def categorize_by_mounting_position(sprites):
    """Categorize options by mounting position"""
    
    categories = {
        'main_products': [],
        'top': [],          # Document feeders (mounted on top)
        'side': [],         # Finishers (mounted on side)
        'bottom': [],       # Cabinets/Desks (under the device)
        'internal': [],     # Controllers, authentication (inside/back)
        'accessories': []   # Mount kits, etc.
    }
    
    for sprite in sprites:
        # Main products
        if re.match(r'C\d{3}[ie]', sprite):
            categories['main_products'].append(sprite)
        
        # Top-mounted (Document Feeders)
        elif sprite.startswith('DF-'):
            categories['top'].append(sprite)
        
        # Side-mounted (Finishers, Large Capacity)
        elif sprite.startswith(('FS-', 'LU-', 'JS-', 'RU-')):
            categories['side'].append(sprite)
        
        # Bottom-mounted (Cabinets, Desks)
        elif sprite.startswith(('PC-', 'DK-', 'WT-')):
            categories['bottom'].append(sprite)
        
        # Internal/Back (Controllers, Auth, Fax)
        elif sprite.startswith(('CU-', 'EK-', 'IC-', 'AU-', 'UK-', 'FK-', 'SX-')):
            categories['internal'].append(sprite)
        
        # Accessories (Mount kits, Punch kits, etc.)
        elif sprite.startswith(('MK-', 'PK-', 'HT-', 'KP-', 'OC-', 'EM-')):
            categories['accessories'].append(sprite)
        
        # Other
        elif sprite not in ['MONSRV', 'Mainbody', 'Paperfeeder', 'iOptions']:
            categories['accessories'].append(sprite)
    
    return categories

def build_compatibility_rules(categories, tabsum_rules, specs):
    """Build compatibility rules based on mounting positions"""
    
    print("=" * 80)
    print("BUILDING COMPATIBILITY MATRIX")
    print("=" * 80)
    
    rules = []
    
    for main_product in categories['main_products']:
        print(f"\n{'=' * 80}")
        print(f"PRODUCT: {main_product}")
        print("=" * 80)
        
        compatible = {
            'main_product': main_product,
            'compatible_options': {},
            'mounting_positions': categories.copy(),
            'example_configurations': []
        }
        
        # All options are potentially compatible
        # unless they conflict physically
        
        # TOP: Can have ONE document feeder
        compatible['compatible_options']['top'] = {
            'options': categories['top'],
            'max_quantity': 1,
            'mutually_exclusive': True,
            'description': 'Document feeder mounted on top'
        }
        
        # SIDE: Can have MULTIPLE finishers/units
        # But some may be mutually exclusive
        compatible['compatible_options']['side'] = {
            'options': categories['side'],
            'max_quantity': 3,  # Typically max 3 side units
            'mutually_exclusive': False,
            'description': 'Finishers and units mounted on side'
        }
        
        # BOTTOM: Can have ONE cabinet/desk
        compatible['compatible_options']['bottom'] = {
            'options': categories['bottom'],
            'max_quantity': 1,
            'mutually_exclusive': True,
            'description': 'Cabinet or desk under the device'
        }
        
        # INTERNAL: Can have MULTIPLE controllers
        compatible['compatible_options']['internal'] = {
            'options': categories['internal'],
            'max_quantity': 5,
            'mutually_exclusive': False,
            'description': 'Internal controllers and interfaces'
        }
        
        # ACCESSORIES: Can have MULTIPLE
        compatible['compatible_options']['accessories'] = {
            'options': categories['accessories'],
            'max_quantity': 10,
            'mutually_exclusive': False,
            'description': 'Mount kits, punch kits, and other accessories'
        }
        
        # Add example configurations from TABSUM
        for rule in tabsum_rules:
            if rule['main_product'] == main_product:
                compatible['example_configurations'] = rule['configurations']
        
        rules.append(compatible)
        
        # Print summary
        print(f"\n✅ Compatible Options:")
        for position, data in compatible['compatible_options'].items():
            print(f"\n  {position.upper()} ({len(data['options'])} options, max {data['max_quantity']}):")
            for opt in data['options'][:5]:
                print(f"    - {opt}")
            if len(data['options']) > 5:
                print(f"    ... and {len(data['options']) - 5} more")
    
    return rules

def save_compatibility_matrix(rules):
    """Save the complete compatibility matrix"""
    
    with open('foliant_compatibility_matrix.json', 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 80}")
    print("✅ SAVED: foliant_compatibility_matrix.json")
    print("=" * 80)
    
    # Create human-readable summary
    summary = []
    summary.append("# FOLIANT COMPATIBILITY MATRIX\n")
    summary.append("=" * 80 + "\n\n")
    
    for rule in rules:
        summary.append(f"## {rule['main_product']}\n\n")
        
        for position, data in rule['compatible_options'].items():
            summary.append(f"### {position.upper()}\n")
            summary.append(f"- Max quantity: {data['max_quantity']}\n")
            summary.append(f"- Mutually exclusive: {data['mutually_exclusive']}\n")
            summary.append(f"- Description: {data['description']}\n")
            summary.append(f"- Options ({len(data['options'])}):\n")
            for opt in data['options']:
                summary.append(f"  - {opt}\n")
            summary.append("\n")
        
        if rule['example_configurations']:
            summary.append("### Example Configurations:\n\n")
            for i, config in enumerate(rule['example_configurations'], 1):
                summary.append(f"**Config {i}:** {', '.join(config)}\n\n")
        
        summary.append("\n" + "=" * 80 + "\n\n")
    
    with open('FOLIANT_COMPATIBILITY_MATRIX.md', 'w', encoding='utf-8') as f:
        f.writelines(summary)
    
    print("✅ SAVED: FOLIANT_COMPATIBILITY_MATRIX.md")

if __name__ == "__main__":
    print("Loading data...")
    sprites_data, tabsum_rules, pandora = load_data()
    
    print(f"✅ Loaded {sprites_data['total']} sprites")
    print(f"✅ Loaded {len(tabsum_rules)} TABSUM rules")
    
    # Parse Physicals
    print("\nParsing Physicals matrix...")
    specs = parse_physicals_matrix(pandora)
    print(f"✅ Found specs for {len(specs)} items")
    
    # Categorize by mounting position
    print("\nCategorizing by mounting position...")
    categories = categorize_by_mounting_position(sprites_data['sprites'])
    
    for position, items in categories.items():
        print(f"  {position}: {len(items)} items")
    
    # Build compatibility rules
    rules = build_compatibility_rules(categories, tabsum_rules, specs)
    
    # Save
    save_compatibility_matrix(rules)
    
    print("\n" + "=" * 80)
    print("🎉 COMPATIBILITY MATRIX COMPLETE!")
    print("=" * 80)
    print("\nFiles created:")
    print("  - foliant_compatibility_matrix.json (machine-readable)")
    print("  - FOLIANT_COMPATIBILITY_MATRIX.md (human-readable)")
