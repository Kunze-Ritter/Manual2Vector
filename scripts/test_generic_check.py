desc = 'Scanner Failure'

generic_phrases = [
    'refer to manual',
    'see documentation',
    'contact support',
    'error code',
    'see page',
    'refer to page',
    'table',
    'figure'
]

desc_lower = desc.lower()

print(f'Description: "{desc}"')
print(f'Length: {len(desc)}')
print(f'Is short (<50): {len(desc) < 50}')
print()

for phrase in generic_phrases:
    contains = phrase in desc_lower
    print(f'  Contains "{phrase}": {contains}')

# The actual check
is_generic = False
if len(desc) < 50:
    for phrase in generic_phrases:
        if phrase in desc_lower:
            is_generic = True
            break

print(f'\nResult: is_generic = {is_generic}')
