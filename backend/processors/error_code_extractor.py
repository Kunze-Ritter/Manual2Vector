"""Error Code Extraction Module

Extracts error codes using manufacturer-specific patterns from JSON config.
"""

import re
import json
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from .logger import get_logger
from .models import ExtractedErrorCode, ValidationError as ValError
from .exceptions import ManufacturerPatternNotFoundError
from utils.hp_solution_filter import extract_hp_technician_solution, is_hp_multi_level_format


logger = get_logger()

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
    """Extract error codes using manufacturer-specific patterns"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize error code extractor with configuration"""
        self.logger = get_logger()
        
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "error_code_patterns.json"
        
        self.config_path = config_path
        self.patterns_config = self._load_config()
        self.extraction_rules = self.patterns_config.get("extraction_rules", {})
        
        logger.info(f"Loaded error code patterns for {len([k for k in self.patterns_config.keys() if k != 'extraction_rules'])} manufacturers")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load error code patterns configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            logger.warning(f"Error code patterns config not found: {self.config_path}")
            return {"extraction_rules": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in error code patterns config: {e}")
            return {"extraction_rules": {}}
    
    def _get_manufacturer_key(self, manufacturer_name: Optional[str]) -> Optional[str]:
        """Convert manufacturer name to config key"""
        if not manufacturer_name:
            return None
        
        # Normalize manufacturer name
        normalized = manufacturer_name.lower().replace(" ", "_").replace("-", "_")
        
        # Direct mapping
        mapping = {
            "hp": "hp",
            "hewlett_packard": "hp",
            "konica_minolta": "konica_minolta",
            "konica": "konica_minolta",
            "minolta": "konica_minolta",
            "canon": "canon",
            "ricoh": "ricoh",
            "xerox": "xerox",
            "lexmark": "lexmark",
            "brother": "brother",
            "epson": "epson",
            "fujifilm": "fujifilm",
            "riso": "riso",
            "sharp": "sharp",
            "kyocera": "kyocera",
            "toshiba": "toshiba",
            "oki": "oki"
        }
        
        # Check direct match
        if normalized in mapping:
            return mapping[normalized]
        
        # Check if any key is in the normalized name
        for key, value in mapping.items():
            if key in normalized:
                return value
        
        return None
    
    def enrich_error_codes_from_document(
        self,
        error_codes: List[ExtractedErrorCode],
        full_document_text: str,
        manufacturer_name: Optional[str] = None
    ) -> List[ExtractedErrorCode]:
        """
        Enrich error codes with full details from entire document
        
        For codes found in lists (e.g., "List of JAM code"), search the entire
        document for detailed sections with Classification, Cause, Measures.
        
        Args:
            error_codes: List of error codes to enrich
            full_document_text: Full text of entire document
            manufacturer_name: Manufacturer name
            
        Returns:
            Enriched error codes with full details
        """
        enriched_codes = []
        
        for error_code in error_codes:
            # Skip if already has good solution
            if error_code.solution_text and len(error_code.solution_text) > 100:
                enriched_codes.append(error_code)
                continue
            
            # Search entire document for this code
            code_pattern = re.escape(error_code.error_code)
            matches = list(re.finditer(rf'\b{code_pattern}\b', full_document_text))
            
            # Try each occurrence to find the detailed section
            best_description = error_code.error_description
            best_solution = error_code.solution_text
            best_confidence = error_code.confidence
            
            for match in matches:
                start_pos = match.start()
                end_pos = match.end()
                
                # Extract larger context (up to 3000 chars for detailed sections)
                context = self._extract_context(full_document_text, start_pos, end_pos, context_size=3000)
                
                # Try to extract structured description
                description = self._extract_description(full_document_text, end_pos, max_length=500)
                if description and len(description) > len(best_description):
                    best_description = description
                    best_confidence = min(0.95, best_confidence + 0.1)
                
                # Try to extract solution
                solution = self._extract_solution(context, full_document_text, end_pos)
                if solution and len(solution) > len(best_solution or ''):
                    best_solution = solution
                    best_confidence = min(0.95, best_confidence + 0.1)
            
            # Create enriched error code
            enriched_code = ExtractedErrorCode(
                error_code=error_code.error_code,
                error_description=best_description,
                solution_text=best_solution or "No solution found",
                context_text=error_code.context_text,
                confidence=best_confidence,
                page_number=error_code.page_number,
                extraction_method=f"{error_code.extraction_method}_enriched",
                severity_level=error_code.severity_level
            )
            enriched_codes.append(enriched_code)
        
        return enriched_codes
    
    def extract_from_text(
        self,
        text: str,
        page_number: int,
        manufacturer_name: Optional[str] = None
    ) -> List[ExtractedErrorCode]:
        """
        Extract error codes from text using manufacturer-specific patterns
        
        Args:
            text: Text to extract from
            page_number: Page number
            manufacturer_name: Manufacturer name for specific patterns
            
        Returns:
            List of validated error codes
        """
        if not text or len(text) < 20:
            return []
        
        # Determine which patterns to use
        manufacturer_key = self._get_manufacturer_key(manufacturer_name)
        patterns_to_use = []
        
        if manufacturer_key and manufacturer_key in self.patterns_config:
            # Use manufacturer-specific patterns ONLY (no generic fallback to avoid false positives like part numbers)
            patterns_to_use.append((manufacturer_key, self.patterns_config[manufacturer_key]))
            logger.debug(f"Using error code patterns for manufacturer: {manufacturer_key}")
        else:
            # NO generic fallback - raise clear error with instructions
            if manufacturer_name:
                raise ManufacturerPatternNotFoundError(
                    manufacturer=manufacturer_name,
                    stage="Error Code Extraction"
                )
            else:
                # No manufacturer specified at all - cannot extract
                logger.warning("No manufacturer specified for error code extraction - skipping")
                return []
        
        # Extract error codes
        found_codes = []
        seen_codes = set()
        
        for mfr_key, mfr_config in patterns_to_use:
            patterns = mfr_config.get("patterns", [])
            validation_regex = mfr_config.get("validation_regex")
            
            for pattern_str in patterns:
                try:
                    pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
                except re.error as e:
                    logger.error(f"Invalid regex pattern '{pattern_str}': {e}")
                    continue
                
                matches = pattern.finditer(text)
                
                for match in matches:
                    # Get code from first capture group
                    code = match.group(1) if match.groups() else match.group(0)
                    code = code.strip()
                    
                    # Validate code format
                    if validation_regex and not re.match(validation_regex, code):
                        continue
                    
                    # Skip duplicates
                    if code in seen_codes:
                        continue
                    
                    # Not a reject word
                    if code.lower() in REJECT_CODES:
                        continue
                    
                    # Extract context
                    context = self._extract_context(text, match.start(), match.end())
                    
                    # Validate context
                    if not self._validate_context(context):
                        continue
                    
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
                    min_confidence = self.extraction_rules.get("min_confidence", 0.70)
                    if confidence < min_confidence:
                        logger.debug(f"Skipping code '{code}' - confidence too low ({confidence:.2f})")
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
                            extraction_method=f"{mfr_key}_pattern",
                            severity_level=severity
                        )
                        found_codes.append(error_code)
                        seen_codes.add(code)
                    except Exception as e:
                        logger.debug(f"Validation failed for code '{code}': {e}")
        
        # Deduplicate and sort
        unique_codes = self._deduplicate(found_codes)
        unique_codes.sort(key=lambda x: x.confidence, reverse=True)
        
        # Apply max codes limit
        max_codes = self.extraction_rules.get("max_codes_per_page", 20)
        if len(unique_codes) > max_codes:
            logger.warning(f"Extracted {len(unique_codes)} error codes, limiting to {max_codes}")
            unique_codes = unique_codes[:max_codes]
        
        # Don't log per-page results - progress bar shows running count
        pass
        
        return unique_codes
    
    def _validate_context(self, context: str) -> bool:
        """Validate that context looks like an error code section"""
        context_lower = context.lower()
        
        # Check for required keywords
        required_keywords = self.extraction_rules.get("require_context_keywords", [])
        has_required = any(kw in context_lower for kw in required_keywords)
        
        # Check for excluded keywords
        excluded_keywords = self.extraction_rules.get("exclude_if_near", [])
        has_excluded = any(kw in context_lower for kw in excluded_keywords)
        
        return has_required and not has_excluded
    
    
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
        
        For Konica Minolta: Looks for 'Classification' section
        For others: Extracts text after error code
        
        Args:
            text: Full text
            code_end_pos: Position where error code ends
            max_length: Maximum description length
            
        Returns:
            Description or None
        """
        # Extract text after code
        remaining_text = text[code_end_pos:code_end_pos + max_length * 2]
        
        # Try to find structured sections (Konica Minolta format)
        classification_match = re.search(r'Classification\s*\n\s*(.+?)(?:\n\s*Cause|\n\s*Measures|$)', remaining_text, re.IGNORECASE | re.DOTALL)
        if classification_match:
            description = classification_match.group(1).strip()
            # Limit to max_length
            if len(description) > max_length:
                description = description[:max_length].rsplit(' ', 1)[0] + '...'
            return description
        
        # Fallback: Extract text after code (original logic)
        remaining_text = remaining_text[:max_length]
        
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
        
        Handles multiple formats:
        - "Recommended action for customers" (HP style)
        - "Solution:" sections
        - Numbered troubleshooting steps
        - Bullet point lists
        
        Returns:
            Solution text or None
        """
        # Extended text window for better extraction (increased for multi-page procedures)
        text_after = full_text[code_end_pos:code_end_pos + 5000]
        combined_text = context + "\n" + text_after
        
        # Pattern 1: HP/Manufacturer style "Recommended action" OR Konica Minolta "Measures/Correction"
        # Supports: 1., 1), Step 1, • bullets
        recommended_action_pattern = re.compile(
            r'(?:recommended\s+action|corrective\s+action|troubleshooting\s+steps?|service\s+procedure|procedure|remedy|repair\s+procedure|measures\s+to\s+take|correction)'
            r'(?:\s+for\s+(?:customers?|technicians?|agents?|users?|when\s+an\s+alert\s+occurs)?)?'
            r'\s*[\n:]+((?:(?:\d+[\.\)]|•|-|\*|step\s+\d+)\s+.{15,}[\n\r]?){1,})',
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )
        
        match = recommended_action_pattern.search(combined_text)
        if match:
            solution = match.group(1).strip()
            # Clean up and limit length
            lines = solution.split('\n')
            # Take up to 20 lines or until we hit a new section (increased for complex procedures)
            filtered_lines = []
            for line in lines[:20]:
                # Match main steps (1., 1)) AND sub-steps (  1), 2), a), etc.)
                if re.match(r'^(?:\s{0,4}\d+[\.\)]|•|-|\*|[a-z][\.\)])\s+', line):
                    filtered_lines.append(line.strip())
                elif filtered_lines and len(line.strip()) > 20:  # Continuation line
                    filtered_lines[-1] += ' ' + line.strip()
                elif filtered_lines and not line.strip():  # Empty line between steps - keep going
                    continue
                elif filtered_lines:  # Stop at section header
                    break
            if filtered_lines:
                return '\n'.join(filtered_lines)
        
        # Pattern 2: Standard "Solution:" or "Fix:" sections
        solution_keywords_pattern = re.compile(
            r'(?:solution|fix|remedy|resolution|procedure|action|steps?)'
            r'\s*[:]\s*(.{50,1500})',
            re.IGNORECASE | re.DOTALL
        )
        
        match = solution_keywords_pattern.search(combined_text)
        if match:
            solution = match.group(1).strip()
            # Extract until next section header or end
            end_patterns = [
                r'\n\s*(?:note|warning|caution|important|tip)',
                r'\n\s*[A-Z][a-z]+\s+[A-Z]',  # New section title
                r'\n\s*\d+\.\d+\s',  # Numbered section
            ]
            for pattern in end_patterns:
                section_end = re.search(pattern, solution, re.IGNORECASE)
                if section_end:
                    solution = solution[:section_end.start()]
                    break
            return solution[:1000].strip()  # Limit length
        
        # Pattern 3: Numbered steps without header (1., 1), 2), Step 1, ...)
        numbered_steps_pattern = re.compile(
            r'((?:(?:\d+[\.\)]|Step\s+\d+)\s+.{20,}[\n\r]?){2,})',
            re.MULTILINE | re.IGNORECASE
        )
        
        match = numbered_steps_pattern.search(text_after)
        if match:
            steps = match.group(1).strip()
            # Take up to 15 steps (increased for complex multi-step procedures)
            lines = [l.strip() for l in steps.split('\n') if l.strip()]
            step_lines = []
            for line in lines[:15]:
                if re.match(r'(?:\d+[\.\)]|Step\s+\d+)', line, re.IGNORECASE):
                    step_lines.append(line)
                elif step_lines and len(line) > 20:  # Continuation of previous step
                    step_lines[-1] += ' ' + line
            if len(step_lines) >= 2:
                return '\n'.join(step_lines)
        
        # Pattern 4: Bullet point lists
        bullet_pattern = re.compile(
            r'((?:(?:•|-|\*|–)\s+.{15,}[\n\r]?){2,})',
            re.MULTILINE
        )
        
        match = bullet_pattern.search(combined_text)
        if match:
            bullets = match.group(1).strip()
            lines = [l.strip() for l in bullets.split('\n') if l.strip()][:8]
            solution = '\n'.join(lines)
            
            # HP-specific: Filter to technician-only solution
            if is_hp_multi_level_format(combined_text):
                solution = extract_hp_technician_solution(solution)
            
            return solution
        
        # No solution found - check if HP format and extract technician section
        if is_hp_multi_level_format(combined_text):
            return extract_hp_technician_solution(combined_text)
        
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
