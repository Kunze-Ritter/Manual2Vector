"""
Product Model Extraction Module

Extracts product model numbers from PDFs with strict validation.
NO filenames, ONLY real product models!
"""

import re
from typing import List, Optional, Dict
from pathlib import Path

from .logger import get_logger
from .models import ExtractedProduct, ValidationError as ValError


logger = get_logger()


# HP Product Model Patterns
HP_PATTERNS = {
    'laserjet': re.compile(
        r'\b(?:Color\s+)?LaserJet\s+(?:Pro\s+|Enterprise\s+|Managed\s+)?'
        r'[A-Z]?\d{3,4}[a-z]{0,3}(?:\s*[a-z]{1,3})?\b',
        re.IGNORECASE
    ),
    'officejet': re.compile(
        r'\bOfficeJet\s+(?:Pro\s+)?[A-Z]?\d{3,4}[a-z]{0,3}\b',
        re.IGNORECASE
    ),
    'designjet': re.compile(
        r'\bDesignJet\s+[A-Z]?\d{3,4}[a-z]{0,3}\b',
        re.IGNORECASE
    ),
    'pagewide': re.compile(
        r'\bPageWide\s+(?:Pro\s+|Enterprise\s+)?[A-Z]?\d{3,4}[a-z]{0,3}\b',
        re.IGNORECASE
    ),
    'simple_model': re.compile(
        r'\b[EM]\d{3,4}[a-z]{0,2}\b'  # E877, M455, etc.
    ),
}

# Canon Patterns
CANON_PATTERNS = {
    'imagerunner': re.compile(
        r'\bimageRUNNER\s+(?:ADVANCE\s+)?[A-Z]?\d{3,4}[a-z]{0,3}\b',
        re.IGNORECASE
    ),
    'pixma': re.compile(
        r'\bPIXMA\s+[A-Z]{2}\d{3,4}\b',
        re.IGNORECASE
    ),
}

# Words to REJECT (not product models)
REJECT_WORDS = {
    'page', 'chapter', 'section', 'figure', 'table', 'error', 'code',
    'step', 'note', 'warning', 'caution', 'procedure', 'manual',
    'document', 'revision', 'version', 'edition', 'copyright',
    'trademark', 'contents', 'index', 'appendix', 'glossary',
    'troubleshooting', 'specifications', 'features', 'overview'
}


