"""
Check article codes for slot sprites from already extracted data
"""
import json
import re

# Load the Pandora data we already extracted
with open('foliant_javascript_analysis.json', encoding='utf-8') as f:
    data = json.load(f)

pandora = data['field_info']['Pandora']['value']

# Extract Articles table
articles_match = re.search(r'<Articles>(.*?)</Articles>', pandora, re.DOTALL)

if not articles_match:
    print("No Articles table found in C257i PDF")
    print("\nThis PDF might not have article codes in the Pandora field.")
    print("Let me check what we DO have...")
    
    # Check if FK-513 is mentioned
    if 'FK-513' in pandora:
        print("\n✅ FK-513 is mentioned in Pandora")
        # Extract context
        for line in pandora.split('\\n'):
            if 'FK-513' in line:
                print(f"  {line[:200]}")
else:
    articles_text = articles_match.group(1)
    
    # Parse CSV-like format
    lines = re.split(r'\\r|\\n', articles_text)
    lines = [line for line in lines if line.strip()]
    
    print("=" * 80)
    print("ARTICLE CODES FROM PANDORA")
    print("=" * 80)
    
    # Parse header
    if lines:
        header = lines[0].split(';')
        print(f"\nHeader: {header[:5]}")  # Show first 5 columns
        
        # Find FK-513 entries
        print(f"\n{'=' * 80}")
        print("FK-513 (Fax Kit) Article Codes:")
        print("=" * 80)
        
        fk_entries = [line for line in lines[1:] if 'FK-513' in line]
        for entry in fk_entries:
            parts = entry.split(';')
            if len(parts) >= 2:
                sprite = parts[0].strip()
                article = parts[1].strip()
                print(f"  {sprite:20} → {article}")
        
        if fk_entries:
            # Check if same
            articles_only = [line.split(';')[1].strip() for line in fk_entries if len(line.split(';')) > 1]
            unique = set(articles_only)
            
            if len(unique) == 1:
                print(f"\n  ✅ SAME ARTICLE CODE: {list(unique)[0]}")
                print(f"  → FK-513 is ONE product, can be installed in {len(fk_entries)} different slots")
            else:
                print(f"\n  ⚠️ DIFFERENT ARTICLE CODES: {unique}")
                print(f"  → These are {len(unique)} DIFFERENT products!")
        
        # Check if there are any WT or RU entries
        print(f"\n{'=' * 80}")
        print("Other Slot Patterns:")
        print("=" * 80)
        
        for pattern in ['WT-', 'RU-', 'HT-', 'PF-']:
            entries = [line for line in lines[1:] if pattern in line and '_' in line]
            if entries:
                print(f"\n{pattern}* entries found: {len(entries)}")
                for entry in entries[:5]:  # Show first 5
                    parts = entry.split(';')
                    if len(parts) >= 2:
                        sprite = parts[0].strip()
                        article = parts[1].strip()
                        print(f"  {sprite:20} → {article}")
