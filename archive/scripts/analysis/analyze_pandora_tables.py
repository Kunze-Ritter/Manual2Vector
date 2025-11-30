"""
Analyze all tables in Pandora field to find compatibility logic
"""
import json
import re

# Load the JSON
with open('foliant_javascript_analysis.json', encoding='utf-8') as f:
    data = json.load(f)

pandora = data['field_info']['Pandora']['value']

print("Analyzing Pandora field for tables...")
print("=" * 80)

# Find all XML tags
tags = re.findall(r'<(\w+)[^>]*>', pandora)
unique_tags = set(tags)

print(f"\nFound XML tags: {sorted(unique_tags)}")
print()

# Extract each table
for tag in sorted(unique_tags):
    pattern = f'<{tag}[^>]*>(.*?)</{tag}>'
    matches = re.findall(pattern, pandora, re.DOTALL)
    
    if matches:
        print(f"\n{'=' * 80}")
        print(f"TABLE: {tag}")
        print("=" * 80)
        
        for i, match in enumerate(matches, 1):
            # Show first 500 chars
            preview = match[:500].replace('\\r', '\n')
            print(f"\nInstance {i}:")
            print(preview)
            if len(match) > 500:
                print(f"... ({len(match)} total chars)")
            print()

# Look for compatibility keywords
print("\n" + "=" * 80)
print("SEARCHING FOR COMPATIBILITY KEYWORDS")
print("=" * 80)

keywords = ['compat', 'require', 'depend', 'conflict', 'mutual', 'exclusive', 
            'max', 'min', 'qty', 'quantity', 'limit', 'allow', 'forbid']

for keyword in keywords:
    if keyword.lower() in pandora.lower():
        # Find context around keyword
        pattern = f'.{{0,100}}{keyword}.{{0,100}}'
        matches = re.findall(pattern, pandora, re.IGNORECASE)
        if matches:
            print(f"\nKeyword '{keyword}' found ({len(matches)} times):")
            for match in matches[:3]:  # Show first 3
                print(f"  ...{match}...")
