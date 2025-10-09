"""Product Type Mapper

Maps series names to product types.
"""

from typing import Optional


# Series to Product Type mapping
# Valid values: See migration 48_expand_product_type_values.sql
SERIES_PRODUCT_TYPE_MAP = {
    # Konica Minolta
    'AccurioPress': 'production_printer',
    'Revoria': 'production_printer',
    'bizhub': 'laser_multifunction',
    'bizhub PRESS': 'production_printer',
    
    # HP - Laser (Toner)
    'LaserJet': 'laser_printer',
    'LaserJet Pro': 'laser_printer',
    'LaserJet Pro MFP': 'laser_multifunction',
    'LaserJet Enterprise': 'laser_printer',
    'LaserJet Enterprise MFP': 'laser_multifunction',
    'LaserJet Managed': 'laser_printer',
    'Color LaserJet': 'laser_printer',
    'Color LaserJet Pro': 'laser_printer',
    'Color LaserJet Pro MFP': 'laser_multifunction',
    'Color LaserJet Enterprise': 'laser_printer',
    'Laser MFP': 'laser_multifunction',
    
    # HP - Inkjet (Tinte)
    'DeskJet': 'inkjet_printer',
    'DeskJet Plus': 'inkjet_multifunction',
    'ENVY': 'inkjet_multifunction',
    'ENVY Inspire': 'inkjet_multifunction',
    'ENVY Photo': 'inkjet_multifunction',
    'Smart Tank': 'inkjet_printer',
    'Smart Tank Plus': 'inkjet_multifunction',
    'OfficeJet': 'inkjet_multifunction',
    'OfficeJet Pro': 'inkjet_multifunction',
    'PageWide': 'inkjet_multifunction',
    'PageWide Pro': 'inkjet_multifunction',
    'PageWide Enterprise': 'inkjet_multifunction',
    
    # HP - Production & Plotter
    'DesignJet': 'inkjet_plotter',
    'Latex': 'latex_plotter',
    'Indigo Digital Press': 'production_printer',
    'Scitex': 'production_printer',
    
    # Canon - MFP/Printer
    'imageRUNNER': 'laser_multifunction',
    'imageRUNNER ADVANCE': 'laser_multifunction',
    'imageRUNNER ADVANCE DX': 'laser_multifunction',
    'i-SENSYS': 'laser_printer',
    'i-SENSYS MF': 'laser_multifunction',
    
    # Canon - Production
    'imagePRESS': 'production_printer',
    'imagePRESS C': 'production_printer',
    'varioPRINT': 'production_printer',
    
    # Canon - Plotter
    'imagePROGRAF': 'inkjet_plotter',
    'imagePROGRAF PRO': 'inkjet_plotter',
    'imagePROGRAF TX': 'inkjet_plotter',
    'imagePROGRAF TM': 'inkjet_plotter',
    'imagePROGRAF TA': 'inkjet_plotter',
    'imagePROGRAF iPF': 'inkjet_plotter',
    
    # Xerox - Production
    'Iridesse Production Press': 'production_printer',
    'Color Press': 'production_printer',
    'Versant': 'production_printer',
    'iGen': 'production_printer',
    'PrimeLink': 'production_printer',
    
    # Xerox - MFP
    'AltaLink': 'laser_multifunction',
    'VersaLink': 'laser_multifunction',
    'WorkCentre': 'laser_multifunction',
    'ColorQube': 'solid_ink_multifunction',
    'DocuCentre': 'laser_multifunction',
    
    # Xerox - Printer
    'Phaser': 'laser_printer',
    'DocuPrint': 'laser_printer',
    
    # Xerox - Wide Format
    'Wide Format': 'inkjet_plotter',
    
    # Ricoh - Production
    'Pro C': 'production_printer',
    'Pro VC': 'production_printer',
    'Pro 8': 'production_printer',
    
    # Ricoh - MFP
    'IM C': 'laser_multifunction',
    'IM': 'laser_multifunction',
    'IM CW': 'inkjet_plotter',
    'MP C': 'laser_multifunction',
    'MP': 'laser_multifunction',
    'MP W': 'inkjet_plotter',
    'Aficio MP C': 'laser_multifunction',
    'Aficio MP': 'laser_multifunction',
    
    # Ricoh - Printer
    'SP C': 'laser_printer',
    'SP': 'laser_printer',
    'P C': 'laser_printer',
    'P': 'laser_printer',
    'Aficio SG': 'inkjet_printer',
    
    # Brother - Production
    'GTXpro': 'production_printer',
    'GTX': 'production_printer',
    
    # Brother - Specialty
    'PL Series': 'inkjet_plotter',
    'ScanNCut': 'accessory',
    
    # Brother - Inkjet MFP
    'MFC-J': 'inkjet_multifunction',
    'DCP-J': 'inkjet_multifunction',
    
    # Brother - Laser MFP
    'MFC-L': 'laser_multifunction',
    'DCP-L': 'laser_multifunction',
    
    # Brother - Printer
    'HL-L': 'laser_printer',
    
    # Brother - Fax/Mobile
    'IntelliFax': 'laser_multifunction',
    'PJ Series': 'inkjet_printer',
    
    # Lexmark - MFP (multifunction)
    'MX Series': 'laser_multifunction',
    'CX Series': 'laser_multifunction',
    'XC Series': 'laser_multifunction',
    'XM Series': 'laser_multifunction',
    'MB Series': 'laser_multifunction',
    'MC Series': 'laser_multifunction',
    
    # Lexmark - Printer
    'MS Series': 'laser_printer',
    'CS Series': 'laser_printer',
    'B Series': 'laser_printer',
    'C Series': 'laser_printer',
    
    # Lexmark - Production
    'Enterprise Production': 'production_printer',
    'Enterprise Color': 'laser_multifunction',
    
    # Lexmark - Legacy
    'Interpret S400 Series': 'inkjet_printer',
    'Plus Matrix Series': 'dot_matrix_printer',
    
    # Kyocera - Production
    'TASKalfa Pro': 'production_printer',
    
    # Kyocera - MFP
    'TASKalfa': 'laser_multifunction',
    'ECOSYS M': 'laser_multifunction',
    'ECOSYS MA': 'laser_multifunction',
    'FS-Series MFP': 'laser_multifunction',
    'KM-Series': 'laser_multifunction',
    
    # Kyocera - Printer
    'ECOSYS': 'laser_printer',
    'ECOSYS P': 'laser_printer',
    'ECOSYS PA': 'laser_printer',
    'FS-Series': 'laser_printer',
    'TC-Series': 'laser_printer',
    'F-Series': 'laser_printer',
    'DC-Series': 'laser_printer',
    'DP-Series': 'laser_printer',
    
    # UTAX (TA Triumph-Adler) - MFP
    'P-Series MFP': 'laser_multifunction',
    'CDC Series': 'laser_multifunction',
    '2506ci': 'laser_multifunction',
    '3206ci': 'laser_multifunction',
    '4006ci': 'laser_multifunction',
    '5006ci': 'laser_multifunction',
    '6006ci': 'laser_multifunction',
    '7006ci': 'laser_multifunction',
    '8006ci': 'laser_multifunction',
    
    # UTAX - Printer
    'P-Series': 'laser_printer',
    'LP-Series': 'laser_printer',
    'CDP Series': 'laser_printer',
    'CD Series': 'laser_printer',
    
    # Epson - Production
    'SureColor Production': 'production_printer',
    'SureColor F': 'production_printer',
    'Monna Lisa': 'production_printer',
    'SureLab': 'production_printer',
    'Stylus Pro': 'inkjet_plotter',
    
    # Epson - Professional
    'SureColor P': 'inkjet_plotter',
    
    # Epson - MFP
    'WorkForce Enterprise': 'inkjet_multifunction',
    'WorkForce Pro': 'inkjet_multifunction',
    'WorkForce': 'inkjet_multifunction',
    'EcoTank': 'inkjet_multifunction',
    'Expression Home': 'inkjet_multifunction',
    
    # Epson - Printer
    'Expression Photo': 'inkjet_printer',
    'Stylus Photo': 'inkjet_printer',
    'Stylus': 'inkjet_printer',
    
    # Epson - Legacy
    'MJ Series': 'dot_matrix_printer',
    'MX Series': 'inkjet_printer',
    'MP Series': 'inkjet_printer',
    'P Series': 'inkjet_printer',
    
    # OKI - Production
    'Pro9': 'production_printer',
    'Pro10': 'production_printer',
    
    # OKI - MFP
    'MC Series': 'laser_multifunction',
    'MB Series': 'laser_multifunction',
    'B Series MFP': 'laser_multifunction',
    'ES Series MFP': 'laser_multifunction',
    'CX Series': 'laser_multifunction',
    
    # OKI - Printer
    'C Series': 'laser_printer',
    'B Series': 'laser_printer',
    'ES Series': 'laser_printer',
    
    # Fujifilm - Production
    'Revoria Press': 'production_printer',
    'JetPress': 'production_printer',
    'ApeosPro': 'production_printer',
    
    # Fujifilm - MFP
    'ApeosPort-VII': 'laser_multifunction',
    'ApeosPort': 'laser_multifunction',
    'Apeos': 'laser_multifunction',
    'DocuCentre': 'laser_multifunction',
    
    # Fujifilm - Printer
    'ApeosPrint': 'laser_printer',
    'DocuPrint': 'laser_printer',
    
    # Fujifilm - Photo
    'INSTAX mini Link': 'dye_sublimation_printer',
    'INSTAX SQUARE Link': 'dye_sublimation_printer',
    'INSTAX Link Wide': 'dye_sublimation_printer',
    'INSTAX': 'dye_sublimation_printer',
    
    # Sharp - Production
    'BP Pro': 'production_printer',
    'MX Production': 'production_printer',
    
    # Sharp - MFP
    'BP Series': 'laser_multifunction',
    'MX Series': 'laser_multifunction',
    'MX-B': 'laser_multifunction',
    'MX-C': 'laser_multifunction',
    'AR Series': 'laser_multifunction',
    
    # Sharp - Printer
    'BP Printer': 'laser_printer',
    'MX-B Printer': 'laser_printer',
    'MX-C Printer': 'laser_printer',
    'AL Series': 'laser_printer',
    
    # Toshiba - Production
    'e-STUDIO Production': 'production_printer',
    
    # Toshiba - MFP
    'e-STUDIO': 'laser_multifunction',
    'e-STUDIO Hybrid': 'laser_multifunction',
    
    # Toshiba - Legacy
    'Pagelaser': 'laser_printer',
    'PAL Series': 'laser_printer',
    'Spot Series': 'laser_printer',
    'T Series': 'laser_printer',
    'TF Series': 'laser_printer',
    'TF-P Series': 'laser_printer',
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
        
        # bizhub PRESS/PRO = production_printer
        if 'PRESS' in series_name or 'PRO' in series_name:
            return 'production_printer'
        
        # Printer-only models (4020, 4050, 4750, C3300i, C4000i)
        if any(x in check_str for x in ['4020', '4050', '4750', 'C3300', 'C4000']):
            return 'laser_printer'
        
        # Everything else is MFP
        return 'laser_multifunction'
    
    # Direct match
    if series_name in SERIES_PRODUCT_TYPE_MAP:
        return SERIES_PRODUCT_TYPE_MAP[series_name]
    
    # Partial match (for variations)
    for key, value in SERIES_PRODUCT_TYPE_MAP.items():
        if key.lower() in series_lower or series_lower in key.lower():
            return value
    
    # Default fallback
    return 'multifunction'


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
