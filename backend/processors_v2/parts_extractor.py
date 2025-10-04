"""
Parts Extractor - Extract spare parts from parts catalogs using manufacturer-specific patterns
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from .models import ExtractedPart


class PartsExtractor:
    """Extract spare parts from documents using pattern matching"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize parts extractor with configuration
        
        Args:
            config_path: Path to parts_patterns.json config file
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "parts_patterns.json"
        
        self.config_path = config_path
        self.patterns_config = self._load_config()
        self.extraction_rules = self.patterns_config.get("extraction_rules", {})
        
        logger.info(f"Loaded parts patterns for {len(self.patterns_config) - 1} manufacturers")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load parts patterns configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            logger.warning(f"Parts patterns config not found: {self.config_path}")
            return {"extraction_rules": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in parts patterns config: {e}")
            return {"extraction_rules": {}}
    
    def extract_parts(
        self, 
        text: str, 
        manufacturer_name: Optional[str] = None,
        page_number: Optional[int] = None
    ) -> List[ExtractedPart]:
        """
        Extract parts from text using manufacturer-specific patterns
        
        Args:
            text: Text to extract parts from
            manufacturer_name: Manufacturer name to use specific patterns
            page_number: Page number for context
            
        Returns:
            List of ExtractedPart objects
        """
        if not text or len(text.strip()) < 10:
            return []
        
        # Determine which patterns to use
        manufacturer_key = self._get_manufacturer_key(manufacturer_name)
        patterns_to_use = []
        
        if manufacturer_key and manufacturer_key in self.patterns_config:
            # Use manufacturer-specific patterns first
            patterns_to_use.append((manufacturer_key, self.patterns_config[manufacturer_key]))
            logger.debug(f"Using patterns for manufacturer: {manufacturer_key}")
        
        # Always add generic patterns as fallback
        if "generic" in self.patterns_config:
            patterns_to_use.append(("generic", self.patterns_config["generic"]))
        
        # Extract parts
        extracted_parts = []
        seen_part_numbers = set()
        
        for mfr_key, mfr_config in patterns_to_use:
            patterns = mfr_config.get("patterns", [])
            
            for pattern_config in patterns:
                parts = self._extract_with_pattern(
                    text=text,
                    pattern_config=pattern_config,
                    manufacturer_name=manufacturer_name or mfr_config.get("manufacturer_name"),
                    page_number=page_number
                )
                
                for part in parts:
                    # Deduplicate by part number
                    if part.part_number not in seen_part_numbers:
                        seen_part_numbers.add(part.part_number)
                        extracted_parts.append(part)
        
        # Sort by confidence
        extracted_parts.sort(key=lambda p: p.confidence, reverse=True)
        
        # Apply max parts limit
        max_parts = self.extraction_rules.get("max_parts_per_page", 50)
        if len(extracted_parts) > max_parts:
            logger.warning(f"Extracted {len(extracted_parts)} parts, limiting to {max_parts}")
            extracted_parts = extracted_parts[:max_parts]
        
        logger.info(f"Extracted {len(extracted_parts)} unique parts from text")
        return extracted_parts
    
    def _get_manufacturer_key(self, manufacturer_name: Optional[str]) -> Optional[str]:
        """Convert manufacturer name to config key"""
        if not manufacturer_name:
            return None
        
        # Normalize manufacturer name
        normalized = manufacturer_name.lower().replace(" ", "_").replace("-", "_")
        
        # Direct mapping for common cases
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
    
    def _extract_with_pattern(
        self,
        text: str,
        pattern_config: Dict[str, Any],
        manufacturer_name: Optional[str],
        page_number: Optional[int]
    ) -> List[ExtractedPart]:
        """Extract parts using a specific pattern"""
        pattern = pattern_config.get("pattern")
        pattern_name = pattern_config.get("name")
        base_confidence = pattern_config.get("confidence", 0.75)
        
        if not pattern:
            return []
        
        try:
            regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
            return []
        
        parts = []
        context_window = self.extraction_rules.get("context_window_chars", 200)
        
        for match in regex.finditer(text):
            part_number = match.group(0).strip()
            
            # Get context around match
            start = max(0, match.start() - context_window // 2)
            end = min(len(text), match.end() + context_window // 2)
            context = text[start:end].strip()
            
            # Validate context
            if not self._validate_context(context):
                continue
            
            # Extract additional info from context
            part_name, part_description = self._extract_part_info(context, part_number)
            
            # Adjust confidence based on context
            confidence = self._calculate_confidence(
                base_confidence=base_confidence,
                context=context,
                has_name=bool(part_name),
                has_description=bool(part_description)
            )
            
            # Skip if confidence too low
            min_confidence = self.extraction_rules.get("min_confidence", 0.70)
            if confidence < min_confidence:
                continue
            
            part = ExtractedPart(
                part_number=part_number,
                part_name=part_name,
                part_description=part_description,
                part_category=self._infer_category(context, pattern_name),
                manufacturer_name=manufacturer_name,
                confidence=confidence,
                pattern_name=pattern_name,
                page_number=page_number,
                context=context[:500]  # Limit context length
            )
            
            parts.append(part)
        
        return parts
    
    def _validate_context(self, context: str) -> bool:
        """Validate that context looks like a parts catalog entry"""
        context_lower = context.lower()
        
        # Check for required keywords
        required_keywords = self.extraction_rules.get("require_context_keywords", [])
        has_required = any(kw in context_lower for kw in required_keywords)
        
        # Check for excluded keywords (like "page", "figure", etc.)
        excluded_keywords = self.extraction_rules.get("exclude_if_near", [])
        has_excluded = any(kw in context_lower for kw in excluded_keywords)
        
        return has_required and not has_excluded
    
    def _extract_part_info(self, context: str, part_number: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract part name and description from context"""
        # Simple heuristic: text after part number is likely the description
        lines = context.split('\n')
        part_name = None
        part_description = None
        
        for i, line in enumerate(lines):
            if part_number in line:
                # Name is often on the same line or next line
                remaining = line.split(part_number, 1)[1].strip()
                if remaining and len(remaining) > 3:
                    part_name = remaining[:255]
                
                # Description might be on next lines
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and len(next_line) > 10:
                        part_description = next_line[:500]
                
                break
        
        return part_name, part_description
    
    def _calculate_confidence(
        self,
        base_confidence: float,
        context: str,
        has_name: bool,
        has_description: bool
    ) -> float:
        """Calculate final confidence score"""
        confidence = base_confidence
        
        # Boost if has additional info
        if has_name:
            confidence = min(1.0, confidence + 0.05)
        if has_description:
            confidence = min(1.0, confidence + 0.03)
        
        # Boost if context has part indicators
        context_lower = context.lower()
        part_indicators = self.extraction_rules.get("part_number_indicators", [])
        if any(indicator in context_lower for indicator in part_indicators):
            confidence = min(1.0, confidence + 0.05)
        
        return round(confidence, 2)
    
    def _infer_category(self, context: str, pattern_name: Optional[str]) -> Optional[str]:
        """Infer part category from context and pattern"""
        context_lower = context.lower()
        
        # Check pattern name first
        if pattern_name:
            if "toner" in pattern_name:
                return "toner_cartridge"
            elif "drum" in pattern_name:
                return "drum_unit"
            elif "fuser" in pattern_name:
                return "fuser_assembly"
            elif "maintenance" in pattern_name:
                return "maintenance_kit"
            elif "ink" in pattern_name:
                return "ink_cartridge"
        
        # Check consumable types in context
        consumable_types = self.extraction_rules.get("consumable_types", [])
        for consumable in consumable_types:
            if consumable in context_lower:
                return consumable.replace(" ", "_")
        
        return None
