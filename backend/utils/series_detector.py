"""Product Series Detection Module

Detects product series from model numbers and names.
"""

import re
from typing import Optional, Dict, Tuple


def _calculate_confidence(series_data: Dict, context: str) -> float:
    """
    Calculate confidence score based on context
    
    Args:
        series_data: Detected series information
        context: Text context (e.g., document chunk)
        
    Returns:
        Confidence score 0.0-1.0
    """
    if not context:
        return 0.5  # Default confidence without context
    
    context_lower = context.lower()
    series_name = series_data.get('series_name', '').lower()
    
    confidence = 0.5  # Base confidence
    
    # Check if series name appears in context
    if series_name in context_lower:
        confidence += 0.3
    
    # Check for partial matches (e.g., "accurio" for "AccurioPress")
    series_keywords = series_name.split()
    for keyword in series_keywords:
        if len(keyword) > 3 and keyword in context_lower:
            confidence += 0.1
    
    # Boost confidence for specific series markers
    series_markers = {
        'laserjet': ['laserjet', 'laser jet'],
        'officejet': ['officejet', 'office jet'],
        'pagewide': ['pagewide', 'page wide'],
        'accuriopress': ['accuriopress', 'accurio press'],
        'accurioprint': ['accurioprint', 'accurio print'],
        'bizhub': ['bizhub', 'biz hub'],
        'imagerunner': ['imagerunner', 'image runner'],
        'versalink': ['versalink', 'versa link'],
        'workcentre': ['workcentre', 'work centre', 'workcentre'],
    }
    
    for series_key, markers in series_markers.items():
        if series_key in series_name.replace(' ', ''):
            for marker in markers:
                if marker in context_lower:
                    confidence += 0.2
                    break
    
    # Cap at 1.0
    return min(confidence, 1.0)


def detect_series(model_number: str, manufacturer_name: str, context: str = None) -> Optional[Dict]:
    """
    Detect product series from model number with optional context validation
    
    Args:
        model_number: Product model number (e.g., "M479fdw", "X580", "C454e")
        manufacturer_name: Manufacturer name
        context: Optional text context to validate series name (e.g., document chunk)
        
    Returns:
        Dict with series_name, series_code, confidence, or None
    """
    if not model_number:
        return None
    
    # Skip very short model numbers without context validation
    if len(model_number) < 3 and not context:
        return None
    
    manufacturer_lower = manufacturer_name.lower()
    
    # HP Series Detection
    if 'hp' in manufacturer_lower:
        result = _detect_hp_series(model_number)
        if result and context:
            result['confidence'] = _calculate_confidence(result, context)
        return result
    
    # Canon Series Detection
    elif 'canon' in manufacturer_lower:
        result = _detect_canon_series(model_number)
        if result and context:
            result['confidence'] = _calculate_confidence(result, context)
        return result
    
    # Konica Minolta Series Detection
    elif 'konica' in manufacturer_lower or 'minolta' in manufacturer_lower:
        result = _detect_konica_series(model_number)
        if result:
            if context:
                result['confidence'] = _calculate_confidence(result, context)
                # Reject low confidence matches for short model numbers or context-required patterns
                if (len(model_number) <= 3 or result.get('requires_context', False)) and result.get('confidence', 0) < 0.7:
                    return None
            elif result.get('requires_context', False):
                # Pattern requires context but none provided - reject
                return None
        return result
    
    # Ricoh Series Detection
    elif 'ricoh' in manufacturer_lower:
        result = _detect_ricoh_series(model_number)
        if result and context:
            result['confidence'] = _calculate_confidence(result, context)
        return result
    
    # Xerox Series Detection
    elif 'xerox' in manufacturer_lower:
        result = _detect_xerox_series(model_number)
        if result and context:
            result['confidence'] = _calculate_confidence(result, context)
        return result
    
    # Brother Series Detection
    elif 'brother' in manufacturer_lower:
        result = _detect_brother_series(model_number)
        if result and context:
            result['confidence'] = _calculate_confidence(result, context)
        return result
    
    # Lexmark Series Detection
    elif 'lexmark' in manufacturer_lower:
        result = _detect_lexmark_series(model_number)
        if result and context:
            result['confidence'] = _calculate_confidence(result, context)
        return result
    
    # Kyocera Series Detection
    elif 'kyocera' in manufacturer_lower:
        result = _detect_kyocera_series(model_number)
        if result and context:
            result['confidence'] = _calculate_confidence(result, context)
        return result
    
    # Generic fallback
    result = _detect_generic_series(model_number)
    if result and context:
        result['confidence'] = _calculate_confidence(result, context)
    return result


