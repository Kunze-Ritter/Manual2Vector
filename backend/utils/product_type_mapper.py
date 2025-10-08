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
    
    # HP - Laser (Toner)
    'LaserJet': 'Laser Printer',
    'LaserJet Pro': 'Laser Printer',
    'LaserJet Enterprise': 'Laser Printer',
    'LaserJet Managed': 'Laser Printer',
    'Color LaserJet': 'Laser Printer',
    'Color LaserJet Pro': 'Laser Printer',
    'Color LaserJet Enterprise': 'Laser Printer',
    
    # HP - Inkjet (Tinte)
    'OfficeJet': 'Inkjet Multifunktionsdrucker',
    'OfficeJet Pro': 'Inkjet Multifunktionsdrucker',
    'PageWide': 'Inkjet Multifunktionsdrucker',
    'PageWide Pro': 'Inkjet Multifunktionsdrucker',
    'PageWide Enterprise': 'Inkjet Multifunktionsdrucker',
    
    # HP - Plotter
    'DesignJet': 'Plotter (Inkjet)',
    'Latex': 'Plotter (Latex)',
    'Scitex': 'Production Printing (Inkjet)',
    
    # Canon - MFP/Printer
    'imageRUNNER': 'Multifunktionsdrucker',
    'imageRUNNER ADVANCE': 'Multifunktionsdrucker',
    'imageRUNNER ADVANCE DX': 'Multifunktionsdrucker',
    'i-SENSYS': 'Laser Printer',
    'i-SENSYS MF': 'Multifunktionsdrucker',
    
    # Canon - Production
    'imagePRESS': 'Production Printing',
    'imagePRESS C': 'Production Printing',
    'varioPRINT': 'Production Printing',
    
    # Canon - Plotter
    'imagePROGRAF': 'Plotter (Inkjet)',
    'imagePROGRAF PRO': 'Plotter (Inkjet)',
    'imagePROGRAF TX': 'Plotter (Inkjet)',
    'imagePROGRAF TM': 'Plotter (Inkjet)',
    'imagePROGRAF TA': 'Plotter (Inkjet)',
    'imagePROGRAF iPF': 'Plotter (Inkjet)',
    
    # Xerox - MFP/Printer
    'VersaLink': 'Multifunktionsdrucker',
    'AltaLink': 'Multifunktionsdrucker',
    'WorkCentre': 'Multifunktionsdrucker',
    'Phaser': 'Laser Printer',
    'ColorQube': 'Solid Ink Printer',
    
    # Xerox - Production
    'Versant': 'Production Printing',
    'iGen': 'Production Printing',
    'PrimeLink': 'Production Printing',
    'Color C': 'Production Printing',
    
    # Ricoh - MFP/Printer
    'Aficio': 'Multifunktionsdrucker',
    'MP': 'Multifunktionsdrucker',
    'IM': 'Multifunktionsdrucker',
    'SP': 'Laser Printer',
    
    # Ricoh - Production
    'Pro C': 'Production Printing',
    'Pro 8': 'Production Printing',
    
    # Brother - Laser
    'MFC': 'Multifunktionsdrucker',
    'DCP': 'Multifunktionsdrucker',
    'HL': 'Laser Printer',
    
    # Brother - Inkjet
    'MFC-J': 'Inkjet Multifunktionsdrucker',
    'DCP-J': 'Inkjet Multifunktionsdrucker',
    
    # Lexmark - MFP (Multifunktionsdrucker)
    'MX': 'Multifunktionsdrucker',
    'CX': 'Multifunktionsdrucker',
    'XC': 'Multifunktionsdrucker',
    'XM': 'Multifunktionsdrucker',
    'MB': 'Multifunktionsdrucker',
    'MC': 'Multifunktionsdrucker',
    'M': 'Multifunktionsdrucker',
    'X': 'Multifunktionsdrucker',
    
    # Lexmark - Printer
    'MS': 'Laser Printer',
    'CS': 'Laser Printer',
    'B': 'Laser Printer',
    'C': 'Laser Printer',
    
    # Kyocera - MFP
    'TASKalfa': 'Multifunktionsdrucker',
    'TASKalfa Pro': 'Multifunktionsdrucker',
    'ECOSYS M': 'Multifunktionsdrucker',
    
    # Kyocera - Printer
    'ECOSYS': 'Laser Printer',
    'ECOSYS P': 'Laser Printer',
    'FS': 'Laser Printer',
    
    # Utax (TA Triumph-Adler) - MFP
    'Utax': 'Multifunktionsdrucker',
    '2506ci': 'Multifunktionsdrucker',
    '3206ci': 'Multifunktionsdrucker',
    '4006ci': 'Multifunktionsdrucker',
    '5006ci': 'Multifunktionsdrucker',
    '6006ci': 'Multifunktionsdrucker',
    '7006ci': 'Multifunktionsdrucker',
    '8006ci': 'Multifunktionsdrucker',
    
    # Utax - Printer
    'P-C': 'Laser Printer',
    'P-': 'Laser Printer',
    
    # Epson
    'WorkForce': 'Inkjet Multifunktionsdrucker',
    'WorkForce Pro': 'Inkjet Multifunktionsdrucker',
    'EcoTank': 'Inkjet Multifunktionsdrucker',
    'SureColor': 'Plotter (Inkjet)',
    
    # OKI
    'MC': 'Multifunktionsdrucker',
    'MPS': 'Multifunktionsdrucker',
    'C': 'Laser Printer',
    'B': 'Laser Printer',
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
