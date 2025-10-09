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
    
    # UTAX Series Detection (Kyocera rebrand)
    elif 'utax' in manufacturer_lower or 'triumph' in manufacturer_lower or 'ta ' in manufacturer_lower:
        result = _detect_utax_series(model_number)
        if result and context:
            result['confidence'] = _calculate_confidence(result, context)
        return result
    
    # Fujifilm Series Detection (Xerox successor in Asia/Japan)
    elif 'fujifilm' in manufacturer_lower or 'fuji' in manufacturer_lower or 'xerox' in manufacturer_lower:
        result = _detect_fujifilm_series(model_number)
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
    model = model_number.upper().strip()
    
    # Remove common prefixes for pattern matching
    model_clean = re.sub(r'^(?:HP\s+)?', '', model).strip()
    
    # ===== PRIORITY 1: Production & Large Format =====
    
    # HP Indigo Digital Press (12000 HD, 7900, 7K, 6K, 100K)
    if re.match(r'^INDIGO\s+(\d+K?|HD|\d+\s+HD)', model_clean):
        return {
            'series_name': 'Indigo Digital Press',
            'model_pattern': 'Indigo',
            'series_description': 'HP Indigo digital production press'
        }
    
    # HP Latex Production (115, 315, 335, 365, 570, 800, 630, 730, 830, R530, FS50, FS60)
    match = re.match(r'^LATEX\s+([RF]?S?\d{2,3})$', model_clean)
    if match:
        return {
            'series_name': 'Latex',
            'model_pattern': 'Latex',
            'series_description': 'HP Latex production printer'
        }
    
    # DesignJet Large Format (T650, T730, Z6, Z9+)
    match = re.match(r'^DESIGNJET\s+([TZ]\d+\+?)$', model_clean)
    if match:
        series = match.group(1)[0]  # T or Z
        return {
            'series_name': 'DesignJet',
            'model_pattern': f'DesignJet {series}',
            'series_description': f'HP DesignJet {series} series large format printer'
        }
    
    # ===== PRIORITY 2: Inkjet Series =====
    
    # Smart Tank / Smart Tank Plus (5105, 570, 615)
    if re.match(r'^SMART\s+TANK(\s+PLUS)?\s+\d{3,4}$', model_clean):
        if 'PLUS' in model_clean:
            return {
                'series_name': 'Smart Tank Plus',
                'model_pattern': 'Smart Tank Plus',
                'series_description': 'HP Smart Tank Plus refillable ink tank printer'
            }
        return {
            'series_name': 'Smart Tank',
            'model_pattern': 'Smart Tank',
            'series_description': 'HP Smart Tank refillable ink tank printer'
        }
    
    # ENVY Inspire (7920e)
    if re.match(r'^ENVY\s+INSPIRE\s+\d{4}E?$', model_clean):
        return {
            'series_name': 'ENVY Inspire',
            'model_pattern': 'ENVY Inspire',
            'series_description': 'HP ENVY Inspire all-in-one inkjet printer'
        }
    
    # ENVY Photo (6230)
    if re.match(r'^ENVY\s+PHOTO\s+\d{4}$', model_clean):
        return {
            'series_name': 'ENVY Photo',
            'model_pattern': 'ENVY Photo',
            'series_description': 'HP ENVY Photo all-in-one inkjet printer'
        }
    
    # ENVY (6020)
    if re.match(r'^ENVY\s+\d{4}$', model_clean):
        return {
            'series_name': 'ENVY',
            'model_pattern': 'ENVY',
            'series_description': 'HP ENVY all-in-one inkjet printer'
        }
    
    # DeskJet Plus (4120)
    if re.match(r'^DESKJET\s+PLUS\s+\d{4}$', model_clean):
        return {
            'series_name': 'DeskJet Plus',
            'model_pattern': 'DeskJet Plus',
            'series_description': 'HP DeskJet Plus all-in-one inkjet printer'
        }
    
    # DeskJet (3760)
    if re.match(r'^DESKJET\s+\d{4}$', model_clean):
        return {
            'series_name': 'DeskJet',
            'model_pattern': 'DeskJet',
            'series_description': 'HP DeskJet inkjet printer'
        }
    
    # OfficeJet Pro (9020, 7740, 7740 Wide Format)
    match = re.match(r'^(?:OFFICEJET\s+)?PRO\s+(\d{4})(?:\s+WIDE\s+FORMAT)?$', model_clean)
    if match:
        return {
            'series_name': 'OfficeJet Pro',
            'model_pattern': 'OfficeJet Pro',
            'series_description': 'HP OfficeJet Pro inkjet all-in-one'
        }
    
    # OfficeJet (6950)
    if re.match(r'^OFFICEJET\s+\d{4}$', model_clean):
        return {
            'series_name': 'OfficeJet',
            'model_pattern': 'OfficeJet',
            'series_description': 'HP OfficeJet inkjet all-in-one'
        }
    
    # PageWide Pro (352dw, 477dw, 577dw, 7740)
    match = re.match(r'^PAGEWIDE\s+PRO\s+(\d{3,4})[A-Z]{0,3}$', model_clean)
    if match:
        return {
            'series_name': 'PageWide Pro',
            'model_pattern': 'PageWide Pro',
            'series_description': 'HP PageWide Pro business inkjet printer'
        }
    
    # PageWide (352dw)
    match = re.match(r'^PAGEWIDE\s+(\d{3})[A-Z]{0,3}$', model_clean)
    if match:
        return {
            'series_name': 'PageWide',
            'model_pattern': 'PageWide',
            'series_description': 'HP PageWide inkjet printer'
        }
    
    # ===== PRIORITY 3: LaserJet Enterprise =====
    
    # LaserJet Enterprise MFP (M634h, M725)
    match = re.match(r'^(?:LASERJET\s+)?ENTERPRISE\s+MFP\s+M(\d{3,4})[A-Z]?$', model_clean)
    if match:
        series_num = match.group(1)
        return {
            'series_name': 'LaserJet Enterprise MFP',
            'model_pattern': f'M{series_num[0]}xx',
            'series_description': f'HP LaserJet Enterprise MFP M{series_num[0]}xx series'
        }
    
    # LaserJet Enterprise (M506, M607, M611, M632, M635)
    match = re.match(r'^(?:LASERJET\s+)?ENTERPRISE\s+M(\d{3})$', model_clean)
    if match:
        series_num = match.group(1)
        return {
            'series_name': 'LaserJet Enterprise',
            'model_pattern': f'M{series_num[0]}xx',
            'series_description': f'HP LaserJet Enterprise M{series_num[0]}xx series'
        }
    
    # ===== PRIORITY 4: Color LaserJet Pro MFP =====
    
    # Color LaserJet Pro MFP (M255dw, M283fdw, M452nw, M454dn, M479fdn, M479fdw, M281fdw)
    match = re.match(r'^(?:COLOR\s+LASERJET\s+PRO\s+)?MFP\s+M(\d{3,4})[A-Z]{0,5}$', model_clean)
    if match:
        series_num = match.group(1)
        return {
            'series_name': 'Color LaserJet Pro MFP',
            'model_pattern': f'M{series_num[0]}xx',
            'series_description': f'HP Color LaserJet Pro MFP M{series_num[0]}xx series'
        }
    
    # ===== PRIORITY 5: LaserJet Pro MFP =====
    
    # LaserJet Pro MFP (M28w, M130fn, M148fdw, M2727nf, M428fdn, M428fdw, M429fdn)
    match = re.match(r'^(?:LASERJET\s+PRO\s+)?MFP\s+M(\d{2,4})[A-Z]{0,5}$', model_clean)
    if match:
        series_num = match.group(1)
        return {
            'series_name': 'LaserJet Pro MFP',
            'model_pattern': f'M{series_num[0]}xx' if len(series_num) >= 3 else f'M{series_num}',
            'series_description': f'HP LaserJet Pro MFP M{series_num[0]}xx series'
        }
    
    # ===== PRIORITY 6: Laser MFP (Compact) =====
    
    # Laser MFP (131, 133, 135, 137, 135a, 137fnw)
    match = re.match(r'^LASER\s+MFP\s+1(\d{2})[A-Z]{0,5}$', model_clean)
    if match:
        return {
            'series_name': 'Laser MFP',
            'model_pattern': '1xx',
            'series_description': 'HP Laser MFP 1xx series compact multifunction printer'
        }
    
    # ===== PRIORITY 7: LaserJet Pro (Single Function) =====
    
    # LaserJet Pro M series (M15w, M28w, M102w, M130fn, M404dn, M428fdw, M521dn)
    match = re.match(r'^(?:LASERJET\s+PRO\s+)?M(\d{2,3})[A-Z]{0,5}$', model_clean)
    if match:
        series_num = match.group(1)
        return {
            'series_name': 'LaserJet Pro',
            'model_pattern': f'M{series_num[0]}xx' if len(series_num) >= 3 else f'M{series_num}',
            'series_description': f'HP LaserJet Pro M{series_num[0]}xx series'
        }
    
    # ===== PRIORITY 8: Legacy Patterns =====
    
    # LaserJet E series (E50045, E50145, E52545, etc.)
    match = re.match(r'^E(\d)(\d{2})', model_clean)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'LaserJet Enterprise',
            'model_pattern': f'E{series_digit}xxxx',
            'series_description': f'HP LaserJet Enterprise E{series_digit}0000 series'
        }
    
    # OfficeJet Pro X series (X580, X585, etc.)
    match = re.match(r'^X(\d)(\d{2})', model_clean)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'OfficeJet Pro',
            'model_pattern': f'X{series_digit}xx',
            'series_description': f'HP OfficeJet Pro X{series_digit}00 series'
        }
    
    # PageWide series (P77960, P55250, etc.)
    match = re.match(r'^P(\d)(\d{4})', model_clean)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'PageWide',
            'model_pattern': f'P{series_digit}xxxx',
            'series_description': f'HP PageWide P{series_digit} series'
        }
    
    # Color LaserJet series (CP5225, CP4525, etc.)
    match = re.match(r'^CP(\d{2})', model_clean)
    if match:
        return {
            'series_name': 'Color LaserJet',
            'model_pattern': f'CP{match.group(1)}xx',
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
    """Detect Kyocera series - Returns marketing name + technical pattern"""
    model = model_number.upper().strip()
    
    # Remove common prefixes for pattern matching
    model_clean = re.sub(r'^(?:KYOCERA\s+)?', '', model).strip()
    
    # ===== PRIORITY 1: TASKalfa Pro (Production) =====
    
    # TASKalfa Pro (Pro 15000c, Pro 55000c)
    match = re.match(r'^(?:TASKALFA\s+)?PRO\s+(\d{5})C?$', model_clean)
    if match:
        return {
            'series_name': 'TASKalfa Pro',
            'model_pattern': 'TASKalfa Pro',
            'series_description': 'Kyocera TASKalfa Pro production color systems'
        }
    
    # ===== PRIORITY 2: TASKalfa (A3/A4 MFP) =====
    
    # TASKalfa with ci suffix (2553ci, 5053ci, etc.)
    match = re.match(r'^(?:TASKALFA\s+)?(\d{4})CI$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'TASKalfa',
            'model_pattern': f'TASKalfa {series_digit}xxxci',
            'series_description': f'Kyocera TASKalfa {series_digit}xxxci series color MFPs'
        }
    
    # TASKalfa general (2552, 3252, etc.)
    match = re.match(r'^(?:TASKALFA\s+)?(\d{4})([A-Z]{0,3})?$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'TASKalfa',
            'model_pattern': f'TASKalfa {series_digit}xxx',
            'series_description': f'Kyocera TASKalfa {series_digit}xxx series MFPs'
        }
    
    # ===== PRIORITY 3: ECOSYS PA/MA/M Serie =====
    
    # ECOSYS PA (PA3500cx, PA4500x)
    match = re.match(r'^(?:ECOSYS\s+)?PA(\d{4})([A-Z]{0,3})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'ECOSYS PA',
            'model_pattern': f'ECOSYS PA{series_digit}xxx',
            'series_description': f'Kyocera ECOSYS PA{series_digit}xxx series color printers'
        }
    
    # ECOSYS MA (MA2100cfx, MA3500cifx)
    match = re.match(r'^(?:ECOSYS\s+)?MA(\d{4})([A-Z]{0,5})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'ECOSYS MA',
            'model_pattern': f'ECOSYS MA{series_digit}xxx',
            'series_description': f'Kyocera ECOSYS MA{series_digit}xxx series color MFPs'
        }
    
    # ECOSYS M (M3860idnf, M4132idn, M8130cidn)
    match = re.match(r'^(?:ECOSYS\s+)?M(\d{4})([A-Z]{0,5})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'ECOSYS M',
            'model_pattern': f'ECOSYS M{series_digit}xxx',
            'series_description': f'Kyocera ECOSYS M{series_digit}xxx series MFPs'
        }
    
    # ===== PRIORITY 4: FS-Serie (Drucker & MFP) =====
    
    # FS-Serie MFP (FS-1030MFP, FS-6530MFP)
    match = re.match(r'^FS-(\d{4})MFP$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'FS-Series MFP',
            'model_pattern': f'FS-{series_digit}xxxMFP',
            'series_description': f'Kyocera FS-{series_digit}xxx series multifunction printers'
        }
    
    # FS-Serie Drucker (FS-1000, FS-1120DN, FS-1320D, FS-4020DN, FS-6020DTN)
    match = re.match(r'^FS-(\d{4})([A-Z]{0,5})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'FS-Series',
            'model_pattern': f'FS-{series_digit}xxx',
            'series_description': f'Kyocera FS-{series_digit}xxx series printers'
        }
    
    # ===== PRIORITY 5: KM-Serie (Ältere MFPs) =====
    
    # KM-Serie (KM-2050, KM-5050)
    match = re.match(r'^KM-(\d{4})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'KM-Series',
            'model_pattern': f'KM-{series_digit}xxx',
            'series_description': f'Kyocera KM-{series_digit}xxx series legacy MFPs'
        }
    
    # ===== PRIORITY 6: Weitere Serien (DC, DP, TC, F) =====
    
    # TC-Serie (TC-4026i)
    match = re.match(r'^TC-(\d{4})([A-Z]?)$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'TC-Series',
            'model_pattern': f'TC-{series_digit}xxx',
            'series_description': f'Kyocera TC-{series_digit}xxx series'
        }
    
    # F-Serie (F 2010)
    match = re.match(r'^F\s*(\d{4})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'F-Series',
            'model_pattern': f'F {series_digit}xxx',
            'series_description': f'Kyocera F {series_digit}xxx series'
        }
    
    # DC-Serie
    match = re.match(r'^DC-(\d{4})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'DC-Series',
            'model_pattern': f'DC-{series_digit}xxx',
            'series_description': f'Kyocera DC-{series_digit}xxx series'
        }
    
    # DP-Serie
    match = re.match(r'^DP-(\d{4})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'DP-Series',
            'model_pattern': f'DP-{series_digit}xxx',
            'series_description': f'Kyocera DP-{series_digit}xxx series'
        }
    
    return None


def _detect_utax_series(model_number: str) -> Optional[Dict]:
    """Detect UTAX series - Returns marketing name + technical pattern
    
    UTAX is a Kyocera rebrand (TA Triumph-Adler)
    """
    model = model_number.upper().strip()
    
    # Remove common prefixes for pattern matching
    model_clean = re.sub(r'^(?:UTAX\s+)?', '', model).strip()
    
    # ===== PRIORITY 1: P-Serie (Monochrom & Farb MFP/Drucker) =====
    
    # P-Serie MFP with i suffix (P-4532i MFP, P-4539i MFP, P-5539i MFP, P-6039i MFP)
    match = re.match(r'^P-(\d)(\d{3})I\s*MFP$', model_clean)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'P-Series MFP',
            'model_pattern': f'P-{series_digit}xxxI MFP',
            'series_description': f'UTAX P-{series_digit}xxx series multifunction printers (i-model)'
        }
    
    # P-Serie MFP without i (P-4532 MFP, P-4539 MFP)
    match = re.match(r'^P-(\d)(\d{3})\s*MFP$', model_clean)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'P-Series MFP',
            'model_pattern': f'P-{series_digit}xxx MFP',
            'series_description': f'UTAX P-{series_digit}xxx series multifunction printers'
        }
    
    # P-Serie Drucker (P-4534DN, P-5034DN, P-5534DN, P-6034DN)
    match = re.match(r'^P-(\d)(\d{3})([A-Z]{0,3})$', model_clean)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'P-Series',
            'model_pattern': f'P-{series_digit}xxx',
            'series_description': f'UTAX P-{series_digit}xxx series printers'
        }
    
    # ===== PRIORITY 2: LP-Serie (A3-Monochrom) =====
    
    # LP-Serie (LP 3130DN, LP 4155DN, LP 3245, LP 4345)
    match = re.match(r'^LP\s*(\d)(\d{3})([A-Z]{0,3})$', model_clean)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': 'LP-Series',
            'model_pattern': f'LP {series_digit}xxx',
            'series_description': f'UTAX LP {series_digit}xxx series A3 monochrome printers'
        }
    
    # ===== PRIORITY 3: CDC/CDP/CD-Serie (Farb-MFP/Drucker) =====
    
    # CDC Serie (CDC 1720, CDC 2240)
    match = re.match(r'^CDC\s*(\d{4})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'CDC Series',
            'model_pattern': f'CDC {series_digit}xxx',
            'series_description': f'UTAX CDC {series_digit}xxx series color MFPs'
        }
    
    # CDP Serie
    match = re.match(r'^CDP\s*(\d{4})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'CDP Series',
            'model_pattern': f'CDP {series_digit}xxx',
            'series_description': f'UTAX CDP {series_digit}xxx series color printers'
        }
    
    # CD Serie (CD 1630)
    match = re.match(r'^CD\s*(\d{4})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'CD Series',
            'model_pattern': f'CD {series_digit}xxx',
            'series_description': f'UTAX CD {series_digit}xxx series color devices'
        }
    
    # ===== PRIORITY 4: Numeric Models (Kyocera-based) =====
    
    # 4-digit models with "ci" suffix (5006ci, 4006ci, 3206ci, etc.)
    # These are Kyocera TASKalfa rebrands
    match = re.match(r'^(\d)(\d{3})CI$', model_clean)
    if match:
        series_digit = match.group(1)
        return {
            'series_name': f'{series_digit}xxxci Series',
            'model_pattern': f'{series_digit}xxxci',
            'series_description': f'UTAX {series_digit}xxxci series color MFPs (Kyocera-based)'
        }
    
    return None


