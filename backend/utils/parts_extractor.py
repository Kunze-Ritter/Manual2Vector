"""Parts Extraction Module

Extracts part numbers from error code solutions and descriptions.
"""

import re
from typing import List, Optional


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


def extract_parts_with_context(text: str, max_parts: int = 10) -> List[dict]:
    """
    Extract parts with surrounding context
    
    Args:
        text: Text to extract from
        max_parts: Maximum number of parts to return
        
    Returns:
        List of dicts with 'part' and 'context' keys
    """
    if not text:
        return []
    
    parts_with_context = []
    
    # Find all part numbers with context
    patterns = [
        (r'([A-Z0-9]{3,6}-[A-Z0-9]{3,6}(?:-[A-Z0-9]{3})?)', 50),  # HP style
        (r'([A-Z]{2}\d{3,4}[A-Z]{0,2})', 30),  # Consumables
        (r'([A-Z0-9]{4}-[A-Z0-9]{4}-\d{2})', 50),  # Konica Minolta
        (r'([A-Z]{2}\d-\d{4}-\d{3})', 50),  # Canon
        (r'(\d{2}X\d{4})', 30),  # Lexmark
    ]
    
    for pattern, context_len in patterns:
        for match in re.finditer(pattern, text):
            part = match.group(1)
            start = max(0, match.start() - context_len)
            end = min(len(text), match.end() + context_len)
            context = text[start:end].strip()
            
            parts_with_context.append({
                'part': part,
                'context': context
            })
    
    # Deduplicate by part number
    seen = set()
    unique_parts = []
    for item in parts_with_context:
        if item['part'] not in seen:
            seen.add(item['part'])
            unique_parts.append(item)
    
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
