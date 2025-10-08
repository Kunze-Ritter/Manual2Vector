"""Parts Extraction Module

Extracts part numbers from error code solutions and descriptions.
Uses manufacturer-specific patterns from config/parts_patterns.json
"""

import re
import json
from pathlib import Path
from typing import List, Optional, Dict


# Load parts patterns config
CONFIG_PATH = Path(__file__).parent.parent / "config" / "parts_patterns.json"
PARTS_CONFIG = None

def _load_config():
    """Load parts patterns configuration"""
    global PARTS_CONFIG
    if PARTS_CONFIG is None:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            PARTS_CONFIG = json.load(f)
    return PARTS_CONFIG


def extract_parts_by_manufacturer(text: str, manufacturer_key: str) -> Optional[str]:
    """
    Extract parts using manufacturer-specific patterns from config
    
    Args:
        text: Text to extract from
        manufacturer_key: Manufacturer key (e.g., 'hp', 'canon', 'konica_minolta')
        
    Returns:
        Comma-separated list of part numbers or None
    """
    if not text:
        return None
    
    config = _load_config()
    
    # Get manufacturer patterns
    if manufacturer_key not in config:
        manufacturer_key = 'generic'
    
    manufacturer_config = config.get(manufacturer_key, {})
    patterns = manufacturer_config.get('patterns', [])
    
    if not patterns:
        return None
    
    parts = []
    min_confidence = config.get('extraction_rules', {}).get('min_confidence', 0.70)
    
    # Extract using all patterns for this manufacturer
    for pattern_config in patterns:
        pattern = pattern_config.get('pattern')
        confidence = pattern_config.get('confidence', 0.5)
        
        if confidence < min_confidence:
            continue
        
        try:
            matches = re.findall(pattern, text)
            parts.extend(matches)
        except re.error:
            continue
    
    # Deduplicate
    parts = list(set(parts))
    
    # Filter out false positives
    parts = _filter_false_positives(parts, config)
    
    if not parts:
        return None
    
    parts.sort()
    return ', '.join(parts)


def _filter_false_positives(parts: List[str], config: Dict) -> List[str]:
    """Filter out common false positives"""
    rules = config.get('extraction_rules', {})
    exclude_near = rules.get('exclude_if_near', [])
    
    # Filter by length
    parts = [p for p in parts if 5 <= len(p) <= 25]
    
    # Filter common false positives
    false_positives = {'ERROR', 'CODE', 'PAGE', 'STEP', 'NOTE', 'FIG', 'TABLE', 'SECTION'}
    parts = [p for p in parts if p.upper() not in false_positives]
    
    return parts


def extract_parts(text: str) -> Optional[str]:
    """
    Extract part numbers from text
    
    Supports multiple formats:
    - 6QN29-67005
    - RM1-1234-000
    - CE285A
    - Q7553X
    - Part: ABC123
    - Part Number: XYZ-456
    
    Args:
        text: Text to extract parts from
        
    Returns:
        Comma-separated list of part numbers or None
    """
    if not text:
        return None
    
    parts = []
    
    # Pattern 1: HP style (6QN29-67005, RM1-1234-000)
    hp_pattern = r'\b([A-Z0-9]{3,6}-[A-Z0-9]{3,6}(?:-[A-Z0-9]{3})?)\b'
    parts.extend(re.findall(hp_pattern, text))
    
    # Pattern 2: Toner/Consumable codes (CE285A, Q7553X, CF283A)
    consumable_pattern = r'\b([A-Z]{2}\d{3,4}[A-Z]{0,2})\b'
    parts.extend(re.findall(consumable_pattern, text))
    
    # Pattern 3: "Part:" or "Part Number:" followed by code
    part_label_pattern = r'(?:part(?:\s+number)?|p/n|part\s*#)\s*[:=]?\s*([A-Z0-9][-A-Z0-9]{4,20})'
    parts.extend(re.findall(part_label_pattern, text, re.IGNORECASE))
    
    # Pattern 4: Konica Minolta style (A1DU-R750-00, 4062-R750-01)
    km_pattern = r'\b([A-Z0-9]{4}-[A-Z0-9]{4}-\d{2})\b'
    parts.extend(re.findall(km_pattern, text))
    
    # Pattern 5: Canon style (FM3-5945-000, QY6-0073-000)
    canon_pattern = r'\b([A-Z]{2}\d-\d{4}-\d{3})\b'
    parts.extend(re.findall(canon_pattern, text))
    
    # Pattern 6: Lexmark style (40X5852, 40X7743)
    lexmark_pattern = r'\b(\d{2}X\d{4})\b'
    parts.extend(re.findall(lexmark_pattern, text))
    
    # Deduplicate and clean
    parts = list(set(parts))
    
    # Filter out common false positives
    false_positives = {'ERROR', 'CODE', 'PAGE', 'STEP', 'NOTE', 'FIG', 'TABLE'}
    parts = [p for p in parts if p.upper() not in false_positives]
    
    # Filter out too short or too long
    parts = [p for p in parts if 5 <= len(p) <= 25]
    
    if not parts:
        return None
    
    # Sort and return
    parts.sort()
    return ', '.join(parts)


