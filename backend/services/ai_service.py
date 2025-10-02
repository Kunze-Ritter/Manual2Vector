"""
AI Service for KR-AI-Engine
Ollama integration with hardware-optimized model selection
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import httpx

from config.ai_config import get_ai_config, get_ollama_models, get_model_requirements
from utils.gpu_detector import get_gpu_info, get_recommended_vision_model

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
        
        # Auto-detect GPU and select best vision model
        self.gpu_info = get_gpu_info()
        
        # Override vision model from env or use auto-detected
        env_vision_model = os.getenv('OLLAMA_MODEL_VISION')
        if env_vision_model:
            self.models['vision'] = env_vision_model
            self.logger.info(f"Using vision model from env: {env_vision_model}")
        else:
            self.models['vision'] = self.gpu_info['recommended_vision_model']
            self.logger.info(f"Auto-detected vision model: {self.models['vision']} (GPU: {self.gpu_info['gpu_name']}, VRAM: {self.gpu_info['vram_gb']:.1f}GB)")
        
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
            
            # For vision models, keep them loaded longer to avoid reload crashes
            if images:
                # Convert images to base64 for Ollama
                import base64
                images_b64 = [base64.b64encode(img).decode() for img in images]
                payload["images"] = images_b64
                # Keep vision model loaded for 10 minutes to avoid repeated loading/unloading
                payload["keep_alive"] = "10m"
            
            # Retry logic for vision models (they may crash due to VRAM)
            max_retries = 2 if images else 1
            retry_delay = 5  # seconds
            
            for attempt in range(max_retries):
                try:
                    response = await self.client.post(
                        f"{self.ollama_url}/api/generate",
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    else:
                        error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                        if attempt < max_retries - 1 and "resource limitations" in response.text:
                            self.logger.warning(f"{error_msg} - Retrying in {retry_delay}s...")
                            await asyncio.sleep(retry_delay)
                            continue
                        raise Exception(error_msg)
                except Exception as e:
                    if attempt < max_retries - 1 and "resource limitations" in str(e):
                        self.logger.warning(f"Attempt {attempt + 1} failed - Retrying in {retry_delay}s...")
                        await asyncio.sleep(retry_delay)
                        continue
                    raise
                
        except Exception as e:
            self.logger.error(f"Failed to call Ollama model {model}: {e}")
            # Try fallback models if primary model fails
            fallback_models = self._get_fallback_model(model)
            if fallback_models:
                for fallback in fallback_models:
                    try:
                        self.logger.info(f"Trying fallback model: {fallback}")
                        # Recursively call _call_ollama with the fallback model
                        payload = {
                            "model": fallback,
                            "prompt": prompt,
                            "stream": False,
                            **kwargs
                        }
                        if images:
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
                            raise Exception(f"Ollama API error: {response.status_code}")
                    except Exception as fallback_error:
                        self.logger.warning(f"Fallback model {fallback} also failed: {fallback_error}")
                        continue
            raise
    
    def _get_fallback_model(self, model: str) -> List[str]:
        """Get fallback models for when primary model fails"""
        fallbacks = {
            # Text classification fallbacks
            'llama3.2:latest': ['llama3.2:3b', 'llama3.1:8b'],
            'llama3.2:3b': ['llama3.1:8b'],
            
            # Embedding fallbacks  
            'embeddinggemma:latest': ['nomic-embed-text:latest'],
            
            # Vision fallbacks - DISABLED due to VRAM issues
            # If llava:7b fails, don't try larger models
            'llava:latest': ['llava:7b'],
            'llava:7b': [],  # No fallbacks - prevents trying larger models
            'bakllava:latest': [],
        }
        return fallbacks.get(model, [])
    
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
        # Check if vision processing is disabled
        if os.getenv('DISABLE_VISION_PROCESSING', 'false').lower() == 'true':
            self.logger.info("Vision processing disabled, using fallback analysis")
            return {
                "image_type": "diagram",
                "description": "Technical image (vision processing disabled)",
                "contains_text": False,
                "tags": ["technical"],
                "confidence": 0.5
            }
        
        # Skip SVG files - they crash the vision model
        if image.startswith(b'<svg') or image.startswith(b'<?xml'):
            self.logger.warning("Skipping SVG image (not supported by vision model)")
            return {
                "image_type": "diagram",
                "description": "SVG vector graphic (not analyzed)",
                "contains_text": False,
                "tags": ["svg", "vector"],
                "confidence": 0.5
            }
        
        try:
            model = self.models['vision']
            
            prompt = f"""
            Analyze this technical image and provide JSON with:
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
    
    async def extract_error_codes_from_image(self, image_url: str = None, image_bytes: bytes = None, 
                                           image_id: str = None, manufacturer: str = "Unknown") -> Dict[str, Any]:
        """
        Extract error codes from screenshot/image using Vision Model (LLaVA via Ollama)
        
        Args:
            image_url: URL to image (will be downloaded)
            image_bytes: Image content as bytes (alternative to URL)
            image_id: Image ID for reference
            manufacturer: Manufacturer name for context
            
        Returns:
            Dict with error_codes list and metadata
        """
        # Check if vision processing is disabled
        if os.getenv('DISABLE_VISION_PROCESSING', 'false').lower() == 'true':
            self.logger.info("Vision processing disabled via DISABLE_VISION_PROCESSING env var")
            return {"error_codes": [], "skipped": True, "reason": "Vision processing disabled"}
        
        try:
            model = self.models['vision']
            
            # Download image if URL provided
            if image_url and not image_bytes:
                try:
                    response = await self.client.get(image_url)
                    if response.status_code == 200:
                        image_bytes = response.content
                    else:
                        raise Exception(f"Failed to download image: {response.status_code}")
                except Exception as e:
                    self.logger.error(f"Failed to download image from {image_url}: {e}")
                    return {"error_codes": [], "error": str(e)}
            
            if not image_bytes:
                return {"error_codes": [], "error": "No image data provided"}
            
            # Skip SVG files - they crash the vision model
            if image_bytes.startswith(b'<svg') or image_bytes.startswith(b'<?xml'):
                self.logger.warning(f"Skipping SVG image (not supported by vision model)")
                return {"error_codes": [], "skipped": True, "reason": "SVG format not supported"}
            
            # Reduce image size if too large (Ollama has issues with large images)
            try:
                from PIL import Image
                import io
                
                img = Image.open(io.BytesIO(image_bytes))
                
                # Get image size
                width, height = img.size
                max_dimension = 1024  # Max 1024px for stability
                
                # Resize if too large
                if width > max_dimension or height > max_dimension:
                    # Calculate new size maintaining aspect ratio
                    if width > height:
                        new_width = max_dimension
                        new_height = int(height * (max_dimension / width))
                    else:
                        new_height = max_dimension
                        new_width = int(width * (max_dimension / height))
                    
                    self.logger.info(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Convert back to bytes
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG', optimize=True)
                    image_bytes = buffer.getvalue()
                    
            except Exception as resize_error:
                self.logger.warning(f"Failed to resize image, using original: {resize_error}")
            
            # Craft prompt for error code extraction
            prompt = f"""
            Analyze this technical screenshot or diagram for error codes and error messages.
            
            Manufacturer: {manufacturer}
            
            Extract all error codes visible in this image and return a JSON array with:
            [
              {{
                "code": "exact error code (e.g., 13.20.01, E001, SC542)",
                "description": "error description if visible",
                "solution": "solution text if visible in the image",
                "context": "surrounding text or context",
                "confidence": 0.0-1.0 (your confidence in this extraction)
              }}
            ]
            
            IMPORTANT:
            - Only extract ACTUAL error codes visible in the image
            - Include the error code exactly as shown (with dots, dashes, etc.)
            - If no error codes are visible, return an empty array []
            - Look for patterns like: XX.XX.XX, EXXX, SCXXX, XXX-XXX
            - Look at control panel displays, error screens, diagrams
            
            Return ONLY the JSON array, no other text.
            """
            
            # Call Ollama with vision model
            result = await self._call_ollama(model, prompt, images=[image_bytes])
            response_text = result.get('response', '[]')
            
            # Parse response
            try:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    error_codes = json.loads(json_match.group(0))
                else:
                    error_codes = json.loads(response_text)
            except json.JSONDecodeError:
                self.logger.warning(f"Failed to parse JSON from vision model response: {response_text[:200]}")
                error_codes = []
            
            self.logger.info(f"Extracted {len(error_codes)} error codes from image using {model}")
            
            return {
                "error_codes": error_codes,
                "model": model,
                "image_id": image_id,
                "manufacturer": manufacturer,
                "tokens_used": result.get('eval_count', 0) + result.get('prompt_eval_count', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract error codes from image: {e}")
            return {
                "error_codes": [],
                "error": str(e),
                "model": model if 'model' in locals() else "unknown"
            }
    
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
