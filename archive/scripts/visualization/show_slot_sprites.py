"""
Show which PDFs contain slot sprites (WT-511_1, RU-510_1, etc.)
"""
import json

with open('foliant_all_pdfs_analysis.json', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("SLOT SPRITES FOUND IN PDFs")
print("=" * 80)

# Find WT-511 slots
print("\n🔍 WT-511 (Working Table) Slots:")
print("-" * 80)
for result in data['pdf_results']:
    wt_slots = [s for s in result['sprites'] if 'WT-511' in s]
    if wt_slots:
        print(f"\n📄 {result['pdf']}")
        print(f"   Found: {', '.join(sorted(wt_slots))}")

# Find RU-510 slots
print("\n\n🔍 RU-510 (Relay Unit) Slots:")
print("-" * 80)
for result in data['pdf_results']:
    ru_slots = [s for s in result['sprites'] if 'RU-510' in s]
    if ru_slots:
        print(f"\n📄 {result['pdf']}")
        print(f"   Found: {', '.join(sorted(ru_slots))}")

# Find RU-518 slots
print("\n\n🔍 RU-518 (Relay Unit) Slots:")
print("-" * 80)
for result in data['pdf_results']:
    ru_slots = [s for s in result['sprites'] if 'RU-518' in s]
    if ru_slots:
        print(f"\n📄 {result['pdf']}")
        print(f"   Found: {', '.join(sorted(ru_slots))}")

# Find ALL slot patterns (_1, _2, etc.)
print("\n\n🔍 ALL SLOT PATTERNS:")
print("-" * 80)

slot_patterns = {}
for result in data['pdf_results']:
    for sprite in result['sprites']:
        if '_' in sprite and sprite[-1].isdigit():
            base = sprite.rsplit('_', 1)[0]
            if base not in slot_patterns:
                slot_patterns[base] = set()
            slot_patterns[base].add(sprite)

for base, slots in sorted(slot_patterns.items()):
    if len(slots) > 1:
        print(f"\n  {base}:")
        for slot in sorted(slots):
            print(f"    - {slot}")

print("\n\n" + "=" * 80)
print("EXPLANATION")
print("=" * 80)
print("""
Diese Sprite-Namen kommen DIREKT aus den PDF-Formularen!

Jedes Sprite repräsentiert ein klickbares Element im PDF.
Wenn ein Accessory in mehreren Positionen installiert werden kann,
gibt es mehrere Sprites mit _1, _2, _3, etc.

Beispiel:
  WT-511_1 = Working Table in Position 1
  WT-511_2 = Working Table in Position 2
  ...
  WT-511_7 = Working Table in Position 7

Das bedeutet: Der WT-511 kann in 7 verschiedenen Positionen
installiert werden (wahrscheinlich verschiedene Höhen/Konfigurationen).

Das ist NICHT unser Fehler - das ist wie Konica Minolta es designed hat!
""")
