"""
Model Number Cleaner

Cleans up model numbers extracted from documents to remove noise and duplicates.
"""

import re
from typing import Optional


def clean_model_number(model_number: str) -> str:
    """
    Clean model number by removing common noise patterns
    
    Args:
        model_number: Raw model number from extraction
        
    Returns:
        Cleaned model number
        
    Examples:
        >>> clean_model_number("RU-702 (1st device)")
        "RU-702"
        >>> clean_model_number("RU-702 (2nd device)")
        "RU-702"
        >>> clean_model_number("LS (1st tandem), LS (2nd tandem)")
        "LS"
        >>> clean_model_number("SD-506, SD-513")
        "SD-506"
    """
    if not model_number:
        return model_number
    
    original = model_number
    
    # Remove device/tandem suffixes
    # Pattern: (1st device), (2nd device), (1st tandem), (2nd tandem)
    model_number = re.sub(r'\s*\(\d+(?:st|nd|rd|th)\s+(?:device|tandem)\)', '', model_number, flags=re.IGNORECASE)
    
    # Remove multiple model numbers (keep only first)
    # Pattern: "SD-506, SD-513" -> "SD-506"
    if ',' in model_number:
        model_number = model_number.split(',')[0].strip()
    
    # Remove "only" suffix
    # Pattern: "Business card tray only (The JS-507 must be installed)"
    model_number = re.sub(r'\s+only\s*\(.*?\)$', '', model_number, flags=re.IGNORECASE)
    
    # Remove quotes
    model_number = model_number.strip('"\'')
    
    # Remove extra whitespace
    model_number = ' '.join(model_number.split())
    
    # Log if changed
    if model_number != original:
        from .logger import get_logger
        logger = get_logger()
        logger.debug(f"Cleaned model number: '{original}' -> '{model_number}'")
    
    return model_number


def is_duplicate_model(model1: str, model2: str) -> bool:
    """
    Check if two model numbers are duplicates (ignoring suffixes)
    
    Args:
        model1: First model number
        model2: Second model number
        
    Returns:
        True if models are duplicates
        
    Examples:
        >>> is_duplicate_model("RU-702", "RU-702 (1st device)")
        True
        >>> is_duplicate_model("RU-702", "RU-703")
        False
    """
    clean1 = clean_model_number(model1)
    clean2 = clean_model_number(model2)
    
    return clean1.lower() == clean2.lower()


if __name__ == "__main__":
    # Test cases
    test_cases = [
        "RU-702 (1st device)",
        "RU-702 (2nd device)",
        "LS (1st tandem), LS (2nd tandem)",
        "SD-506, SD-513",
        "Business card tray only (The JS-507 must be installed)",
        "RU-518m (1st device), RU-518m (2nd device)",
        "C4080",
    ]
    
    print("Model Number Cleaning Tests:")
    print("=" * 60)
    for test in test_cases:
        cleaned = clean_model_number(test)
        print(f"{test:50s} -> {cleaned}")
