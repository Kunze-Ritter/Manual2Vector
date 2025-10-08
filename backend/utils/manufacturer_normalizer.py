"""Manufacturer Normalizer

Normalizes manufacturer names to handle variations and aliases.
"""

import re
from typing import Optional


# Manufacturer normalization map
# Key: canonical name (what we store in DB)
# Value: list of aliases/variations
MANUFACTURER_MAP = {
    'Hewlett Packard': [
        'hp', 'HP', 'HP Inc', 'HP Inc.', 'hp inc', 'hp inc.',
        'Hewlett Packard', 'Hewlett-Packard', 'hewlett packard',
        'hewlett-packard', 'HEWLETT PACKARD', 'HEWLETT-PACKARD',
        'H-P', 'H P', 'Hp'
    ],
    'Konica Minolta': [
        'konica minolta', 'Konica Minolta', 'KONICA MINOLTA',
        'konica', 'Konica', 'KONICA',
        'minolta', 'Minolta', 'MINOLTA',
        'km', 'KM', 'K-M', 'K M',
        'Konica-Minolta', 'konica-minolta'
    ],
    'Canon': [
        'canon', 'Canon', 'CANON',
        'Canon Inc', 'Canon Inc.', 'canon inc', 'canon inc.'
    ],
    'Ricoh': [
        'ricoh', 'Ricoh', 'RICOH',
        'Ricoh Company', 'ricoh company'
    ],
    'Xerox': [
        'xerox', 'Xerox', 'XEROX',
        'Xerox Corporation', 'xerox corporation'
    ],
    'Brother': [
        'brother', 'Brother', 'BROTHER',
        'Brother Industries', 'brother industries'
    ],
    'Lexmark': [
        'lexmark', 'Lexmark', 'LEXMARK',
        'Lexmark International', 'lexmark international'
    ],
    'Kyocera': [
        'kyocera', 'Kyocera', 'KYOCERA',
        'Kyocera Document Solutions', 'kyocera document solutions'
    ],
    'Sharp': [
        'sharp', 'Sharp', 'SHARP',
        'Sharp Corporation', 'sharp corporation'
    ],
    'Epson': [
        'epson', 'Epson', 'EPSON',
        'Seiko Epson', 'seiko epson', 'SEIKO EPSON'
    ],
    'Fujifilm': [
        'fujifilm', 'Fujifilm', 'FUJIFILM',
        'fuji', 'Fuji', 'FUJI',
        'Fuji Xerox', 'fuji xerox', 'FUJI XEROX'
    ],
    'Riso': [
        'riso', 'Riso', 'RISO',
        'Riso Kagaku', 'riso kagaku'
    ],
    'Toshiba': [
        'toshiba', 'Toshiba', 'TOSHIBA',
        'Toshiba TEC', 'toshiba tec', 'TOSHIBA TEC'
    ],
    'OKI': [
        'oki', 'Oki', 'OKI',
        'Oki Data', 'oki data', 'OKI DATA',
        'Okidata', 'okidata', 'OKIDATA'
    ],
    'Utax': [
        'utax', 'Utax', 'UTAX',
        'TA Triumph-Adler', 'ta triumph-adler'
    ]
}


def normalize_manufacturer(name: str) -> Optional[str]:
    """
    Normalize manufacturer name to canonical form
    
    Args:
        name: Manufacturer name (any variation)
        
    Returns:
        Canonical manufacturer name or None if not found
        
    Examples:
        normalize_manufacturer("hp inc") -> "HP"
        normalize_manufacturer("KM") -> "Konica Minolta"
        normalize_manufacturer("hewlett packard") -> "HP"
    """
    if not name:
        return None
    
    # Clean input
    name_clean = name.strip()
    
    # Try exact match first (case-insensitive)
    for canonical, aliases in MANUFACTURER_MAP.items():
        if name_clean.lower() in [alias.lower() for alias in aliases]:
            return canonical
    
    # Try fuzzy match (contains)
    name_lower = name_clean.lower()
    
    # Special cases for common patterns
    if 'hewlett' in name_lower or 'packard' in name_lower:
        return 'HP'
    
    if 'konica' in name_lower or 'minolta' in name_lower:
        return 'Konica Minolta'
    
    # Try partial match
    for canonical, aliases in MANUFACTURER_MAP.items():
        for alias in aliases:
            if alias.lower() in name_lower or name_lower in alias.lower():
                return canonical
    
    # No match found
    return None


def get_manufacturer_aliases(canonical_name: str) -> list:
    """
    Get all aliases for a canonical manufacturer name
    
    Args:
        canonical_name: Canonical manufacturer name
        
    Returns:
        List of aliases
    """
    return MANUFACTURER_MAP.get(canonical_name, [])


def is_manufacturer_alias(name: str, canonical_name: str) -> bool:
    """
    Check if name is an alias of canonical manufacturer
    
    Args:
        name: Name to check
        canonical_name: Canonical manufacturer name
        
    Returns:
        True if name is an alias
    """
    if not name or not canonical_name:
        return False
    
    aliases = MANUFACTURER_MAP.get(canonical_name, [])
    return name.lower() in [alias.lower() for alias in aliases]


def add_manufacturer_alias(canonical_name: str, alias: str):
    """
    Add a new alias to a manufacturer
    
    Args:
        canonical_name: Canonical manufacturer name
        alias: New alias to add
    """
    if canonical_name in MANUFACTURER_MAP:
        if alias not in MANUFACTURER_MAP[canonical_name]:
            MANUFACTURER_MAP[canonical_name].append(alias)


if __name__ == '__main__':
    # Test cases
    test_cases = [
        'HP Inc',
        'hp',
        'Hewlett Packard',
        'KM',
        'Konica',
        'Minolta',
        'konica minolta',
        'Canon Inc.',
        'Ricoh',
        'Brother Industries'
    ]
    
    print("Manufacturer Normalization Tests:")
    print("=" * 60)
    for test in test_cases:
        normalized = normalize_manufacturer(test)
        print(f"{test:30} -> {normalized}")
