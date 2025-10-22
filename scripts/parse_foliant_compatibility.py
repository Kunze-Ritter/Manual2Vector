"""
Parse Foliant PDF compatibility logic from DynamicData/ValueSets
Extracts valid product configurations from JavaScript code
"""
import json
import re
from collections import defaultdict

def extract_compatibility_rules(pandora_value):
    """Extract compatibility rules from Pandora DynamicData"""
    
    print("Extracting compatibility rules from DynamicData...")
    print("=" * 80)
    
    # Find DynamicData section
    dynamic_match = re.search(r'<DynamicData>(.*?)</DynamicData>', pandora_value, re.DOTALL)
    if not dynamic_match:
        print("No DynamicData found")
        return []
    
    dynamic_data = dynamic_match.group(1)
    
    # Find all TABSUM calls with product arrays
    # Pattern: TABSUM('property',['product1','product2',...])
    tabsum_pattern = r"TABSUM\(['\"](\w+)['\"],\s*\[(.*?)\]\s*\)"
    matches = re.findall(tabsum_pattern, dynamic_data)
    
    configurations = []
    seen_configs = set()
    
    for property_name, products_str in matches:
        # Extract product list
        products = re.findall(r"['\"]([^'\"]+)['\"]", products_str)
        
        if products:
            # Create unique key for this configuration
            config_key = tuple(sorted(products))
            
            if config_key not in seen_configs:
                seen_configs.add(config_key)
                configurations.append({
                    'products': products,
                    'property': property_name,
                    'count': len(products)
                })
    
    return configurations

def analyze_configurations(configurations):
    """Analyze configurations to find patterns"""
    
    print(f"\nFound {len(configurations)} unique configurations")
    print("=" * 80)
    
    # Group by main product
    by_main_product = defaultdict(list)
    
    for config in configurations:
        products = config['products']
        
        # Find main product (C###i pattern)
        main_products = [p for p in products if re.match(r'C\d{3}[ie]', p)]
        
        if main_products:
            for main in main_products:
                by_main_product[main].append(config)
    
    # Analyze each main product
    compatibility_rules = []
    
    for main_product, configs in by_main_product.items():
        print(f"\n{main_product}:")
        print("-" * 80)
        
        # Get all accessories across all configs
        all_accessories = set()
        for config in configs:
            accessories = [p for p in config['products'] if not re.match(r'C\d{3}[ie]', p)]
            all_accessories.update(accessories)
        
        print(f"  Compatible accessories: {len(all_accessories)}")
        
        # Find which accessories appear together
        accessory_combinations = []
        for config in configs:
            accessories = [p for p in config['products'] if not re.match(r'C\d{3}[ie]', p)]
            if accessories:
                accessory_combinations.append(accessories)
        
        # Show sample configurations
        print(f"  Sample configurations:")
        for i, combo in enumerate(accessory_combinations[:3], 1):
            print(f"    Config {i}: {', '.join(combo[:5])}" + (" ..." if len(combo) > 5 else ""))
        
        compatibility_rules.append({
            'main_product': main_product,
            'compatible_accessories': list(all_accessories),
            'configurations': accessory_combinations
        })
    
    return compatibility_rules

def save_compatibility_rules(rules, output_file='foliant_compatibility_rules.json'):
    """Save rules to JSON file"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 80}")
    print(f"Saved {len(rules)} compatibility rules to: {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    # Load the Pandora data
    with open('foliant_javascript_analysis.json', encoding='utf-8') as f:
        data = json.load(f)
    
    pandora = data['field_info']['Pandora']['value']
    
    # Extract configurations
    configurations = extract_compatibility_rules(pandora)
    
    if configurations:
        print(f"\nTotal configurations found: {len(configurations)}")
        
        # Show first few
        print("\nSample configurations:")
        for i, config in enumerate(configurations[:5], 1):
            print(f"\n{i}. Property: {config['property']}")
            print(f"   Products ({config['count']}): {', '.join(config['products'][:10])}" + 
                  (" ..." if config['count'] > 10 else ""))
        
        # Analyze and create rules
        rules = analyze_configurations(configurations)
        
        # Save to file
        save_compatibility_rules(rules)
        
        # Summary
        print(f"\nSUMMARY:")
        print(f"  Main products: {len(rules)}")
        total_accessories = sum(len(r['compatible_accessories']) for r in rules)
        print(f"  Total accessory relationships: {total_accessories}")
        total_configs = sum(len(r['configurations']) for r in rules)
        print(f"  Total valid configurations: {total_configs}")
    else:
        print("No configurations found!")