def _detect_hp_series(model_number: str) -> Optional[Dict]:
    """Detect HP series - Returns marketing name + technical pattern"""
    model = model_number.upper()
    
    # LaserJet M series (M479, M454, M428, etc.)
    match = re.match(r'M(\d)(\d{2})', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'LaserJet',  # Marketing name
            'model_pattern': f'M{series_digit}xx',  # Technical pattern
            'series_description': f'HP LaserJet M{series_digit}00 series multifunction printers'
        }
    
    # LaserJet Pro M series (M15, M28, M29, etc.)
    match = re.match(r'M(\d{2})', model)
    if match:
        return {
            'series_name': 'LaserJet Pro',  # Marketing name
            'model_pattern': f'M{match.group(1)}',  # Technical pattern
            'series_description': f'HP LaserJet Pro M{match.group(1)} series'
        }
    
    # LaserJet E series (E50045, E50145, E52545, etc.)
    match = re.match(r'E(\d)(\d{2})', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'LaserJet',  # Marketing name
            'model_pattern': f'E{series_digit}xxxx',  # Technical pattern
            'series_description': f'HP LaserJet E{series_digit}0000 series'
        }
    
    # OfficeJet Pro X series (X580, X585, etc.)
    match = re.match(r'X(\d)(\d{2})', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'OfficeJet Pro',  # Marketing name
            'model_pattern': f'X{series_digit}xx',  # Technical pattern
            'series_description': f'HP OfficeJet Pro X{series_digit}00 series'
        }
    
    # PageWide series (P77960, P55250, etc.)
    match = re.match(r'P(\d)(\d{4})', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'PageWide',  # Marketing name
            'model_pattern': f'P{series_digit}xxxx',  # Technical pattern
            'series_code': f'P{series_digit}XXXX',
            'series_description': f'HP PageWide P{series_digit} series'
        }
    
    # Color LaserJet series (CP5225, CP4525, etc.)
    match = re.match(r'CP(\d{2})', model)
    if match:
        return {
            'series_name': 'Color LaserJet',  # Marketing name
            'model_pattern': f'CP{match.group(1)}xx',  # Technical pattern
            'series_description': f'HP Color LaserJet CP{match.group(1)} series'
        }
    
    return None


def _detect_canon_series(model_number: str) -> Optional[Dict]:
    """Detect Canon series - Returns marketing name + technical pattern"""
    model = model_number.upper()
    
    # imageRUNNER ADVANCE C series (C5560i, C5550i, etc.)
    match = re.match(r'C(\d{2})\d{2}', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'imageRUNNER ADVANCE',  # Marketing name
            'model_pattern': f'C{series_digit}xx',  # Technical pattern
            'series_description': f'Canon imageRUNNER ADVANCE C{series_digit} series'
        }
    
    # imageRUNNER series (iR2530, iR2545, etc.)
    match = re.match(r'(?:IR)?(\d{2})\d{2}', model)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'imageRUNNER',  # Marketing name
            'model_pattern': f'{series_digit}xx',  # Technical pattern
            'series_description': f'Canon imageRUNNER {series_digit} series'
        }
    
    return None


