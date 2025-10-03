"""
LLM-based Product & Specification Extraction

Uses local Ollama LLM for intelligent extraction.
"""

import json
from typing import List, Dict, Optional, Any
import requests
from pydantic import ValidationError

from .logger import get_logger
from .models import ExtractedProduct


class LLMProductExtractor:
    """Extract products and specifications using local LLM"""
    
    def __init__(
        self, 
        model_name: str = "qwen2.5:7b",
        ollama_url: str = "http://localhost:11434",
        debug: bool = False
    ):
        """
        Initialize LLM extractor
        
        Args:
            model_name: Ollama model to use (qwen2.5:7b, llama3.2, etc.)
            ollama_url: Ollama API endpoint
            debug: Enable debug logging
        """
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.debug = debug
        self.logger = get_logger()
    
    def extract_from_specification_section(
        self,
        text: str,
        manufacturer: str,
        page_number: int = 1
    ) -> List[ExtractedProduct]:
        """
        Extract products and specs from specification section
        
        Args:
            text: Text from specification section
            manufacturer: Manufacturer name
            page_number: Source page number
            
        Returns:
            List of extracted products with specifications
        """
        prompt = self._build_extraction_prompt(text, manufacturer)
        
        try:
            response = self._call_ollama(prompt)
            products = self._parse_llm_response(response, manufacturer, page_number)
            
            if self.debug:
                self.logger.debug(f"LLM extracted {len(products)} products with specs")
            
            return products
            
        except Exception as e:
            self.logger.error(f"LLM extraction failed: {e}")
            return []
    
    def _build_extraction_prompt(self, text: str, manufacturer: str) -> str:
        """Build extraction prompt for LLM"""
        
        prompt = f"""You are a technical documentation parser. Extract ALL products and their specifications from this {manufacturer} service manual section.

TEXT:
{text[:4000]}  # Limit context

TASK:
Extract products in JSON format with these fields:
- model_number: Product model (e.g., "C4080", "M455")
- product_series: Series name if mentioned (e.g., "AccurioPress", "LaserJet")
- max_print_speed_ppm: Print speed in pages per minute (integer)
- max_resolution_dpi: Maximum resolution (integer)
- max_paper_size: Largest paper size (e.g., "A3", "SRA3")
- duplex_capable: Can print duplex (true/false)
- dimensions_mm: Dimensions as {{"width": X, "depth": Y, "height": Z}}
- connectivity_options: List of connectivity (e.g., ["USB", "Ethernet", "WiFi"])
- specifications: Any other specs as key-value pairs

IMPORTANT:
- Return ONLY valid JSON array
- Include ALL models mentioned
- Extract numerical values without units (e.g., "80 ppm" -> 80)
- If spec not found, use null

OUTPUT FORMAT:
```json
[
  {{
    "model_number": "C4080",
    "product_series": "AccurioPress",
    "max_print_speed_ppm": 80,
    "max_resolution_dpi": 1200,
    "max_paper_size": "SRA3",
    "duplex_capable": true,
    "dimensions_mm": {{"width": 750, "depth": 850, "height": 1200}},
    "connectivity_options": ["USB", "Ethernet", "WiFi"],
    "specifications": {{"monthly_duty_cycle": "300000 pages"}}
  }}
]
```

JSON:"""
        
        return prompt
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API"""
        
        url = f"{self.ollama_url}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",  # Force JSON output
            "options": {
                "temperature": 0.1,  # Low temp for consistency
                "num_predict": 2000
            }
        }
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
    
    def _parse_llm_response(
        self,
        response: str,
        manufacturer: str,
        page_number: int
    ) -> List[ExtractedProduct]:
        """Parse LLM JSON response into ExtractedProduct objects"""
        
        products = []
        
        try:
            # Extract JSON from response (LLM might add markdown)
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            data = json.loads(json_str)
            
            # Handle both array and single object
            if isinstance(data, dict):
                data = [data]
            
            for item in data:
                try:
                    # Build specifications JSONB
                    specifications = {
                        k: v for k, v in item.items() 
                        if k not in ['model_number', 'product_series'] and v is not None
                    }
                    
                    product = ExtractedProduct(
                        model_number=item.get("model_number", ""),
                        product_series=item.get("product_series"),
                        product_type="printer",  # Default
                        manufacturer_name=manufacturer,
                        confidence=0.85,  # LLM extraction confidence
                        source_page=page_number,
                        extraction_method="llm",
                        specifications=specifications  # All specs in JSONB
                    )
                    products.append(product)
                    
                except ValidationError as e:
                    if self.debug:
                        self.logger.debug(f"Validation failed for item: {e}")
                    continue
        
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM JSON: {e}")
            if self.debug:
                self.logger.debug(f"Response was: {response[:500]}")
        
        return products
    
    def detect_specification_section(self, page_texts: Dict[int, str]) -> Optional[Dict[str, Any]]:
        """
        Detect if document has a specification section
        
        Returns:
            Dict with page_number and text if found, else None
        """
        keywords = [
            "product specification",
            "specifications",
            "technical specifications",
            "product features",
            "system specifications"
        ]
        
        for page_num, text in page_texts.items():
            text_lower = text.lower()
            for keyword in keywords:
                if keyword in text_lower:
                    # Extract section (next ~1000 chars)
                    start_idx = text_lower.index(keyword)
                    section_text = text[start_idx:start_idx + 3000]
                    
                    self.logger.info(f"Found specification section on page {page_num}")
                    return {
                        "page_number": page_num,
                        "text": section_text,
                        "keyword": keyword
                    }
        
        return None
