"""Fix all manufacturer configs to use Pydantic-compatible product_types"""

import re
from pathlib import Path

# Mapping of old types to new types
TYPE_MAPPING = {
    'laser_printer': 'printer',
    'laser_multifunction': 'multifunction',
    'laser_production_printer': 'printer',
    'inkjet_multifunction': 'multifunction',
    'inkjet_printer': 'printer',
    'solid_ink_printer': 'printer',
    'large_format_printer': 'plotter',
}

configs_dir = Path('backend/configs')

for config_file in configs_dir.glob('*.yaml'):
    print(f"Processing {config_file.name}...")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Replace all old types with new types
    for old_type, new_type in TYPE_MAPPING.items():
        # Replace in type: "old_type" format
        content = re.sub(
            rf'type:\s*["\']?{old_type}["\']?',
            f'type: "{new_type}"',
            content
        )
    
    if content != original:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Updated {config_file.name}")
    else:
        print(f"  - No changes needed for {config_file.name}")

print("\n✅ All configs updated!")
