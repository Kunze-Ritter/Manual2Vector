"""Product Series Detection Module

Detects product series from model numbers and names.
"""

import re
from typing import Optional, Dict, Tuple


def detect_series(model_number: str, manufacturer_name: str) -> Optional[Dict]:
    """
    Detect product series from model number
    
    Args:
        model_number: Product model number (e.g., "M479fdw", "X580", "C454e")
        manufacturer_name: Manufacturer name
        
    Returns:
        Dict with series_name, series_code, or None
    """
    if not model_number:
        return None
    
    manufacturer_lower = manufacturer_name.lower()
    
    # HP Series Detection
    if 'hp' in manufacturer_lower:
        return _detect_hp_series(model_number)
    
    # Canon Series Detection
    elif 'canon' in manufacturer_lower:
        return _detect_canon_series(model_number)
    
    # Konica Minolta Series Detection
    elif 'konica' in manufacturer_lower or 'minolta' in manufacturer_lower:
        return _detect_konica_series(model_number)
    
    # Ricoh Series Detection
    elif 'ricoh' in manufacturer_lower:
        return _detect_ricoh_series(model_number)
    
    # Xerox Series Detection
    elif 'xerox' in manufacturer_lower:
        return _detect_xerox_series(model_number)
    
    # Brother Series Detection
    elif 'brother' in manufacturer_lower:
        return _detect_brother_series(model_number)
    
    # Lexmark Series Detection
    elif 'lexmark' in manufacturer_lower:
        return _detect_lexmark_series(model_number)
    
    # Kyocera Series Detection
    elif 'kyocera' in manufacturer_lower:
        return _detect_kyocera_series(model_number)
    
    # Generic fallback
    return _detect_generic_series(model_number)


def _detect_hp_series(model_number: str) -> Optional[Dict]:
    """Detect HP series"""
    model = model_number.upper()
    
    # LaserJet M series (M479, M454, M428, etc.)
    match = re.match(r'M(\d)(\d{2})', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'LaserJet M{series_digit}00 Series',
            'series_code': f'M{series_digit}XX',
            'series_description': f'HP LaserJet M{series_digit}00 series multifunction printers'
        }
    
    # LaserJet Pro M series (M15, M28, M29, etc.)
    match = re.match(r'M(\d{2})', model)
    if match:
        return {
            'series_name': f'LaserJet Pro M{match.group(1)} Series',
            'series_code': f'M{match.group(1)}',
            'series_description': f'HP LaserJet Pro M{match.group(1)} series'
        }
    
    # OfficeJet Pro X series (X580, X585, etc.)
    match = re.match(r'X(\d)(\d{2})', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'OfficeJet Pro X{series_digit}00 Series',
            'series_code': f'X{series_digit}XX',
            'series_description': f'HP OfficeJet Pro X{series_digit}00 series'
        }
    
    # PageWide series (P77960, P55250, etc.)
    match = re.match(r'P(\d)(\d{4})', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'PageWide P{series_digit}xxxx Series',
            'series_code': f'P{series_digit}XXXX',
            'series_description': f'HP PageWide P{series_digit} series'
        }
    
    # Color LaserJet series (CP5225, CP4525, etc.)
    match = re.match(r'CP(\d{2})', model)
    if match:
        return {
            'series_name': f'Color LaserJet CP{match.group(1)}xx Series',
            'series_code': f'CP{match.group(1)}XX',
            'series_description': f'HP Color LaserJet CP{match.group(1)} series'
        }
    
    return None


def _detect_canon_series(model_number: str) -> Optional[Dict]:
    """Detect Canon series"""
    model = model_number.upper()
    
    # imageRUNNER ADVANCE C series (C5560i, C5550i, etc.)
    match = re.match(r'C(\d{2})\d{2}', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'imageRUNNER ADVANCE C{series_digit}xx Series',
            'series_code': f'C{series_digit}XX',
            'series_description': f'Canon imageRUNNER ADVANCE C{series_digit} series'
        }
    
    # imageRUNNER series (iR2530, iR2545, etc.)
    match = re.match(r'(?:IR)?(\d{2})\d{2}', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'imageRUNNER {series_digit}xx Series',
            'series_code': f'{series_digit}XX',
            'series_description': f'Canon imageRUNNER {series_digit} series'
        }
    
    return None


def _detect_konica_series(model_number: str) -> Optional[Dict]:
    """Detect Konica Minolta series"""
    model = model_number.upper()
    
    # bizhub C series (C454e, C554e, C654e, etc.)
    match = re.match(r'C(\d)(\d{2})', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'bizhub C{series_digit}xx Series',
            'series_code': f'C{series_digit}XX',
            'series_description': f'Konica Minolta bizhub C{series_digit} series color MFPs'
        }
    
    # bizhub series (454e, 554e, 654e, etc.)
    match = re.match(r'(\d)(\d{2})', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'bizhub {series_digit}xx Series',
            'series_code': f'{series_digit}XX',
            'series_description': f'Konica Minolta bizhub {series_digit} series monochrome MFPs'
        }
    
    return None


