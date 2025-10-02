"""
Error Code Extraction Module

Extracts error codes with STRICT validation.
ONLY numeric codes (XX.XX.XX format), NO random words!
"""

import re
from typing import List, Optional, Tuple
from .logger import get_logger
from .models import ExtractedErrorCode, ValidationError as ValError


logger = get_logger()


# Strict error code patterns
ERROR_CODE_PATTERNS = {
    'hp_standard': re.compile(
        r'\b(\d{2}\.\d{2}\.\d{2})\b'  # 13.20.01
    ),
    'hp_short': re.compile(
        r'\b(\d{2}\.\d{2})\b'  # 49.38
    ),
    'hp_events': re.compile(
        r'\b(\d{5}-\d{4})\b'  # 12345-6789
    ),
}

# Words that are NOT error codes (reject these!)
REJECT_CODES = {
    'descriptions', 'information', 'lookup', 'troubleshooting',
    'specify', 'displays', 'field', 'system', 'file', 'page',
    'section', 'chapter', 'table', 'figure', 'error', 'code',
    'manual', 'document', 'version', 'revision', 'contents'
}

# Technical terms that indicate real error context
TECHNICAL_TERMS = {
    'fuser', 'sensor', 'motor', 'cartridge', 'drum', 'roller',
    'replace', 'check', 'clean', 'reset', 'calibrate', 'inspect',
    'toner', 'paper', 'jam', 'feed', 'pickup', 'transfer',
    'formatter', 'engine', 'scanner', 'adf', 'duplex', 'tray',
    'thermistor', 'heater', 'solenoid', 'clutch', 'gear', 'belt'
}


