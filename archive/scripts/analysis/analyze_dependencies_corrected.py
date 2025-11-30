"""
Analyze dependencies with CORRECTED logic:
- Mounting positions (top/side/bottom/internal/accessory) are COMPATIBLE
- Mutual exclusivity only WITHIN same position (based on max_quantity)
"""
import json
from collections import defaultdict

# Load data
with open('foliant_all_sprites.json', encoding='utf-8') as f:
    sprites_data = json.load(f)

with open('foliant_compatibility_rules.json', encoding='utf-8') as f:
    tabsum_rules = json.load(f)

with open('foliant_compatibility_matrix.json', encoding='utf-8') as f:
    matrix = json.load(f)

print("=" * 80)
print("CORRECTED DEPENDENCY ANALYSIS")
print("=" * 80)
print("\n✅ KEY INSIGHT: Mounting positions are COMPATIBLE with each other!")
print("   TOP + SIDE + BOTTOM + INTERNAL + ACCESSORY = All can be combined\n")

for rule in tabsum_rules:
    main_product = rule['main_product']
    configs = rule['configurations']
    
    print(f"\n{'=' * 80}")
    print(f"PRODUCT: {main_product}")
    print("=" * 80)
    
    # Categorize accessories by mounting position
    def get_mounting_position(accessory):
        if accessory.startswith('DF-'):
            return 'top'
        elif accessory.startswith(('FS-', 'LU-', 'JS-', 'RU-')):
            return 'side'
        elif accessory.startswith(('PC-', 'DK-', 'WT-')):
            return 'bottom'
        elif accessory.startswith(('CU-', 'EK-', 'IC-', 'AU-', 'UK-', 'FK-', 'SX-')):
            return 'internal'
        else:
            return 'accessory'
    
    # Analyze each configuration
    print(f"\n📊 CONFIGURATION ANALYSIS:")
    print("-" * 80)
    
    for i, config in enumerate(configs, 1):
        by_position = defaultdict(list)
        for accessory in config:
            pos = get_mounting_position(accessory)
            by_position[pos].append(accessory)
        
        print(f"\nConfig {i}:")
        for position in ['top', 'side', 'bottom', 'internal', 'accessory']:
            if position in by_position:
                items = by_position[position]
                print(f"  {position.upper():12} ({len(items)}): {', '.join(items)}")
    
    # Find REAL dependencies (always appear together)
    print(f"\n\n🔗 DEPENDENCIES (Always appear together):")
    print("-" * 80)
    
    accessory_count = defaultdict(int)
    for config in configs:
        for accessory in config:
            accessory_count[accessory] += 1
    
    dependencies = []
    for accessory in sorted(accessory_count.keys()):
        count = accessory_count[accessory]
        
        # Find what ALWAYS appears with this accessory
        appears_with = defaultdict(int)
        for config in configs:
            if accessory in config:
                for other in config:
                    if other != accessory:
                        appears_with[other] += 1
        
        # Filter: only show if they appear together in ALL occurrences
        always_with = [other for other, other_count in appears_with.items() 
                       if other_count == count]
        
        if always_with:
            pos = get_mounting_position(accessory)
            print(f"\n  {accessory} ({pos.upper()})")
            print(f"    Always appears with:")
            for other in sorted(always_with):
                other_pos = get_mounting_position(other)
                print(f"      → {other} ({other_pos.upper()})")
            
            dependencies.append({
                'accessory': accessory,
                'requires': always_with
            })
    
    # Mutual exclusivity WITHIN same position
    print(f"\n\n❌ MUTUAL EXCLUSIVITY (Within same position):")
    print("-" * 80)
    
    # Group by position
    by_position_all = defaultdict(set)
    for accessory in accessory_count.keys():
        pos = get_mounting_position(accessory)
        by_position_all[pos].add(accessory)
    
    for position, accessories in sorted(by_position_all.items()):
        if len(accessories) > 1:
            # Get max_quantity for this position
            max_qty = None
            for product_rule in matrix:
                if product_rule['main_product'] == main_product:
                    if position in product_rule['compatible_options']:
                        max_qty = product_rule['compatible_options'][position]['max_quantity']
                        break
            
            print(f"\n  {position.upper()} (max {max_qty if max_qty else '?'}):")
            print(f"    Options: {', '.join(sorted(accessories))}")
            
            if max_qty:
                if max_qty == 1:
                    print(f"    ⚠️ Only 1x allowed → All are mutually exclusive")
                elif max_qty < len(accessories):
                    print(f"    ⚠️ Max {max_qty}x allowed → Choose up to {max_qty}")
                else:
                    print(f"    ✅ All can be combined (max {max_qty})")
            else:
                print(f"    ℹ️ Max quantity not defined")

print(f"\n\n{'=' * 80}")
print("SUMMARY")
print("=" * 80)
print("""
✅ CORRECTED UNDERSTANDING:

1. **Mounting positions are COMPATIBLE:**
   - You CAN combine TOP + SIDE + BOTTOM + INTERNAL + ACCESSORY
   - Example: DF-633 (top) + FS-539 (side) + PC-418 (bottom) = ✅ VALID

2. **Mutual exclusivity is WITHIN positions:**
   - TOP: max 1 → Only 1x document feeder
   - SIDE: max 3 → Up to 3x finishers/units
   - BOTTOM: max 1 → Only 1x cabinet/desk
   - INTERNAL: max 5 → Up to 5x controllers
   - ACCESSORY: max 10 → Up to 10x kits

3. **Dependencies are REAL requirements:**
   - If FS-539 always appears with PK-519 → PK-519 is likely required
   - If LU-301 always appears with BT-C1e → BT-C1e is required for large capacity

4. **Agent can now validate:**
   - Check if configuration respects max_quantity per position
   - Check if required accessories are included
   - Suggest compatible additions based on remaining slots
""")