def extract_parts_with_context(text: str, manufacturer_key: str = None, max_parts: int = 20) -> List[dict]:
    """
    Extract parts with surrounding context using config patterns
    
    Args:
        text: Text to extract from
        manufacturer_key: Manufacturer key for specific patterns
        max_parts: Maximum number of parts to return
        
    Returns:
        List of dicts with 'part', 'context', 'pattern_name', and 'confidence' keys
    """
    if not text:
        return []
    
    config = _load_config()
    context_window = config.get('extraction_rules', {}).get('context_window_chars', 200)
    min_confidence = config.get('extraction_rules', {}).get('min_confidence', 0.70)
    
    parts_with_context = []
    
    # Determine which manufacturers to use
    manufacturers_to_check = []
    if manufacturer_key and manufacturer_key in config:
        manufacturers_to_check.append(manufacturer_key)
    else:
        # Try all manufacturers if no specific one given
        manufacturers_to_check = [k for k in config.keys() if k != 'extraction_rules']
    
    # Extract from each manufacturer's patterns
    for mfr_key in manufacturers_to_check:
        mfr_config = config.get(mfr_key, {})
        patterns = mfr_config.get('patterns', [])
        
        for pattern_config in patterns:
            pattern = pattern_config.get('pattern')
            confidence = pattern_config.get('confidence', 0.5)
            pattern_name = pattern_config.get('name', 'unknown')
            
            if confidence < min_confidence:
                continue
            
            try:
                for match in re.finditer(pattern, text):
                    part = match.group(0)
                    start = max(0, match.start() - context_window)
                    end = min(len(text), match.end() + context_window)
                    context = text[start:end].strip()
                    
                    parts_with_context.append({
                        'part': part,
                        'context': context,
                        'pattern_name': pattern_name,
                        'confidence': confidence,
                        'manufacturer': mfr_key
                    })
            except re.error:
                continue
    
    # Deduplicate by part number (keep highest confidence)
    seen = {}
    for item in parts_with_context:
        part = item['part']
        if part not in seen or item['confidence'] > seen[part]['confidence']:
            seen[part] = item
    
    unique_parts = list(seen.values())
    
    # Sort by confidence
    unique_parts.sort(key=lambda x: x['confidence'], reverse=True)
    
    return unique_parts[:max_parts]


if __name__ == '__main__':
    # Test
    test_text = """
    Replace the flatbed scanner assembly.
    Flatbed scanner - 6QN29-67005
    
    If error persists, replace toner cartridge CE285A.
    Part Number: RM1-1234-000
    """
    
    parts = extract_parts(test_text)
    print(f"Parts found: {parts}")
    
    parts_ctx = extract_parts_with_context(test_text)
    for item in parts_ctx:
        print(f"Part: {item['part']}")
        print(f"Context: {item['context']}")
        print()
