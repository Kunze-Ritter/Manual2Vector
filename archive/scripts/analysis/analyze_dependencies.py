"""
Analyze dependencies from TABSUM configurations
Find which accessories always appear together (potential dependencies)
"""
import json
from collections import defaultdict

# Load compatibility rules
with open('foliant_compatibility_rules.json', encoding='utf-8') as f:
    rules = json.load(f)

print("=" * 80)
print("DEPENDENCY ANALYSIS")
print("=" * 80)

for rule in rules:
    main_product = rule['main_product']
    configs = rule['configurations']
    
    print(f"\n{'=' * 80}")
    print(f"PRODUCT: {main_product}")
    print("=" * 80)
    
    # Count how often each accessory appears
    accessory_count = defaultdict(int)
    for config in configs:
        for accessory in config:
            accessory_count[accessory] += 1
    
    # Find accessories that ALWAYS appear together
    print(f"\n🔗 POTENTIAL DEPENDENCIES:")
    print("-" * 80)
    
    dependencies = []
    
    for accessory in sorted(accessory_count.keys()):
        count = accessory_count[accessory]
        percentage = (count / len(configs)) * 100
        
        # Find what this accessory appears with
        appears_with = defaultdict(int)
        for config in configs:
            if accessory in config:
                for other in config:
                    if other != accessory:
                        appears_with[other] += 1
        
        # Check if any accessory ALWAYS appears with this one
        always_with = []
        for other, other_count in appears_with.items():
            if other_count == count:  # Appears in ALL configs where accessory appears
                always_with.append(other)
        
        if always_with:
            print(f"\n  {accessory} ({count}/{len(configs)} configs, {percentage:.0f}%)")
            print(f"    ALWAYS appears with:")
            for other in sorted(always_with):
                other_percentage = (accessory_count[other] / len(configs)) * 100
                print(f"      → {other} ({accessory_count[other]}/{len(configs)} configs, {other_percentage:.0f}%)")
            
            # Store potential dependency
            dependencies.append({
                'accessory': accessory,
                'requires': always_with,
                'confidence': 'high' if count == len(configs) else 'medium'
            })
    
    if not dependencies:
        print("\n  No strong dependencies found")
        print("  (Accessories can be used independently)")
    
    # Find accessories that NEVER appear together (mutual exclusivity)
    print(f"\n\n❌ MUTUAL EXCLUSIVITY:")
    print("-" * 80)
    
    exclusions = []
    accessories = list(accessory_count.keys())
    
    for i, acc1 in enumerate(accessories):
        for acc2 in accessories[i+1:]:
            # Check if they ever appear together
            appear_together = False
            for config in configs:
                if acc1 in config and acc2 in config:
                    appear_together = True
                    break
            
            if not appear_together:
                # They never appear together
                # But only if both appear in at least one config
                if accessory_count[acc1] > 0 and accessory_count[acc2] > 0:
                    exclusions.append((acc1, acc2))
    
    if exclusions:
        for acc1, acc2 in sorted(exclusions):
            print(f"\n  {acc1} ⚔️ {acc2}")
            print(f"    Never appear together in any configuration")
    else:
        print("\n  No mutual exclusivity found")
        print("  (All accessories can potentially be combined)")

print(f"\n\n{'=' * 80}")
print("SUMMARY")
print("=" * 80)
print("""
Dependencies found indicate accessories that are ALWAYS used together.
This could mean:
1. One accessory REQUIRES the other (e.g., Finisher requires Relay Unit)
2. They are part of a standard package
3. They are physically connected

Mutual exclusivity indicates accessories that NEVER appear together.
This could mean:
1. They occupy the same physical space
2. They serve the same function (only one needed)
3. They are incompatible for technical reasons
""")
