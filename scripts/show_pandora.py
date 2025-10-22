import json

with open('foliant_javascript_analysis.json', encoding='utf-8') as f:
    data = json.load(f)

pandora = data['field_info']['Pandora']['value']
print("Pandora field (first 1000 chars):")
print("=" * 80)
print(pandora[:1000])
print("\n...")
print(f"\nTotal length: {len(pandora)} characters")
