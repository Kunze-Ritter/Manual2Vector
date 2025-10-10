"""
OEM/Rebrand Manufacturer Mappings
==================================

Many printer manufacturers rebrand other manufacturers' products.
This causes issues with error code and parts detection because:
- The BRAND says "Konica Minolta"
- But the ERROR CODES are from "Brother"
- And the PARTS are from "Brother"

This module maps product series to their OEM engine manufacturer.

Usage:
    from backend.config.oem_mappings import get_oem_manufacturer
    
    # Product is branded as "Konica Minolta 5000i"
    oem = get_oem_manufacturer("Konica Minolta", "5000i")
    # Returns: "Brother" (for error codes and parts)
"""

from typing import Optional, Dict, List
import re


# OEM Mappings
# Format: (Brand Manufacturer, Series Pattern) -> OEM Engine Manufacturer
OEM_MAPPINGS = {
    # ===== KONICA MINOLTA REBRANDS =====
    
    # Konica Minolta 5000i/4000i series → Brother Engine
    ('Konica Minolta', r'[45]000i'): {
        'oem_manufacturer': 'Brother',
        'series_name': '5000i/4000i Series',
        'notes': 'Brother engine with Konica Minolta branding',
        'applies_to': ['error_codes', 'parts']
    },
    
    # ===== LEXMARK REBRANDS =====
    
    # Lexmark CS/CX 900 series → Konica Minolta Engine
    ('Lexmark', r'C[SX]9\d{2}'): {
        'oem_manufacturer': 'Konica Minolta',
        'series_name': 'CS/CX 900 Series',
        'notes': 'Konica Minolta bizhub engine',
        'applies_to': ['error_codes', 'parts']
    },
    
    # Lexmark CS/CX 800 series → Konica Minolta Engine
    ('Lexmark', r'C[SX]8\d{2}'): {
        'oem_manufacturer': 'Konica Minolta',
        'series_name': 'CS/CX 800 Series',
        'notes': 'Konica Minolta bizhub engine',
        'applies_to': ['error_codes', 'parts']
    },
    
    # ===== UTAX REBRANDS =====
    
    # UTAX → Kyocera (ALL products!)
    ('UTAX', r'.*'): {
        'oem_manufacturer': 'Kyocera',
        'series_name': 'All UTAX Products',
        'notes': 'UTAX is Kyocera rebrand for European market',
        'applies_to': ['error_codes', 'parts', 'accessories']
    },
    
    # Triumph-Adler → Kyocera (ALL products!)
    ('Triumph-Adler', r'.*'): {
        'oem_manufacturer': 'Kyocera',
        'series_name': 'All Triumph-Adler Products',
        'notes': 'Triumph-Adler is Kyocera rebrand',
        'applies_to': ['error_codes', 'parts', 'accessories']
    },
    
    # ===== XEROX REBRANDS =====
    
    # Xerox VersaLink C400/C405 → Lexmark Engine
    ('Xerox', r'VersaLink C40[05]'): {
        'oem_manufacturer': 'Lexmark',
        'series_name': 'VersaLink C400 Series',
        'notes': 'Lexmark CS/CX engine',
        'applies_to': ['error_codes', 'parts']
    },
    
    # Xerox WorkCentre 6515 → Lexmark Engine
    ('Xerox', r'WorkCentre 651[05]'): {
        'oem_manufacturer': 'Lexmark',
        'series_name': 'WorkCentre 6515 Series',
        'notes': 'Lexmark CS/CX engine',
        'applies_to': ['error_codes', 'parts']
    },
    
    # ===== RICOH REBRANDS =====
    
    # Ricoh → Some models use Konica Minolta engines
    # (Add specific models as discovered)
    
    # ===== SHARP REBRANDS =====
    
    # Sharp → Some models use Toshiba engines
    # (Add specific models as discovered)
}


def get_oem_manufacturer(
    brand_manufacturer: str,
    model_or_series: str,
    for_purpose: str = 'error_codes'
) -> Optional[str]:
    """
    Get the OEM engine manufacturer for a product
    
    Args:
        brand_manufacturer: The brand name (e.g., "Konica Minolta", "Lexmark")
        model_or_series: The model or series name (e.g., "5000i", "CS943")
        for_purpose: What you need the OEM for ('error_codes', 'parts', 'accessories')
        
    Returns:
        OEM manufacturer name if rebrand, None if original manufacturer
        
    Examples:
        >>> get_oem_manufacturer("Konica Minolta", "5000i", "error_codes")
        "Brother"
        
        >>> get_oem_manufacturer("Lexmark", "CS943", "error_codes")
        "Konica Minolta"
        
        >>> get_oem_manufacturer("HP", "M455", "error_codes")
        None  # HP is original manufacturer
    """
    if not brand_manufacturer or not model_or_series:
        return None
    
    # Check each OEM mapping
    for (brand, pattern), mapping in OEM_MAPPINGS.items():
        # Check if brand matches
        if brand.lower() != brand_manufacturer.lower():
            continue
        
        # Check if model/series matches pattern
        if re.search(pattern, model_or_series, re.IGNORECASE):
            # Check if this mapping applies to the requested purpose
            if for_purpose in mapping['applies_to']:
                return mapping['oem_manufacturer']
    
    # No OEM mapping found - use original manufacturer
    return None