class ErrorCodeExtractor:
    """Extract error codes with strict validation"""
    
    def __init__(self):
        """Initialize error code extractor"""
        self.logger = get_logger()
    
    def extract_from_text(
        self,
        text: str,
        page_number: int
    ) -> List[ExtractedErrorCode]:
        """
        Extract error codes from text
        
        Args:
            text: Text to extract from
            page_number: Page number
            
        Returns:
            List of validated error codes
        """
        if not text or len(text) < 20:
            return []
        
        found_codes = []
        
        for pattern_name, pattern in ERROR_CODE_PATTERNS.items():
            matches = pattern.finditer(text)
            
            for match in matches:
                code = match.group(1)
                
                # Validate code format
                if not self._validate_code_format(code):
                    continue
                
                # Extract context
                context = self._extract_context(text, match.start(), match.end())
                
                # Extract description
                description = self._extract_description(text, match.end())
                
                # Skip if description is too generic
                if not description or self._is_generic_description(description):
                    continue
                
                # Extract solution
                solution = self._extract_solution(context, text, match.end())
                
                # Calculate confidence
                confidence = self._calculate_confidence(
                    code, description, solution, context
                )
                
                # Only add if confidence is high enough
                if confidence < 0.6:
                    self.logger.debug(
                        f"Skipping code '{code}' - confidence too low ({confidence:.2f})"
                    )
                    continue
                
                # Determine severity
                severity = self._determine_severity(description, solution)
                
                try:
                    error_code = ExtractedErrorCode(
                        error_code=code,
                        error_description=description,
                        solution_text=solution or "No solution found",
                        context_text=context,
                        confidence=confidence,
                        page_number=page_number,
                        extraction_method=pattern_name,
                        severity_level=severity
                    )
                    found_codes.append(error_code)
                except Exception as e:
                    self.logger.debug(
                        f"Validation failed for code '{code}': {e}"
                    )
        
        # Deduplicate
        unique_codes = self._deduplicate(found_codes)
        
        if unique_codes:
            self.logger.info(
                f"Extracted {len(unique_codes)} error codes from page {page_number}"
            )
        
        return unique_codes
    
    def _validate_code_format(self, code: str) -> bool:
        """
        Validate that code matches expected format
        
        Returns:
            True if valid numeric code
        """
        # Must match numeric pattern
        if not re.match(r'^\d{2}\.\d{2}(\.\d{2})?$', code):
            return False
        
        # Not a reject word
        if code.lower() in REJECT_CODES:
            return False
        
        return True
    
    def _extract_context(
        self,
        text: str,
        start_pos: int,
        end_pos: int,
        context_size: int = 500
    ) -> str:
        """
        Extract context around error code
        
        Args:
            text: Full text
            start_pos: Error code start position
            end_pos: Error code end position
            context_size: Characters to include before/after
            
        Returns:
            Context text
        """
        context_start = max(0, start_pos - context_size)
        context_end = min(len(text), end_pos + context_size)
        
        context = text[context_start:context_end]
        return context.strip()
    
    def _extract_description(
        self,
        text: str,
        code_end_pos: int,
        max_length: int = 500
    ) -> Optional[str]:
        """
        Extract error description (text after error code)
        
        Args:
            text: Full text
            code_end_pos: Position where error code ends
            max_length: Maximum description length
            
        Returns:
            Description or None
        """
        # Extract text after code
        remaining_text = text[code_end_pos:code_end_pos + max_length]
        
        # Find end of sentence or paragraph
        sentence_end = re.search(r'[.!?\n]{1,2}', remaining_text)
        
        if sentence_end:
            description = remaining_text[:sentence_end.start()].strip()
        else:
            description = remaining_text.strip()
        
        # Skip if too short
        if len(description) < 20:
            return None
        
        # Remove common prefixes
        for prefix in [':', '-', '–', '—', 'error', 'code']:
            description = description.lstrip(prefix).strip()
        
        return description
    
    def _extract_solution(
        self,
        context: str,
        full_text: str,
        code_end_pos: int
    ) -> Optional[str]:
        """
        Extract solution steps from context or following text
        
        Returns:
            Solution text or None
        """
        # Look for numbered lists or bullet points in context
        solution_pattern = re.compile(
            r'(?:solution|fix|remedy|action|steps?):\s*(.{50,1000})',
            re.IGNORECASE | re.DOTALL
        )
        
        match = solution_pattern.search(context)
        if match:
            return match.group(1).strip()
        
        # Look for numbered steps (1., 2., etc.)
        steps_pattern = re.compile(
            r'((?:\d+\.\s+.{20,}){2,})',  # At least 2 numbered steps
            re.MULTILINE
        )
        
        text_after = full_text[code_end_pos:code_end_pos + 1000]
        match = steps_pattern.search(text_after)
        if match:
            return match.group(1).strip()
        
        return None
    
    def _is_generic_description(self, description: str) -> bool:
        """
        Check if description is too generic to be useful
        
        Returns:
            True if generic
        """
        generic_phrases = [
            'refer to manual',
            'see documentation',
            'contact support',
            'error code',
            'see page',
            'refer to page',
            'table',
            'figure'
        ]
        
        desc_lower = description.lower()
        
        # If short and contains generic phrase
        if len(description) < 50:
            for phrase in generic_phrases:
                if phrase in desc_lower:
                    return True
        
        return False
    
    def _calculate_confidence(
        self,
        code: str,
        description: str,
        solution: Optional[str],
        context: str
    ) -> float:
        """
        Calculate extraction confidence based on quality indicators
        
        Returns:
            Confidence score (0.0 - 1.0)
        """
        confidence = 0.0
        
        # Base confidence for valid format
        confidence += 0.3
        
        # Has proper description (not generic)
        if description and len(description) > 30:
            confidence += 0.2
        if description and len(description) > 100:
            confidence += 0.1
        
        # Has solution steps
        if solution:
            confidence += 0.2
            # Bonus for numbered or bulleted steps
            if re.search(r'\d+\.|\•|\*', solution):
                confidence += 0.1
        
        # Context contains technical terms
        context_lower = context.lower()
        tech_term_count = sum(
            1 for term in TECHNICAL_TERMS if term in context_lower
        )
        if tech_term_count > 0:
            confidence += 0.1
        if tech_term_count > 3:
            confidence += 0.1
        
        # Code appears multiple times (important!)
        if context.count(code) > 1:
            confidence += 0.1
        
        # Context has reasonable length
        if 200 < len(context) < 2000:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _determine_severity(
        self,
        description: str,
        solution: Optional[str]
    ) -> str:
        """
        Determine error severity from description
        
        Returns:
            One of: low, medium, high, critical
        """
        text = f"{description} {solution or ''}".lower()
        
        # Critical keywords
        if any(kw in text for kw in ['critical', 'fatal', 'shutdown', 'stop']):
            return "critical"
        
        # High severity
        if any(kw in text for kw in ['major', 'serious', 'damage', 'failure']):
            return "high"
        
        # Low severity
        if any(kw in text for kw in ['minor', 'warning', 'informational', 'notice']):
            return "low"
        
        # Default to medium
        return "medium"
    
    def _deduplicate(
        self,
        error_codes: List[ExtractedErrorCode]
    ) -> List[ExtractedErrorCode]:
        """
        Remove duplicate error codes, keep highest confidence
        
        Args:
            error_codes: List of error codes
            
        Returns:
            Deduplicated list
        """
        if not error_codes:
            return []
        
        # Group by error_code
        seen = {}
        for ec in error_codes:
            key = ec.error_code
            if key not in seen or ec.confidence > seen[key].confidence:
                seen[key] = ec
        
        return list(seen.values())
    
    def validate_extraction(
        self,
        error_code: ExtractedErrorCode
    ) -> List[ValError]:
        """
        Validate extracted error code
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check format
        if not re.match(r'^\d{2}\.\d{2}(\.\d{2})?$', error_code.error_code):
            errors.append(ValError(
                field="error_code",
                value=error_code.error_code,
                error_message="Error code doesn't match XX.XX.XX format",
                severity="error"
            ))
        
        # Check description length
        if len(error_code.error_description) < 20:
            errors.append(ValError(
                field="error_description",
                value=error_code.error_description,
                error_message="Description too short (< 20 chars)",
                severity="warning"
            ))
        
        # Check confidence
        if error_code.confidence < 0.6:
            errors.append(ValError(
                field="confidence",
                value=error_code.confidence,
                error_message="Confidence below threshold (0.6)",
                severity="error"
            ))
        
        return errors


# Convenience function
def extract_error_codes_from_text(
    text: str,
    page_number: int
) -> List[ExtractedErrorCode]:
    """
    Convenience function to extract error codes from text
    
    Args:
        text: Text to extract from
        page_number: Page number
        
    Returns:
        List of validated error codes
    """
    extractor = ErrorCodeExtractor()
    return extractor.extract_from_text(text, page_number)