class ProductExtractor:
    """Extract product models with validation"""
    
    def __init__(self, manufacturer_name: str = "HP"):
        """
        Initialize product extractor
        
        Args:
            manufacturer_name: Manufacturer name (HP, Canon, etc.)
        """
        self.manufacturer_name = manufacturer_name
        self.logger = get_logger()
    
    def extract_from_text(
        self,
        text: str,
        page_number: int = 1
    ) -> List[ExtractedProduct]:
        """
        Extract product models from text
        
        Args:
            text: Text to extract from
            page_number: Page number (for metadata)
            
        Returns:
            List of validated ExtractedProduct
        """
        if not text or len(text) < 10:
            return []
        
        # Select patterns based on manufacturer
        if self.manufacturer_name.upper() == "HP":
            patterns = HP_PATTERNS
        elif self.manufacturer_name.upper() == "CANON":
            patterns = CANON_PATTERNS
        else:
            patterns = HP_PATTERNS  # Default to HP
        
        found_models = []
        
        for pattern_name, pattern in patterns.items():
            matches = pattern.finditer(text)
            
            for match in matches:
                model = match.group(0).strip()
                
                # Validate
                if self._validate_model(model):
                    # Calculate confidence
                    confidence = self._calculate_confidence(
                        model, text, match.start(), pattern_name
                    )
                    
                    # Determine product type
                    product_type = self._determine_product_type(model, pattern_name)
                    
                    try:
                        product = ExtractedProduct(
                            model_number=model,
                            model_name=model,  # Can be enhanced later
                            product_type=product_type,
                            manufacturer_name=self.manufacturer_name,
                            confidence=confidence,
                            source_page=page_number,
                            extraction_method=f"regex_{pattern_name}"
                        )
                        found_models.append(product)
                    except Exception as e:
                        self.logger.debug(
                            f"Validation failed for '{model}': {e}"
                        )
        
        # Deduplicate
        unique_models = self._deduplicate(found_models)
        
        if unique_models:
            self.logger.info(
                f"Extracted {len(unique_models)} products from page {page_number}"
            )
        
        return unique_models
    
    def extract_from_first_page(
        self,
        first_page_text: str
    ) -> Optional[ExtractedProduct]:
        """
        Extract primary product model from first page
        
        Args:
            first_page_text: Text from first page
            
        Returns:
            Primary product model or None
        """
        products = self.extract_from_text(first_page_text, page_number=1)
        
        if not products:
            return None
        
        # Return highest confidence product
        products.sort(key=lambda p: p.confidence, reverse=True)
        return products[0]
    
    def _validate_model(self, model: str) -> bool:
        """
        Validate that model is a real product, not garbage
        
        Returns:
            True if valid
        """
        # Length check
        if len(model) < 3 or len(model) > 50:
            return False
        
        # Not a reject word
        if model.lower() in REJECT_WORDS:
            return False
        
        # Must have both letters and numbers
        has_letter = any(c.isalpha() for c in model)
        has_digit = any(c.isdigit() for c in model)
        
        if not (has_letter and has_digit):
            return False
        
        # Must NOT look like a filename
        if any(char in model for char in ['.', '_', '/', '\\', ':', '*', '?']):
            return False
        
        # Not all caps filename pattern (e.g., "COLORLJM480M")
        if len(model) > 12 and model.isupper() and not ' ' in model:
            return False
        
        return True
    
    def _calculate_confidence(
        self,
        model: str,
        full_text: str,
        position: int,
        pattern_name: str
    ) -> float:
        """
        Calculate extraction confidence
        
        Returns:
            Confidence score (0.0 - 1.0)
        """
        confidence = 0.6  # Base confidence
        
        # Bonus for specific patterns
        if pattern_name in ['laserjet', 'officejet', 'designjet', 'pagewide']:
            confidence += 0.2  # High confidence for full product names
        
        # Bonus if appears multiple times
        appearances = full_text.count(model)
        if appearances > 1:
            confidence += 0.1
        if appearances > 3:
            confidence += 0.1
        
        # Bonus if near certain keywords
        context_start = max(0, position - 100)
        context_end = min(len(full_text), position + 100)
        context = full_text[context_start:context_end].lower()
        
        if any(kw in context for kw in ['model', 'product', 'printer', 'scanner']):
            confidence += 0.05
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def _determine_product_type(self, model: str, pattern_name: str) -> str:
        """
        Determine product type from model name
        
        Returns:
            One of: printer, scanner, multifunction, copier, plotter
        """
        model_lower = model.lower()
        
        if 'designjet' in model_lower:
            return "plotter"
        elif any(kw in model_lower for kw in ['mfp', 'multifunction', 'all-in-one']):
            return "multifunction"
        elif 'scanner' in model_lower:
            return "scanner"
        elif 'copier' in model_lower:
            return "copier"
        else:
            # Default to printer for LaserJet, OfficeJet, etc.
            return "printer"
    
    def _deduplicate(self, products: List[ExtractedProduct]) -> List[ExtractedProduct]:
        """
        Remove duplicate products, keep highest confidence
        
        Args:
            products: List of products
            
        Returns:
            Deduplicated list
        """
        if not products:
            return []
        
        # Group by model_number
        seen = {}
        for product in products:
            key = product.model_number.lower()
            if key not in seen or product.confidence > seen[key].confidence:
                seen[key] = product
        
        return list(seen.values())
    
    def validate_extraction(
        self,
        product: ExtractedProduct
    ) -> List[ValError]:
        """
        Validate extracted product
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check model number format
        if '.' in product.model_number or '_' in product.model_number:
            errors.append(ValError(
                field="model_number",
                value=product.model_number,
                error_message="Model number contains filename characters",
                severity="error"
            ))
        
        # Check confidence
        if product.confidence < 0.6:
            errors.append(ValError(
                field="confidence",
                value=product.confidence,
                error_message="Confidence below threshold (0.6)",
                severity="error"
            ))
        
        # Check product type
        valid_types = ['printer', 'scanner', 'multifunction', 'copier', 'plotter']
        if product.product_type not in valid_types:
            errors.append(ValError(
                field="product_type",
                value=product.product_type,
                error_message=f"Invalid product_type, must be one of {valid_types}",
                severity="error"
            ))
        
        return errors


# Convenience function
def extract_products_from_text(
    text: str,
    manufacturer: str = "HP",
    page_number: int = 1
) -> List[ExtractedProduct]:
    """
    Convenience function to extract products from text
    
    Args:
        text: Text to extract from
        manufacturer: Manufacturer name
        page_number: Page number
        
    Returns:
        List of validated products
    """
    extractor = ProductExtractor(manufacturer_name=manufacturer)
    return extractor.extract_from_text(text, page_number)