def get_effective_manufacturer(
    brand_manufacturer: str,
    model_or_series: str,
    for_purpose: str = 'error_codes'
) -> str:
    """
    Get the effective manufacturer to use for detection
    
    This returns either the OEM manufacturer (if rebrand) or the original manufacturer.
    
    Args:
        brand_manufacturer: The brand name
        model_or_series: The model or series name
        for_purpose: What you need the manufacturer for
        
    Returns:
        The manufacturer to use for detection (OEM or original)
        
    Examples:
        >>> get_effective_manufacturer("Konica Minolta", "5000i", "error_codes")
        "Brother"  # Use Brother patterns
        
        >>> get_effective_manufacturer("HP", "M455", "error_codes")
        "HP"  # Use HP patterns
    """
    oem = get_oem_manufacturer(brand_manufacturer, model_or_series, for_purpose)
    return oem if oem else brand_manufacturer


def get_oem_info(brand_manufacturer: str, model_or_series: str) -> Optional[Dict]:
    """
    Get full OEM information for a product
    
    Args:
        brand_manufacturer: The brand name
        model_or_series: The model or series name
        
    Returns:
        Dictionary with OEM info, or None if not a rebrand
        
    Example:
        >>> get_oem_info("Konica Minolta", "5000i")
        {
            'oem_manufacturer': 'Brother',
            'series_name': '5000i/4000i Series',
            'notes': 'Brother engine with Konica Minolta branding',
            'applies_to': ['error_codes', 'parts']
        }
    """
    if not brand_manufacturer or not model_or_series:
        return None
    
    for (brand, pattern), mapping in OEM_MAPPINGS.items():
        if brand.lower() == brand_manufacturer.lower():
            if re.search(pattern, model_or_series, re.IGNORECASE):
                return mapping
    
    return None


def list_all_oem_mappings() -> List[Dict]:
    """
    List all OEM mappings for documentation/debugging
    
    Returns:
        List of all OEM mappings with brand and pattern info
    """
    mappings = []
    for (brand, pattern), mapping in OEM_MAPPINGS.items():
        mappings.append({
            'brand': brand,
            'pattern': pattern,
            **mapping
        })
    return mappings


def is_rebrand(brand_manufacturer: str, model_or_series: str) -> bool:
    """
    Check if a product is a rebrand
    
    Args:
        brand_manufacturer: The brand name
        model_or_series: The model or series name
        
    Returns:
        True if rebrand, False if original
    """
    return get_oem_manufacturer(brand_manufacturer, model_or_series) is not None


# Example usage and testing
if __name__ == '__main__':
    print("=" * 80)
    print("OEM Manufacturer Mappings")
    print("=" * 80)
    
    test_cases = [
        ("Konica Minolta", "5000i", "error_codes"),
        ("Konica Minolta", "4000i", "error_codes"),
        ("Lexmark", "CS943", "error_codes"),
        ("Lexmark", "CX943", "parts"),
        ("UTAX", "P-4020", "error_codes"),
        ("HP", "M455", "error_codes"),
        ("Xerox", "VersaLink C405", "error_codes"),
    ]
    
    print("\nTest Cases:")
    print("-" * 80)
    for brand, model, purpose in test_cases:
        oem = get_oem_manufacturer(brand, model, purpose)
        effective = get_effective_manufacturer(brand, model, purpose)
        is_rb = is_rebrand(brand, model)
        
        print(f"\n{brand} {model} (for {purpose}):")
        print(f"  OEM: {oem if oem else 'None (original)'}")
        print(f"  Effective Manufacturer: {effective}")
        print(f"  Is Rebrand: {is_rb}")
        
        if is_rb:
            info = get_oem_info(brand, model)
            print(f"  Series: {info['series_name']}")
            print(f"  Notes: {info['notes']}")
    
    print("\n" + "=" * 80)
    print("All OEM Mappings:")
    print("=" * 80)
    for mapping in list_all_oem_mappings():
        print(f"\n{mapping['brand']} (pattern: {mapping['pattern']})")
        print(f"  → {mapping['oem_manufacturer']}")
        print(f"  Series: {mapping['series_name']}")
        print(f"  Applies to: {', '.join(mapping['applies_to'])}")
