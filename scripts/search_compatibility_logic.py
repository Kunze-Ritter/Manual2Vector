"""
Search for compatibility logic in JavaScript
"""
import json
import re

# Load scripts
with open('foliant_all_javascript.json', encoding='utf-8') as f:
    scripts = json.load(f)

print("Searching for compatibility logic...")
print("=" * 80)

# Keywords to search for
keywords = ['depend', 'compat', 'conflict', 'mutual', 'exclusive', 
            'require', 'forbid', 'allow', 'enable', 'disable', 'check']

for script in scripts:
    if script['type'] != 'document':
        continue
    
    name = script['name']
    code = script['code']
    
    print(f"\n{'=' * 80}")
    print(f"SCRIPT: {name}")
    print("=" * 80)
    
    # Search for each keyword
    found_lines = []
    for line in code.split('\n'):
        line_lower = line.lower()
        for keyword in keywords:
            if keyword in line_lower and len(line.strip()) > 10:
                found_lines.append((keyword, line.strip()))
                break
    
    if found_lines:
        print(f"\nFound {len(found_lines)} relevant lines:")
        
        # Group by keyword
        by_keyword = {}
        for keyword, line in found_lines:
            if keyword not in by_keyword:
                by_keyword[keyword] = []
            by_keyword[keyword].append(line)
        
        for keyword, lines in sorted(by_keyword.items()):
            print(f"\n  {keyword.upper()} ({len(lines)} lines):")
            for line in lines[:5]:  # Show first 5
                if len(line) > 100:
                    print(f"    {line[:100]}...")
                else:
                    print(f"    {line}")
            if len(lines) > 5:
                print(f"    ... and {len(lines) - 5} more")

# Focus on ButtonHandler and IconHandler
print(f"\n\n{'=' * 80}")
print("DETAILED ANALYSIS: ButtonHandler")
print("=" * 80)

bh = [s for s in scripts if s['name'] == 'ButtonHandler'][0]
code = bh['code']

# Look for function definitions
functions = re.findall(r'function\s+(\w+)\s*\([^)]*\)\s*{', code)
print(f"\nFound {len(functions)} functions:")
for func in functions[:20]:
    print(f"  - {func}()")

# Look for dependency checks
print(f"\n\nDEPENDENCY PATTERNS:")
dep_patterns = [
    r'if\s*\([^)]*depend[^)]*\)',
    r'if\s*\([^)]*enable[^)]*\)',
    r'if\s*\([^)]*disable[^)]*\)',
    r'if\s*\([^)]*check[^)]*\)',
]

for pattern in dep_patterns:
    matches = re.findall(pattern, code, re.IGNORECASE)
    if matches:
        print(f"\nPattern: {pattern}")
        for match in matches[:3]:
            print(f"  {match}")
