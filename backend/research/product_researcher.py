"""
AI-Powered Product Researcher
==============================

Automatically researches products online to extract:
- Product specifications
- Series information
- OEM relationships
- Lifecycle data

Uses:
- Web search (Tavily API or SerpAPI)
- Web scraping (BeautifulSoup)
- LLM analysis (Ollama)
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class ProductResearcher:
    """
    AI-powered product researcher that extracts specs from manufacturer websites
    """
    
    def __init__(
        self,
        supabase=None,
        ollama_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b",
        cache_days: int = 90
    ):
        """
        Initialize researcher
        
        Args:
            supabase: Supabase client
            ollama_url: Ollama API URL
            model: LLM model to use
            cache_days: Days to cache research results
        """
        self.supabase = supabase
        self.ollama_url = ollama_url
        self.model = model
        self.cache_days = cache_days
        
        # Search API (Tavily preferred, fallback to direct search)
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        self.use_tavily = bool(self.tavily_api_key)
        
        logger.info(f"ProductResearcher initialized (search: {'Tavily' if self.use_tavily else 'Direct'})")
    
    def research_product(
        self,
        manufacturer: str,
        model_number: str,
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Research product online and extract specifications
        
        Args:
            manufacturer: Manufacturer name
            model_number: Model number
            force_refresh: Force new research (ignore cache)
            
        Returns:
            Dictionary with research results or None
        """
        logger.info(f"Researching: {manufacturer} {model_number}")
        
        # Check cache first
        if not force_refresh and self.supabase:
            cached = self._get_cached_research(manufacturer, model_number)
            if cached:
                logger.info(f"✓ Using cached research (confidence: {cached.get('confidence', 0):.2f})")
                return cached
        
        # Step 1: Web search
        search_results = self._web_search(manufacturer, model_number)
        if not search_results:
            logger.warning(f"No search results found for {manufacturer} {model_number}")
            return None
        
        # Step 2: Scrape content
        scraped_content = self._scrape_urls(search_results['urls'][:3])  # Top 3 results
        if not scraped_content:
            logger.warning(f"Could not scrape content for {manufacturer} {model_number}")
            return None
        
        # Step 3: LLM analysis
        analysis = self._llm_analyze(
            manufacturer=manufacturer,
            model_number=model_number,
            content=scraped_content,
            source_urls=search_results['urls']
        )
        
        if not analysis:
            logger.warning(f"LLM analysis failed for {manufacturer} {model_number}")
            return None
        
        # Step 4: Save to cache
        if self.supabase:
            self._save_to_cache(manufacturer, model_number, analysis)
        
        logger.info(f"✓ Research complete (confidence: {analysis.get('confidence', 0):.2f})")
        return analysis
    
    def _get_cached_research(self, manufacturer: str, model_number: str) -> Optional[Dict]:
        """Get cached research results"""
        try:
            result = self.supabase.rpc(
                'get_cached_research',
                {'p_manufacturer': manufacturer, 'p_model_number': model_number}
            ).execute()
            
            if result.data:
                return result.data
            return None
        except Exception as e:
            logger.debug(f"Cache lookup failed: {e}")
            return None
    
    def _web_search(self, manufacturer: str, model_number: str) -> Optional[Dict]:
        """
        Search web for product information
        
        Returns:
            Dict with 'urls' and 'snippets'
        """
        query = f"{manufacturer} {model_number} specifications datasheet"
        
        if self.use_tavily:
            return self._tavily_search(query)
        else:
            return self._direct_search(query, manufacturer)
    
    def _tavily_search(self, query: str) -> Optional[Dict]:
        """Search using Tavily API"""
        try:
            response = requests.post(
                'https://api.tavily.com/search',
                json={
                    'api_key': self.tavily_api_key,
                    'query': query,
                    'max_results': 5,
                    'include_raw_content': False
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'urls': [r['url'] for r in data.get('results', [])],
                    'snippets': [r.get('content', '') for r in data.get('results', [])]
                }
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
        
        return None
    
    def _direct_search(self, query: str, manufacturer: str) -> Optional[Dict]:
        """
        Direct search (construct URLs based on manufacturer)
        
        This is a fallback when no search API is available
        """
        # Common manufacturer website patterns
        manufacturer_domains = {
            'konica minolta': 'konicaminolta.com',
            'hp': 'hp.com',
            'canon': 'canon.com',
            'xerox': 'xerox.com',
            'ricoh': 'ricoh.com',
            'lexmark': 'lexmark.com',
            'brother': 'brother.com',
            'epson': 'epson.com',
            'kyocera': 'kyocera.com',
            'sharp': 'sharp.com',
            'toshiba': 'toshiba.com',
            'oki': 'oki.com',
        }
        
        manufacturer_lower = manufacturer.lower()
        domain = manufacturer_domains.get(manufacturer_lower)
        
        if not domain:
            logger.warning(f"No known domain for manufacturer: {manufacturer}")
            return None
        
        # Construct likely URLs
        model_clean = re.sub(r'[^a-zA-Z0-9-]', '', query.split()[-1].lower())
        urls = [
            f"https://www.{domain}/products/{model_clean}",
            f"https://www.{domain}/en/products/{model_clean}",
            f"https://www.{domain}/us/products/{model_clean}",
        ]
        
        return {
            'urls': urls,
            'snippets': []
        }
    
    def _scrape_urls(self, urls: List[str]) -> str:
        """
        Scrape content from URLs
        
        Returns:
            Combined text content
        """
        all_content = []
        
        for url in urls:
            try:
                logger.debug(f"Scraping: {url}")
                response = requests.get(
                    url,
                    timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Get text
                text = soup.get_text(separator='\n', strip=True)
                
                # Clean up
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                text = '\n'.join(lines)
                
                # Limit length
                if len(text) > 10000:
                    text = text[:10000]
                
                all_content.append(text)
                
            except Exception as e:
                logger.debug(f"Failed to scrape {url}: {e}")
                continue
        
        return '\n\n---\n\n'.join(all_content)
    
    def _llm_analyze(
        self,
        manufacturer: str,
        model_number: str,
        content: str,
        source_urls: List[str]
    ) -> Optional[Dict]:
        """
        Analyze scraped content with LLM
        
        Returns:
            Dictionary with extracted information
        """
        prompt = f"""You are a technical product analyst. Analyze the following content about a printer/MFP product and extract structured information.

Product: {manufacturer} {model_number}

Content:
{content[:8000]}

Extract the following information in JSON format:

{{
    "series_name": "Product series name (e.g., 'bizhub i-Series', 'LaserJet Pro')",
    "series_description": "Brief description of the series",
    "product_type": "One of: laser_printer, inkjet_printer, laser_multifunction, inkjet_multifunction, production_printer, etc.",
    "specifications": {{
        "speed_mono": 75,  // Pages per minute (mono)
        "speed_color": 75,  // Pages per minute (color)
        "resolution": "1200x1200 dpi",
        "paper_sizes": ["A4", "A3", "Letter"],
        "duplex": "automatic",  // or "manual" or "none"
        "memory": "8192 MB",
        "storage": "256 GB SSD",
        "connectivity": ["USB 2.0", "Ethernet", "WiFi"],
        "scan_speed": "240 ipm",
        "monthly_duty": 300000
    }},
    "physical_specs": {{
        "dimensions": {{"width": 615, "depth": 685, "height": 1193, "unit": "mm"}},
        "weight": 145.5,
        "weight_unit": "kg",
        "power_consumption": 1500,
        "power_unit": "W"
    }},
    "oem_manufacturer": "OEM manufacturer if rebrand (or null)",
    "oem_notes": "Notes about OEM relationship",
    "launch_year": 2023,
    "confidence": 0.85  // Your confidence in this analysis (0.0-1.0)
}}

IMPORTANT:
- Only include information you find in the content
- Use null for missing information
- Be conservative with confidence score
- Focus on technical specifications

Return ONLY the JSON, no other text.
"""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.1,  # Low temperature for factual extraction
                        'num_predict': 2000
                    }
                },
                timeout=120
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code}")
                return None
            
            result = response.json()
            response_text = result.get('response', '')
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                logger.error("No JSON found in LLM response")
                return None
            
            analysis = json.loads(json_match.group())
            
            # Add metadata
            analysis['source_urls'] = source_urls
            analysis['research_date'] = datetime.now().isoformat()
            
            return analysis
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return None
    
    def _save_to_cache(self, manufacturer: str, model_number: str, analysis: Dict):
        """Save research results to cache"""
        try:
            data = {
                'manufacturer': manufacturer,
                'model_number': model_number,
                'series_name': analysis.get('series_name'),
                'series_description': analysis.get('series_description'),
                'specifications': analysis.get('specifications', {}),
                'physical_specs': analysis.get('physical_specs', {}),
                'oem_manufacturer': analysis.get('oem_manufacturer'),
                'oem_notes': analysis.get('oem_notes'),
                'product_type': analysis.get('product_type'),
                'launch_date': f"{analysis.get('launch_year')}-01-01" if analysis.get('launch_year') else None,
                'confidence': analysis.get('confidence', 0.0),
                'source_urls': analysis.get('source_urls', []),
                'cache_valid_until': (datetime.now() + timedelta(days=self.cache_days)).isoformat(),
                'verified': False
            }
            
            # Upsert (insert or update)
            self.supabase.table('product_research_cache').upsert(
                data,
                on_conflict='manufacturer,model_number'
            ).execute()
            
            logger.info(f"✓ Saved research to cache")
            
        except Exception as e:
            logger.error(f"Failed to save to cache: {e}")


if __name__ == '__main__':
    # Test mode
    import sys
    from supabase import create_client
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Initialize
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None
    
    researcher = ProductResearcher(supabase=supabase)
    
    # Test cases
    test_products = [
        ("Konica Minolta", "C750i"),
        ("HP", "LaserJet Pro M454dw"),
        ("Canon", "imageRUNNER ADVANCE C5550i"),
    ]
    
    if len(sys.argv) > 2:
        # Command line: python product_researcher.py "Konica Minolta" "C750i"
        manufacturer = sys.argv[1]
        model = sys.argv[2]
        test_products = [(manufacturer, model)]
    
    for manufacturer, model in test_products:
        print(f"\n{'='*80}")
        print(f"Researching: {manufacturer} {model}")
        print('='*80)
        
        result = researcher.research_product(manufacturer, model)
        
        if result:
            print(f"\n✅ Research successful!")
            print(f"Confidence: {result.get('confidence', 0):.2f}")
            print(f"\nSeries: {result.get('series_name')}")
            print(f"Type: {result.get('product_type')}")
            print(f"\nSpecifications:")
            print(json.dumps(result.get('specifications', {}), indent=2))
        else:
            print(f"\n❌ Research failed")
