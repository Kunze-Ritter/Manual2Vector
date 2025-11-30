"""
Find Registry.System.Logic in JavaScript
"""
import json
import re

# Load scripts
with open('foliant_all_javascript.json', encoding='utf-8') as f:
    scripts = json.load(f)

print("Searching for Registry.System.Logic...")
print("=" * 80)

for script in scripts:
    if script['type'] != 'document':
        continue
    
    name = script.get('name', 'unknown')
    code = script['code']
    
    # Search for Registry assignments
    registry_lines = []
    for line in code.split('\n'):
        if 'Registry.System.Logic' in line or 'Registry.System.Atoms' in line:
            registry_lines.append(line.strip())
    
    if registry_lines:
        print(f"\n{'=' * 80}")
        print(f"SCRIPT: {name}")
        print("=" * 80)
        
        for line in registry_lines[:20]:
            if len(line) > 120:
                print(f"  {line[:120]}...")
            else:
                print(f"  {line}")
        
        if len(registry_lines) > 20:
            print(f"  ... and {len(registry_lines) - 20} more")

# Also search for initialization
print(f"\n\n{'=' * 80}")
print("SEARCHING FOR INITIALIZATION")
print("=" * 80)

for script in scripts:
    if script['type'] != 'document':
        continue
    
    name = script.get('name', 'unknown')
    code = script['code']
    
    # Look for XML initialization
    if '<Logic>' in code or '<Atoms>' in code:
        print(f"\n{name}: Found XML structure!")
        
        # Extract XML
        xml_match = re.search(r'<Logic>.*?</Logic>', code, re.DOTALL)
        if xml_match:
            print(f"\nLogic XML:")
            print(xml_match.group(0)[:500])
        
        xml_match = re.search(r'<Atoms>.*?</Atoms>', code, re.DOTALL)
        if xml_match:
            print(f"\nAtoms XML:")
            print(xml_match.group(0)[:500])
