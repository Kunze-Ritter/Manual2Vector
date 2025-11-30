#!/usr/bin/env python3
"""Debug error code extraction step by step"""

import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from processors.error_code_extractor import ErrorCodeExtractor

test_text = """
30.03.30 Scanner Failure
Flatbed motor shutdown.
The SCB cannot communicate with the flatbed scanner motor.
"""

print("\n" + "=" * 100)
print("DEBUG ERROR CODE EXTRACTION")
print("=" * 100)

extractor = ErrorCodeExtractor()

# Get HP config
hp_config = extractor.patterns_config.get('hp', {})
patterns = hp_config.get('patterns', [])
validation_regex = hp_config.get('validation_regex')

print(f"\nHP Patterns: {len(patterns)}")
print(f"Validation Regex: {validation_regex}\n")

# Test each pattern
for i, pattern_str in enumerate(patterns, 1):
    print(f"\n--- Pattern {i}: {pattern_str} ---")
    
    try:
        pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
        matches = list(pattern.finditer(test_text))
        
        print(f"Matches: {len(matches)}")
        
        for match in matches:
            code = match.group(1) if match.groups() else match.group(0)
            code = code.strip()
            
            print(f"\n  Found: '{code}'")
            
            # Check validation
            if validation_regex:
                is_valid = bool(re.match(validation_regex, code))
                print(f"  Validation: {is_valid}")
                if not is_valid:
                    print(f"  ❌ FAILED VALIDATION")
                    continue
            
            # Check context
            context_start = max(0, match.start() - 200)
            context_end = min(len(test_text), match.end() + 200)
            context = test_text[context_start:context_end].strip()
            
            print(f"  Context: '{context[:80]}...'")
            
            # Validate context
            context_lower = context.lower()
            required_keywords = ["error", "code", "fault", "trouble", "malfunction", "failure"]
            has_required = any(kw in context_lower for kw in required_keywords)
            print(f"  Has required keywords: {has_required}")
            
            if not has_required:
                print(f"  ❌ FAILED CONTEXT VALIDATION")
                continue
            
            # Extract description
            desc_start = match.end()
            desc_end = min(len(test_text), desc_start + 200)
            description = test_text[desc_start:desc_end].strip()
            
            # Get first line as description
            if '\n' in description:
                description = description.split('\n')[0].strip()
            
            print(f"  Description: '{description}'")
            
            # Check if generic
            generic_terms = ['error', 'code', 'failure', 'problem']
            is_generic = len(description.split()) < 3 or all(term in description.lower() for term in generic_terms)
            print(f"  Is generic: {is_generic}")
            
            if is_generic:
                print(f"  ❌ DESCRIPTION TOO GENERIC")
                continue
            
            print(f"  ✅ PASSED ALL CHECKS!")
    
    except re.error as e:
        print(f"  ❌ Invalid regex: {e}")

print("\n" + "=" * 100)
