"""
AI Service for KR-AI-Engine
Ollama integration with hardware-optimized model selection
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import httpx

from config.ai_config import get_ai_config, get_ollama_models, get_model_requirements

class AIService:
    """
    AI service for Ollama integration with hardware detection
    
    Handles AI operations for KR-AI-Engine:
    - Text Classification (llama3.2:latest)
    - Embeddings (embeddinggemma:latest) 
    - Vision (llava:latest)
    - GPU Acceleration (RTX 2000 + 8GB VRAM)
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.client = None
        self.logger = logging.getLogger("krai.ai")
        self._setup_logging()
        
        # Get hardware-optimized configuration
        self.config = get_ai_config()
        self.models = get_ollama_models()
        self.requirements = get_model_requirements()
        
        self.logger.info(f"AI Service initialized with {self.config.tier.value} tier")
        self.logger.info(f"Models: {self.models}")
        self.logger.info(f"GPU Acceleration: {self.config.gpu_acceleration}")
    
    def _setup_logging(self):
        """Setup logging for AI service"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - AI - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def connect(self):
        """Connect to Ollama service"""
        try:
            self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout for large models
            
            # Test connection
            await self.test_connection()
            
            self.logger.info("Connected to Ollama service")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Ollama: {e}")
            raise
    
    async def test_connection(self):
        """Test Ollama connection"""
        try:
            response = await self.client.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                self.logger.info(f"Ollama connection successful. Available models: {len(models)}")
            else:
                raise Exception(f"Ollama API returned status {response.status_code}")
        except Exception as e:
            self.logger.error(f"Ollama connection test failed: {e}")
            raise
    
    async def _call_ollama(self, model: str, prompt: str, images: List[bytes] = None, **kwargs) -> Dict[str, Any]:
        """Call Ollama API with model"""
        try:
            if self.client is None:
                # Mock mode for testing
                self.logger.info(f"Using mock Ollama response for model {model}")
                return {
                    'response': 'Mock AI response for testing',
                    'model': model,
                    'created_at': '2024-01-01T00:00:00Z',
                    'done': True
                }
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }
            
            if images:
                # Convert images to base64 for Ollama
                import base64
                images_b64 = [base64.b64encode(img).decode() for img in images]
                payload["images"] = images_b64
            
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"Failed to call Ollama model {model}: {e}")
            raise
    
    async def classify_document(self, text: str, filename: str = None) -> Dict[str, Any]:
        """
        Classify document type using text classification model
        
        Args:
            text: Document text content
            filename: Optional filename for context
            
        Returns:
            Classification result
        """
        try:
            model = self.models['text_classification']
            
            prompt = f"""
            Analyze this technical document and classify it. Return a JSON response with:
            - document_type: service_manual, parts_catalog, technical_bulletin, cpmd_database, user_manual, installation_guide, troubleshooting_guide
            - manufacturer: Exact manufacturer name (HP Inc., Konica Minolta, Canon Inc., Lexmark International, etc.)
            - series: product series name (LaserJet Pro, Bizhub C, imageCLASS LBP, etc.)
            - models: ALL model numbers found in the document (not just filename) - include variations, options, and related models
            - options: any option numbers or accessory models mentioned
            - version: document version if found
            - confidence: confidence score 0-1
            - language: document language
            
            IMPORTANT: 
            - Extract ALL models mentioned in the document, not just the main model
            - Include option models and accessory models
            - Look for model patterns like M404dn, M404n, M404dw, etc.
            - Include any model variations or related models
            
            Document text: {text[:3000]}...
            """
            
            if filename:
                prompt += f"\nFilename: {filename}"
            
            result = await self._call_ollama(model, prompt)
            response_text = result.get('response', '{}')
            
            # Parse JSON response
            try:
                classification = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                classification = {
                    "document_type": "service_manual",
                    "manufacturer": "Unknown",
                    "series": "Unknown",
                    "models": [],
                    "version": "1.0",
                    "confidence": 0.5,
                    "language": "en"
                }
            
            self.logger.info(f"Document classified: {classification['document_type']} ({classification['manufacturer']})")
            return classification
            
        except Exception as e:
            self.logger.error(f"Failed to classify document: {e}")
            raise
    
    async def extract_features(self, text: str, manufacturer: str, series: str) -> Dict[str, Any]:
        """
        Extract product features from document text
        
        Args:
            text: Document text content
            manufacturer: Manufacturer name
            series: Product series name
            
        Returns:
            Features extraction result
        """
        try:
            model = self.models['text_classification']
            
            prompt = f"""
            Extract product features from this technical document. Return a JSON response with:
            - series_features: global features for the product series (JSON object)
            - product_features: model-specific features (JSON object)
            - key_features: list of key features
            - target_market: target market segment
            - price_range: price range category
            
            Manufacturer: {manufacturer}
            Series: {series}
            
            Document text: {text[:3000]}...
            """
            
            result = await self._call_ollama(model, prompt)
            response_text = result.get('response', '{}')
            
            try:
                features = json.loads(response_text)
            except json.JSONDecodeError:
                features = {
                    "series_features": {},
                    "product_features": {},
                    "key_features": [],
                    "target_market": "Unknown",
                    "price_range": "Unknown"
                }
            
            self.logger.info(f"Features extracted for {manufacturer} {series}")
            return features
            
        except Exception as e:
            self.logger.error(f"Failed to extract features: {e}")
            raise
    
    async def extract_error_codes(self, text: str, manufacturer: str) -> List[Dict[str, Any]]:
        """
        Extract error codes from document text
        
        Args:
            text: Document text content
            manufacturer: Manufacturer name
            
        Returns:
            List of error codes
        """
        try:
            model = self.models['text_classification']
            
            prompt = f"""
            Extract error codes from this technical document. Return a JSON array with:
            - error_code: the error code
            - description: error description
            - solution: solution text
            - page_number: page where found
            - confidence: confidence score 0-1
            - severity: low, medium, high
            
            Manufacturer: {manufacturer}
            
            Document text: {text[:4000]}...
            """
            
            result = await self._call_ollama(model, prompt)
            response_text = result.get('response', '[]')
            
            try:
                error_codes = json.loads(response_text)
            except json.JSONDecodeError:
                error_codes = []
            
            self.logger.info(f"Extracted {len(error_codes)} error codes for {manufacturer}")
            return error_codes
            
        except Exception as e:
            self.logger.error(f"Failed to extract error codes: {e}")
            raise
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings for text using embedding model
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (768-dimensional)
        """
        try:
            if self.client is None:
                # Mock mode for testing
                self.logger.info("Using mock embeddings for testing")
                return [0.1] * 768  # Mock 768-dimensional embedding
            
            model = self.models['embeddings']
            
            # Use Ollama's embedding endpoint
            response = await self.client.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": model,
                    "prompt": text
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get('embedding', [])
                
                self.logger.info(f"Generated embedding with {len(embedding)} dimensions")
                return embedding
            else:
                raise Exception(f"Embedding API error: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    async def analyze_image(self, image: bytes, description: str = None) -> Dict[str, Any]:
        """
        Analyze image using vision model
        
        Args:
            image: Image content as bytes
            description: Optional description of what to analyze
            
        Returns:
            Image analysis result
        """
        try:
            model = self.models['vision']
            
            prompt = f"""
            Analyze this technical image and provide:
            - image_type: diagram, screenshot, photo, chart, schematic, flowchart
            - description: detailed description of the image
            - contains_text: whether the image contains text
            - ocr_text: extracted text if any
            - tags: relevant tags for the image
            - confidence: confidence score 0-1
            
            {description or "Analyze this technical image"}
            """
            
            result = await self._call_ollama(model, prompt, images=[image])
            response_text = result.get('response', '{}')
            
            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                analysis = {
                    "image_type": "photo",
                    "description": "Technical image",
                    "contains_text": False,
                    "ocr_text": "",
                    "tags": [],
                    "confidence": 0.5
                }
            
            self.logger.info(f"Image analyzed: {analysis['image_type']} (confidence: {analysis['confidence']})")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze image: {e}")
            raise
    
    async def detect_defects(self, image: bytes, description: str = None) -> Dict[str, Any]:
        """
        Detect defects in image for defect detection system
        
        Args:
            image: Image content as bytes
            description: Optional description of the defect
            
        Returns:
            Defect detection result
        """
        try:
            model = self.models['vision']
            
            prompt = f"""
            Analyze this image for printer defects and provide:
            - defect_type: type of defect (paper_jam, toner_issue, mechanical, etc.)
            - confidence: confidence score 0-1
            - suggested_solutions: list of solutions
            - estimated_fix_time: estimated time to fix
            - required_parts: list of parts needed
            - difficulty_level: easy, medium, hard
            - related_error_codes: list of related error codes
            
            {description or "Detect any defects in this printer image"}
            """
            
            result = await self._call_ollama(model, prompt, images=[image])
            response_text = result.get('response', '{}')
            
            try:
                defects = json.loads(response_text)
            except json.JSONDecodeError:
                defects = {
                    "defect_type": "unknown",
                    "confidence": 0.0,
                    "suggested_solutions": [],
                    "estimated_fix_time": "Unknown",
                    "required_parts": [],
                    "difficulty_level": "easy",
                    "related_error_codes": []
                }
            
            self.logger.info(f"Defect detected: {defects['defect_type']} (confidence: {defects['confidence']})")
            return defects
            
        except Exception as e:
            self.logger.error(f"Failed to detect defects: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform AI service health check"""
        try:
            start_time = datetime.utcnow()
            
            # Test basic model availability
            response = await self.client.get(f"{self.ollama_url}/api/tags")
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                return {
                    "status": "healthy",
                    "response_time_ms": response_time * 1000,
                    "available_models": available_models,
                    "configured_models": self.models,
                    "gpu_acceleration": self.config.gpu_acceleration,
                    "tier": self.config.tier.value,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"Ollama API returned status {response.status_code}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