def _detect_fujifilm_series(model_number: str) -> Optional[Dict]:
    """Detect Fujifilm series - Returns marketing name + technical pattern
    
    Fujifilm is the Xerox successor in Asia/Japan (formerly Fuji Xerox)
    """
    model = model_number.upper().strip()
    
    # Remove common prefixes for pattern matching
    model_clean = re.sub(r'^(?:FUJIFILM\s+)?', '', model).strip()
    
    # ===== PRIORITY 1: Production Systems =====
    
    # Revoria Press (SC285(S), EC2100(S), PC1120(S))
    match = re.match(r'^REVORIA\s+PRESS\s+([SEMP]C)(\d{3,4})\(?S?\)?$', model_clean)
    if match:
        series_prefix = match.group(1)  # SC, EC, MC, PC
        return {
            'series_name': 'Revoria Press',
            'model_pattern': f'Revoria Press {series_prefix}',
            'series_description': f'Fujifilm Revoria Press {series_prefix} series high-end production systems'
        }
    
    # JetPress (750S)
    match = re.match(r'^JETPRESS\s+(\d{3,4})S?$', model_clean)
    if match:
        return {
            'series_name': 'JetPress',
            'model_pattern': 'JetPress',
            'series_description': 'Fujifilm JetPress inkjet SRA3 production printer'
        }
    
    # ===== PRIORITY 2: ApeosPro (Light Production) =====
    
    # ApeosPro C Series (C810, C750, C650)
    match = re.match(r'^APEOSPRO\s+C(\d{3})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'ApeosPro',
            'model_pattern': f'ApeosPro C{series_digit}xx',
            'series_description': f'Fujifilm ApeosPro C{series_digit}xx series light production color systems'
        }
    
    # ===== PRIORITY 3: Apeos/ApeosPort (MFP) =====
    
    # ApeosPort-VII (ApeosPort-VII C4473)
    match = re.match(r'^APEOSPORT-VII\s+C(\d{4})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'ApeosPort-VII',
            'model_pattern': f'ApeosPort-VII C{series_digit}xxx',
            'series_description': f'Fujifilm ApeosPort-VII C{series_digit}xxx series color MFPs'
        }
    
    # ApeosPort (general)
    match = re.match(r'^APEOSPORT\s+C(\d{4})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'ApeosPort',
            'model_pattern': f'ApeosPort C{series_digit}xxx',
            'series_description': f'Fujifilm ApeosPort C{series_digit}xxx series color MFPs'
        }
    
    # Apeos MFP (C3060, C3070)
    match = re.match(r'^APEOS\s+C(\d{4})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'Apeos',
            'model_pattern': f'Apeos C{series_digit}xxx',
            'series_description': f'Fujifilm Apeos C{series_digit}xxx series color MFPs'
        }
    
    # ===== PRIORITY 4: ApeosPrint (Printer) =====
    
    # ApeosPrint (C325, C4030)
    match = re.match(r'^APEOSPRINT\s+C(\d{3,4})$', model_clean)
    if match:
        series_num = match.group(1)
        series_digit = series_num[0]
        return {
            'series_name': 'ApeosPrint',
            'model_pattern': f'ApeosPrint C{series_digit}xx',
            'series_description': f'Fujifilm ApeosPrint C{series_digit}xx series color printers'
        }
    
    # ===== PRIORITY 5: INSTAX (Photo Printers) =====
    
    # INSTAX mini Link
    if re.match(r'^INSTAX\s+MINI\s+LINK', model_clean):
        return {
            'series_name': 'INSTAX mini Link',
            'model_pattern': 'INSTAX mini Link',
            'series_description': 'Fujifilm INSTAX mini Link compact photo printer'
        }
    
    # INSTAX SQUARE Link
    if re.match(r'^INSTAX\s+SQUARE\s+LINK', model_clean):
        return {
            'series_name': 'INSTAX SQUARE Link',
            'model_pattern': 'INSTAX SQUARE Link',
            'series_description': 'Fujifilm INSTAX SQUARE Link compact photo printer'
        }
    
    # INSTAX Link Wide
    if re.match(r'^INSTAX\s+LINK\s+WIDE', model_clean):
        return {
            'series_name': 'INSTAX Link Wide',
            'model_pattern': 'INSTAX Link Wide',
            'series_description': 'Fujifilm INSTAX Link Wide compact photo printer'
        }
    
    # INSTAX (generic)
    if re.match(r'^INSTAX', model_clean):
        return {
            'series_name': 'INSTAX',
            'model_pattern': 'INSTAX',
            'series_description': 'Fujifilm INSTAX compact photo printer'
        }
    
    # ===== PRIORITY 6: Legacy DocuPrint/DocuCentre (Xerox-based) =====
    
    # DocuPrint (CP505)
    match = re.match(r'^DOCUPRINT\s+([A-Z]{2})(\d{3})$', model_clean)
    if match:
        series_prefix = match.group(1)
        return {
            'series_name': 'DocuPrint',
            'model_pattern': f'DocuPrint {series_prefix}',
            'series_description': f'Fujifilm DocuPrint {series_prefix} series (Xerox-based legacy)'
        }
    
    # DocuCentre
    match = re.match(r'^DOCUCENTRE\s+([A-Z]{1,2})(\d{3,4})$', model_clean)
    if match:
        series_prefix = match.group(1)
        return {
            'series_name': 'DocuCentre',
            'model_pattern': f'DocuCentre {series_prefix}',
            'series_description': f'Fujifilm DocuCentre {series_prefix} series MFPs (Xerox-based legacy)'
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
