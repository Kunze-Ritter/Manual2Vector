#!/usr/bin/env python3
"""Test error code extraction"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from processors.error_code_extractor import ErrorCodeExtractor

# Test text from PDF
test_text = """
30.03.30 Scanner Failure
Flatbed motor shutdown.
The SCB cannot communicate with the flatbed scanner motor.
"""

print("\n" + "=" * 100)
print("ERROR CODE EXTRACTION TEST")
print("=" * 100)

print(f"\nTest Text:\n{test_text}")

extractor = ErrorCodeExtractor()

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Extract codes
print("\nEXTRACTING WITH DEBUG MODE...\n")
codes = extractor.extract_from_text(
    text=test_text,
    page_number=6,
    manufacturer_name="HP"
)
print(f"\nEXTRACTION COMPLETE\n")

print(f"\n{'='*100}")
print(f"EXTRACTED CODES: {len(codes)}")
print(f"{'='*100}\n")

if codes:
    for code in codes:
        print(f"✅ Code: {code.error_code}")
        print(f"   Description: {code.error_description}")
        print(f"   Context: {code.context[:100]}...")
        print(f"   Confidence: {code.confidence}")
        print(f"   Page: {code.page_number}")
        print()
else:
    print("❌ NO CODES EXTRACTED!")
    print("\n💡 Debugging why...")
    
    # Test pattern directly
    import re
    pattern = r'\b(\d{2}\.\d{2}\.\d{2})\b'
    matches = re.findall(pattern, test_text)
    print(f"   ✅ Pattern matches: {matches}")
    
    # Test context validation
    context_lower = test_text.lower()
    required_keywords = [
        "error", "code", "fault", "trouble", "malfunction", "failure", "alarm",
        "warning", "service", "maintenance", "troubleshooting", "diagnostic",
        "status", "message", "alert", "problem", "issue", "exception"
    ]
    
    found_keywords = [kw for kw in required_keywords if kw in context_lower]
    print(f"   ✅ Found keywords: {found_keywords}")
    
    excluded_keywords = ["page", "figure", "table", "section", "model", "serial",
                        "copyright", "trademark", "version", "revision"]
    found_excluded = [kw for kw in excluded_keywords if kw in context_lower]
    print(f"   ❌ Excluded keywords: {found_excluded}")
    
    # Check validation
    validation_regex = r'^\d{2}\.\d{1,3}[xX]?\.\d{2}$'
    is_valid = bool(re.match(validation_regex, '30.03.30'))
    print(f"   Validation: {is_valid}")

print("=" * 100)
