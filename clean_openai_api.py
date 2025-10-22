"""Clean up openai_compatible_api.py - remove old progressive method"""
from pathlib import Path

api_file = Path('backend/api/openai_compatible_api.py')

with open(api_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the method
start_line = None
for i, line in enumerate(lines):
    if 'async def _process_query_progressive' in line:
        start_line = i
        break

if start_line is None:
    print("Method not found!")
    exit(1)

print(f"Found method at line {start_line + 1}")

# Find the end - look for next method or class-level code
end_line = None
for i in range(start_line + 1, len(lines)):
    # Check if this is a new method (def at same indentation level)
    if lines[i].strip() and not lines[i].startswith(' ' * 8) and lines[i].startswith(' ' * 4):
        if 'def ' in lines[i]:
            end_line = i
            break

if end_line is None:
    end_line = len(lines)

print(f"Method ends at line {end_line}")
print(f"Removing {end_line - start_line} lines")

# Keep only the first 6 lines of the method (the new clean version)
new_method = lines[start_line:start_line+6]

# Rebuild file
new_lines = lines[:start_line] + new_method + lines[end_line:]

with open(api_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"✅ Cleaned! Removed {len(lines) - len(new_lines)} lines")
print(f"Old: {len(lines)} lines, New: {len(new_lines)} lines")
