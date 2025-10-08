"""Product Type Mapper

Maps series names to product types.
"""

from typing import Optional


# Series to Product Type mapping
SERIES_PRODUCT_TYPE_MAP = {
    # Konica Minolta
    'AccurioPress': 'Production Printing',
    'Revoria': 'Production Printing',
    'bizhub': 'Multifunktionsdrucker',
    'bizhub PRESS': 'Production Printing',
    
    # HP
    'LaserJet': 'Printer',
    'LaserJet Pro': 'Printer',
    'Color LaserJet': 'Printer',
    'OfficeJet': 'Multifunktionsdrucker',
    'OfficeJet Pro': 'Multifunktionsdrucker',
    'PageWide': 'Multifunktionsdrucker',
    'DesignJet': 'Plotter',
    'Latex': 'Plotter',
    
    # Canon
    'imageRUNNER': 'Multifunktionsdrucker',
    'imageRUNNER ADVANCE': 'Multifunktionsdrucker',
    'imagePRESS': 'Production Printing',
    'imagePROGRAF': 'Plotter',
    
    # Xerox
    'VersaLink': 'Multifunktionsdrucker',
    'AltaLink': 'Multifunktionsdrucker',
    'WorkCentre': 'Multifunktionsdrucker',
    'Phaser': 'Printer',
    'ColorQube': 'Printer',
    'Versant': 'Production Printing',
    'iGen': 'Production Printing',
    
    # Ricoh
    'Aficio': 'Multifunktionsdrucker',
    'MP': 'Multifunktionsdrucker',
    'Pro C': 'Production Printing',
    
    # Brother
    'MFC': 'Multifunktionsdrucker',
    'DCP': 'Multifunktionsdrucker',
    'HL': 'Printer',
    
    # Lexmark
    'MX': 'Multifunktionsdrucker',
    'CX': 'Multifunktionsdrucker',
    'MS': 'Printer',
    'CS': 'Printer',
    
    # Kyocera
    'TASKalfa': 'Multifunktionsdrucker',
    'ECOSYS': 'Printer',
}


def get_product_type(series_name: str, model_pattern: Optional[str] = None, model_number: Optional[str] = None) -> Optional[str]:
    """
    Get product type based on series name and model pattern
    
    Args:
        series_name: Series name (e.g., "LaserJet", "bizhub")
        model_pattern: Technical pattern (e.g., "C5xx", "M4xx")
        model_number: Full model number (e.g., "C558", "M479fdw")
        
    Returns:
        Product type or None
    """
    if not series_name:
        return None
    
    series_lower = series_name.lower()
    
    # Special handling for bizhub (depends on model)
    if 'bizhub' in series_lower:
        # Check model number or pattern for specific types
        check_str = (model_number or model_pattern or '').upper()
        
        # bizhub PRESS/PRO = Production Printing
        if 'PRESS' in series_name or 'PRO' in series_name:
            return 'Production Printing'
        
        # Printer-only models (4020, 4050, 4750, C3300i, C4000i)
        if any(x in check_str for x in ['4020', '4050', '4750', 'C3300', 'C4000']):
            return 'Printer'
        
        # Everything else is MFP
        return 'Multifunktionsdrucker'
    
    # Direct match
    if series_name in SERIES_PRODUCT_TYPE_MAP:
        return SERIES_PRODUCT_TYPE_MAP[series_name]
    
    # Partial match (for variations)
    for key, value in SERIES_PRODUCT_TYPE_MAP.items():
        if key.lower() in series_lower or series_lower in key.lower():
            return value
    
    # Default fallback
    return 'Multifunktionsdrucker'


if __name__ == '__main__':
    # Test
    test_cases = [
        'LaserJet',
        'bizhub',
        'AccurioPress',
        'DesignJet',
        'imageRUNNER ADVANCE',
        'Phaser'
    ]
    
    print("Product Type Mapping Tests:")
    print("=" * 60)
    for series in test_cases:
        product_type = get_product_type(series)
        print(f"{series:30} → {product_type}")
