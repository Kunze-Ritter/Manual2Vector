"""
Visualize Foliant compatibility configurations
Shows compatible and incompatible combinations
"""
import json
from collections import defaultdict

def load_rules():
    """Load compatibility rules"""
    with open('foliant_compatibility_rules.json', encoding='utf-8') as f:
        return json.load(f)

def analyze_compatibility(rules):
    """Analyze which accessories are compatible/incompatible"""
    
    print("=" * 80)
    print("FOLIANT COMPATIBILITY ANALYSIS")
    print("=" * 80)
    
    for rule in rules:
        main_product = rule['main_product']
        configs = rule['configurations']
        all_accessories = rule['compatible_accessories']
        
        print(f"\n{'=' * 80}")
        print(f"PRODUCT: {main_product}")
        print("=" * 80)
        
        # Show configurations
        print(f"\n✅ VALID CONFIGURATIONS ({len(configs)}):")
        print("-" * 80)
        
        for i, config in enumerate(configs, 1):
            print(f"\nConfiguration {i}:")
            print(f"  📦 {main_product}")
            for accessory in config:
                # Determine type
                if accessory.startswith('FS-'):
                    icon = "🔧"
                    type_name = "Finisher"
                elif accessory.startswith('PK-'):
                    icon = "🔨"
                    type_name = "Punch Kit"
                elif accessory.startswith('LU-'):
                    icon = "📥"
                    type_name = "Large Capacity"
                elif accessory.startswith('DF-'):
                    icon = "📄"
                    type_name = "Document Feeder"
                elif accessory.startswith('PC-') or accessory.startswith('DK-'):
                    icon = "🗄️"
                    type_name = "Cabinet"
                elif accessory.startswith('OT-'):
                    icon = "📤"
                    type_name = "Output Tray"
                elif accessory.startswith('WT-'):
                    icon = "🗑️"
                    type_name = "Waste Toner"
                else:
                    icon = "⚙️"
                    type_name = "Accessory"
                
                print(f"  {icon} {accessory:15} ({type_name})")
        
        # Analyze mutual exclusivity
        print(f"\n❌ INCOMPATIBLE COMBINATIONS:")
        print("-" * 80)
        
        # Find accessories that never appear together
        incompatibilities = find_incompatibilities(configs, all_accessories)
        
        if incompatibilities:
            for accessory1, incompatible_with in incompatibilities.items():
                if incompatible_with:
                    print(f"\n  {accessory1} is INCOMPATIBLE with:")
                    for accessory2 in sorted(incompatible_with):
                        print(f"    ❌ {accessory2}")
        else:
            print("  No strict incompatibilities found")
            print("  (All accessories can potentially be combined)")
        
        # Analyze co-occurrence patterns
        print(f"\n🔗 CO-OCCURRENCE PATTERNS:")
        print("-" * 80)
        
        cooccurrence = analyze_cooccurrence(configs)
        
        # Show strong relationships
        for accessory, partners in sorted(cooccurrence.items()):
            if len(partners) > 1:
                print(f"\n  {accessory} often appears with:")
                for partner, count in sorted(partners.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / len(configs)) * 100
                    print(f"    • {partner:15} ({count}/{len(configs)} configs, {percentage:.0f}%)")

def find_incompatibilities(configs, all_accessories):
    """Find accessories that never appear together"""
    
    incompatibilities = defaultdict(set)
    
    # For each pair of accessories
    for i, acc1 in enumerate(all_accessories):
        for acc2 in all_accessories[i+1:]:
            # Check if they ever appear together
            appear_together = False
            
            for config in configs:
                if acc1 in config and acc2 in config:
                    appear_together = True
                    break
            
            # If they never appear together, they might be incompatible
            if not appear_together:
                # But only if both appear in at least one config
                acc1_appears = any(acc1 in config for config in configs)
                acc2_appears = any(acc2 in config for config in configs)
                
                if acc1_appears and acc2_appears:
                    incompatibilities[acc1].add(acc2)
                    incompatibilities[acc2].add(acc1)
    
    return incompatibilities

def analyze_cooccurrence(configs):
    """Analyze which accessories appear together"""
    
    cooccurrence = defaultdict(lambda: defaultdict(int))
    
    for config in configs:
        for accessory in config:
            for partner in config:
                if accessory != partner:
                    cooccurrence[accessory][partner] += 1
    
    return cooccurrence

def create_summary(rules):
    """Create a summary of all rules"""
    
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print("=" * 80)
    
    total_products = len(rules)
    total_accessories = sum(len(r['compatible_accessories']) for r in rules)
    total_configs = sum(len(r['configurations']) for r in rules)
    
    print(f"\n📊 Statistics:")
    print(f"  • Main products: {total_products}")
    print(f"  • Total accessory relationships: {total_accessories}")
    print(f"  • Total valid configurations: {total_configs}")
    print(f"  • Average accessories per product: {total_accessories / total_products:.1f}")
    print(f"  • Average configs per product: {total_configs / total_products:.1f}")
    
    # Find most common accessories
    accessory_count = defaultdict(int)
    for rule in rules:
        for accessory in rule['compatible_accessories']:
            accessory_count[accessory] += 1
    
    print(f"\n🏆 Most compatible accessories (work with all products):")
    for accessory, count in sorted(accessory_count.items(), key=lambda x: x[1], reverse=True):
        if count == total_products:
            print(f"  ✅ {accessory}")

if __name__ == "__main__":
    rules = load_rules()
    
    # Analyze first product in detail
    if rules:
        analyze_compatibility([rules[0]])  # Show only first product for clarity
        
        # Summary for all
        create_summary(rules)