def _detect_ricoh_series(model_number: str) -> Optional[Dict]:
    """Detect Ricoh series"""
    model = model_number.upper()
    
    # MP C series (MP C2004, MP C2504, etc.)
    match = re.match(r'MP\s*C(\d{2})\d{2}', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'MP C{series_digit}xx Series',
            'series_code': f'MPC{series_digit}XX',
            'series_description': f'Ricoh MP C{series_digit} series color MFPs'
        }
    
    # MP series (MP 2555, MP 3055, etc.)
    match = re.match(r'MP\s*(\d{2})\d{2}', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'MP {series_digit}xx Series',
            'series_code': f'MP{series_digit}XX',
            'series_description': f'Ricoh MP {series_digit} series monochrome MFPs'
        }
    
    return None


def _detect_xerox_series(model_number: str) -> Optional[Dict]:
    """Detect Xerox series"""
    model = model_number.upper()
    
    # VersaLink C series (C7020, C7025, C7030, etc.)
    match = re.match(r'C(\d{2})\d{2}', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'VersaLink C{series_digit}xx Series',
            'series_code': f'C{series_digit}XX',
            'series_description': f'Xerox VersaLink C{series_digit} series color MFPs'
        }
    
    # WorkCentre series (WC7835, WC7845, etc.)
    match = re.match(r'(?:WC)?(\d{2})\d{2}', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'WorkCentre {series_digit}xx Series',
            'series_code': f'WC{series_digit}XX',
            'series_description': f'Xerox WorkCentre {series_digit} series'
        }
    
    return None


def _detect_brother_series(model_number: str) -> Optional[Dict]:
    """Detect Brother series"""
    model = model_number.upper()
    
    # MFC-L series (MFC-L2750DW, MFC-L2710DW, etc.)
    match = re.match(r'MFC-L(\d{2})\d{2}', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'MFC-L{series_digit}xx Series',
            'series_code': f'MFCL{series_digit}XX',
            'series_description': f'Brother MFC-L{series_digit} series laser MFPs'
        }
    
    # HL-L series (HL-L2350DW, HL-L2370DW, etc.)
    match = re.match(r'HL-L(\d{2})\d{2}', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'HL-L{series_digit}xx Series',
            'series_code': f'HLL{series_digit}XX',
            'series_description': f'Brother HL-L{series_digit} series laser printers'
        }
    
    return None


def _detect_lexmark_series(model_number: str) -> Optional[Dict]:
    """Detect Lexmark series"""
    model = model_number.upper()
    
    # CX series (CX421, CX522, CX622, etc.)
    match = re.match(r'CX(\d)(\d{2})', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'CX{series_digit}xx Series',
            'series_code': f'CX{series_digit}XX',
            'series_description': f'Lexmark CX{series_digit} series color MFPs'
        }
    
    # MX series (MX421, MX521, MX622, etc.)
    match = re.match(r'MX(\d)(\d{2})', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'MX{series_digit}xx Series',
            'series_code': f'MX{series_digit}XX',
            'series_description': f'Lexmark MX{series_digit} series monochrome MFPs'
        }
    
    return None


def _detect_kyocera_series(model_number: str) -> Optional[Dict]:
    """Detect Kyocera series"""
    model = model_number.upper()
    
    # ECOSYS M series (M2040dn, M2540dn, M2640idw, etc.)
    match = re.match(r'M(\d{2})\d{2}', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'ECOSYS M{series_digit}xx Series',
            'series_code': f'M{series_digit}XX',
            'series_description': f'Kyocera ECOSYS M{series_digit} series MFPs'
        }
    
    # TASKalfa series (TASKalfa 2552ci, TASKalfa 3252ci, etc.)
    match = re.match(r'(?:TASKALFA\s*)?(\d{2})\d{2}', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'TASKalfa {series_digit}xx Series',
            'series_code': f'TA{series_digit}XX',
            'series_description': f'Kyocera TASKalfa {series_digit} series'
        }
    
    return None


def _detect_generic_series(model_number: str) -> Optional[Dict]:
    """Generic series detection fallback"""
    model = model_number.upper()
    
    # Try to extract first 2-3 digits/letters
    match = re.match(r'([A-Z]{0,2}\d{1,2})', model)
    if match:
        series_code = match.group(1)
        return {
            'series_name': f'{series_code}xx Series',
            'series_code': f'{series_code}XX',
            'series_description': f'{series_code} series products'
        }
    
    return None


if __name__ == '__main__':
    # Test
    test_cases = [
        ('M479fdw', 'HP'),
        ('X580', 'HP'),
        ('C454e', 'Konica Minolta'),
        ('MP C2004', 'Ricoh'),
        ('MFC-L2750DW', 'Brother'),
    ]
    
    for model, mfr in test_cases:
        result = detect_series(model, mfr)
        print(f"{mfr} {model}: {result}")