def _detect_konica_series(model_number: str) -> Optional[Dict]:
    """Detect Konica Minolta series - Returns marketing name + technical pattern"""
    model = model_number.upper().strip()
    
    # Remove common suffixes for pattern matching
    model_clean = re.sub(r'(?:SERIES|MFP)$', '', model).strip()
    
    # ===== PRIORITY 1: BIG Kiss (Special naming) =====
    if 'BIG' in model and 'KISS' in model:
        return {
            'series_name': 'BIG Kiss',
            'model_pattern': 'BIG Kiss',
            'series_description': 'Konica Minolta BIG Kiss special series'
        }
    
    # ===== PRIORITY 2: AccurioPrint (Production) =====
    # MUST CHECK BEFORE AccurioPress to avoid false matches!
    
    # C659, C759 (3 digits)
    if re.match(r'^C[67]59$', model_clean):
        return {
            'series_name': 'AccurioPrint',
            'model_pattern': 'Cx59',
            'series_description': 'Konica Minolta AccurioPrint production color printers'
        }
    
    # C2060, C2070, C4065 (specific 4-digit models)
    if re.match(r'^C(2060|2070|4065)[LP]?$', model_clean):
        return {
            'series_name': 'AccurioPrint',
            'model_pattern': 'Cxxxx',
            'series_description': 'Konica Minolta AccurioPrint production color printers'
        }
    
    # ===== PRIORITY 3: AccurioPress (High-end production) =====
    # C + 4-5 digits (C1060, C3070, C3080, C4070, C4080, C6085, C6100, C7090, C7100, C12000, C14000, C16000)
    # Excludes C2060, C2070, C4065 which are AccurioPrint
    if re.match(r'^C(1[0246][0-9]{2,3}|3[0-9]{3}|4[0-9]{3}|6[01][0-9]{2}|70[79]0|71[0]0)[LNPX]?$', model_clean):
        # Double-check it's not an AccurioPrint model
        if not re.match(r'^C(2060|2070|4065)[LP]?$', model_clean):
            return {
                'series_name': 'AccurioPress',
                'model_pattern': 'Cxxxx',
                'series_description': 'Konica Minolta AccurioPress high-end production color printers'
            }
    
    # 4 digits without C (6100, 6120, 6136, 6136P)
    if re.match(r'^6[01][0-9]{2}P?$', model_clean):
        return {
            'series_name': 'AccurioPress',
            'model_pattern': '6xxx',
            'series_description': 'Konica Minolta AccurioPress high-end production printers'
        }
    
    # ===== PRIORITY 4: bizhub Press (Production) =====
    # C + 4 digits (C1000, C1060, C1070, C1085, C1100, C2060, C2070, C3070, C3080, C6000)
    # Note: Overlaps with AccurioPress/AccurioPrint, so comes after
    if re.match(r'^C(1[0-9]{3}|[236][0-9]{3})[DLPX]{0,2}$', model_clean):
        return {
            'series_name': 'bizhub Press',
            'model_pattern': 'Cxxxx',
            'series_description': 'Konica Minolta bizhub Press production color printers'
        }
    
    # 4 digits (1052, 1200, 1250, 2250)
    if re.match(r'^(1[02][0-9]{2}|2250)[EP]?$', model_clean):
        return {
            'series_name': 'bizhub Press',
            'model_pattern': 'xxxx',
            'series_description': 'Konica Minolta bizhub Press production printers'
        }
    
    # ===== PRIORITY 5: bizhub (Office/MFP) =====
    # C + 3 digits (C224e, C284e, C364e, C454e, C554e, C654e, C754e, C858e, C958)
    match = re.match(r'^C([2-9])(\d{2})([EI]|PS)?$', model_clean)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'bizhub',
            'model_pattern': f'C{series_digit}xx',
            'series_description': f'Konica Minolta bizhub C{series_digit}xx series color MFPs'
        }
    
    # 3-4 digits without C (160, 185, 195, 200, 223, 227, 250, 266, 282, 287, 306, 308, 350, 360, 420, 454e, 554e, 654e, 754e, 920, 950i, 958)
    match = re.match(r'^([1-9])(\d{2,3})([EFIPX]|RM|MFP)?$', model_clean)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'bizhub',
            'model_pattern': f'{series_digit}xxx',
            'series_description': f'Konica Minolta bizhub {series_digit}xxx series MFPs'
        }
    
    # 2 digits (20, 25, 36, 40, 42, 43)
    # NOTE: These are very short and prone to false positives!
    # Only match if there's a suffix (P, E, PX) to increase specificity
    match = re.match(r'^([2-4][0-9])([EP]|PX)$', model_clean)
    if match:
        return {
            'series_name': 'bizhub',
            'model_pattern': match.group(1),
            'series_description': f'Konica Minolta bizhub {match.group(1)} series compact MFPs',
            'requires_context': True  # Flag that this needs context validation
        }
    
    # Special patterns: 3100P, 3300P, 3301P, 3320, 3602P, 3622MFP, 4000i, 4020, 4050, 4400, 4402P, 4422MFP, 4700i, 4750, 5000i, 5020i
    match = re.match(r'^([3-5])[0-9]{3}([IP]|MFP)?$', model_clean)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'bizhub',
            'model_pattern': f'{series_digit}xxx',
            'series_description': f'Konica Minolta bizhub {series_digit}xxx series'
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
    """Detect Lexmark series - Returns marketing name + technical pattern"""
    model = model_number.upper().strip()
    
    # Remove common suffixes for pattern matching
    model_clean = re.sub(r'(?:SERIES)$', '', model).strip()
    
    # ===== PRIORITY 1: Enterprise & Production (9xxx, 8xxx) =====
    # 9xxx = A3 Enterprise Production (e.g., 9300)
    if re.match(r'^9\d{3}$', model_clean):
        return {
            'series_name': 'Enterprise Production',
            'model_pattern': '9xxx',
            'series_description': 'Lexmark 9xxx series A3 Enterprise Production printers/MFPs'
        }
    
    # 8xxx = A4 Enterprise Color MFP (e.g., 8300)
    if re.match(r'^8\d{3}$', model_clean):
        return {
            'series_name': 'Enterprise Color',
            'model_pattern': '8xxx',
            'series_description': 'Lexmark 8xxx series A4 Enterprise Color MFPs'
        }
    
    # ===== PRIORITY 2: Color Series (C, MC, CX) =====
    
    # CX series - Color MFP (CX725, CX735, CX860, CX921, CX931, CX942adse, CX94X)
    # Pattern: CX + 2-4 digits/X + optional suffix
    match = re.match(r'^CX(\d{1,3}[X\d])([A-Z]{0,5})?$', model_clean)
    if match:
        model_num = match.group(1)
        series_digit = model_num[0]  # First digit
        return {
            'series_name': 'CX Series',
            'model_pattern': f'CX{series_digit}xx',
            'series_description': f'Lexmark CX{series_digit}xx series color MFPs'
        }
    
    # MC series - Color MFP (MC3224i, MC3224dwe, MC3326i, MC3426i)
    # Pattern: MC + 4 digits + optional suffix
    match = re.match(r'^MC(\d{4})([A-Z]{0,5})?$', model_clean)
    if match:
        model_num = match.group(1)
        series_digit = model_num[0]  # First digit (3)
        return {
            'series_name': 'MC Series',
            'model_pattern': f'MC{series_digit}xxx',
            'series_description': f'Lexmark MC{series_digit}xxx series color multifunction printers'
        }
    
    # C series - Color Single Function (C2326, C3224dw, C3326dw, C3426dw)
    # Pattern: C + 4 digits + optional suffix
    match = re.match(r'^C(\d{4})([A-Z]{0,5})?$', model_clean)
    if match:
        model_num = match.group(1)
        series_digit = model_num[0]  # First digit
        return {
            'series_name': 'C Series',
            'model_pattern': f'C{series_digit}xxx',
            'series_description': f'Lexmark C{series_digit}xxx series color laser printers'
        }
    
    # ===== PRIORITY 3: Monochrome Series (B, MB, MS, MX, XM) =====
    
    # XM series - Enterprise Monochrome MFP (XM3350, XM9145, XM9155)
    # Pattern: XM + 4 digits
    match = re.match(r'^XM(\d{4})$', model_clean)
    if match:
        model_num = match.group(1)
        series_digit = model_num[0]  # First digit
        return {
            'series_name': 'XM Series',
            'model_pattern': f'XM{series_digit}xxx',
            'series_description': f'Lexmark XM{series_digit}xxx series enterprise monochrome MFPs'
        }
    
    # MX series - Monochrome MFP (MX317dn, MX421ade, MX522adhe, MX532adwe, MX622adhe, MX822ade, MX931dse, MX94X)
    # Pattern: MX + 2-4 digits/X + suffix
    match = re.match(r'^MX(\d{1,3}[X\d])([A-Z]{0,5})?$', model_clean)
    if match:
        model_num = match.group(1)
        series_digit = model_num[0]  # First digit
        return {
            'series_name': 'MX Series',
            'model_pattern': f'MX{series_digit}xx',
            'series_description': f'Lexmark MX{series_digit}xx series monochrome MFPs'
        }
    
    # MS series - Monochrome Single Function (MS310dn, MS312dn, MS317dn, MS321dn, MS331dn, MS421dn)
    # Pattern: MS + 3 digits + suffix
    match = re.match(r'^MS(\d{3})([A-Z]{0,5})?$', model_clean)
    if match:
        model_num = match.group(1)
        series_digit = model_num[0]  # First digit
        return {
            'series_name': 'MS Series',
            'model_pattern': f'MS{series_digit}xx',
            'series_description': f'Lexmark MS{series_digit}xx series monochrome laser printers'
        }
    
    # MB series - Monochrome Compact MFP (MB2236adw, MB2236i, MB3442i)
    # Pattern: MB + 4 digits + suffix
    match = re.match(r'^MB(\d{4})([A-Z]{0,5})?$', model_clean)
    if match:
        model_num = match.group(1)
        series_digit = model_num[0]  # First digit
        return {
            'series_name': 'MB Series',
            'model_pattern': f'MB{series_digit}xxx',
            'series_description': f'Lexmark MB{series_digit}xxx series monochrome compact MFPs'
        }
    
    # B series - Monochrome Compact Single Function (B2236dw, B3340dw, B3442dw)
    # Pattern: B + 4 digits + suffix
    match = re.match(r'^B(\d{4})([A-Z]{0,5})?$', model_clean)
    if match:
        model_num = match.group(1)
        series_digit = model_num[0]  # First digit
        return {
            'series_name': 'B Series',
            'model_pattern': f'B{series_digit}xxx',
            'series_description': f'Lexmark B{series_digit}xxx series monochrome compact laser printers'
        }
    
    # ===== PRIORITY 4: Historical Models =====
    
    # Interpret S400 Series - Inkjet (S400, S402, S405, S408, S415)
    if re.match(r'^S4\d{2}$', model_clean):
        return {
            'series_name': 'Interpret S400 Series',
            'model_pattern': 'S4xx',
            'series_description': 'Lexmark Interpret S400 series inkjet printers'
        }
    
    # Plus Matrix Printers (2380-3, 2381-3, 2390-3, 2391-3)
    match = re.match(r'^(23[89][01])-(\d)$', model_clean)
    if match:
        return {
            'series_name': 'Plus Matrix Series',
            'model_pattern': '23xx',
            'series_description': 'Lexmark Plus series dot matrix printers'
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
