"""
AI-Powered Metadata & Error Code Extraction Processor
Uses GPT-4 Vision for screenshot-based error code extraction
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult, ProcessingError
from core.data_models import ErrorCodeModel

class MetadataProcessorAI(BaseProcessor):
    """
    AI-Powered Metadata Processor - Stage 5
    
    Capabilities:
    - Pattern-based error code extraction (regex)
    - AI-powered error code extraction from screenshots (GPT-4 Vision)
    - Context-aware extraction
    - Confidence scoring
    - Duplicate detection
    """
    
    def __init__(self, database_service, ai_service=None, config_service=None):
        super().__init__("metadata_processor_ai")
        self.database_service = database_service
        self.ai_service = ai_service
        self.config_service = config_service
        
        # Standard error code patterns
        self.error_patterns = {
            'hp': [
                r'\b\d{2}\.\d{2}\.\d{2}\b',  # 13.20.01
                r'\bE\d{3,4}\b',  # E001
                r'\b\d{2}\s+\d{2}\b',  # 13 20
            ],
            'canon': [
                r'\b[E]\d{3,4}[-]\d{4}\b',  # E000-0000
                r'\b\d{4}\b',  # 1234
            ],
            'xerox': [
                r'\b\d{3}[-]\d{3}\b',  # 016-720
                r'\b\d{3}\s+\d{3}\b',  # 016 720
            ],
            'ricoh': [
                r'\bSC\d{3,4}\b',  # SC542
                r'\b[A-Z]\d{2}-\d{2}\b',  # J21-01
            ],
            'generic': [
                r'\berror\s+code[:\s]+([A-Z0-9\-\.]+)\b',
                r'\bcode[:\s]+([A-Z0-9\-\.]+)\b',
            ]
        }
    
    def get_required_inputs(self) -> List[str]:
        return ['document_id', 'file_path']
    
    def get_outputs(self) -> List[str]:
        return ['error_codes_found', 'error_code_ids', 'ai_extracted_count']
    
    def get_output_tables(self) -> List[str]:
        return ['krai_intelligence.error_codes']
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'cpu_intensive': True,
            'memory_intensive': False,
            'gpu_required': False,
            'estimated_ram_gb': 1.0,
            'parallel_safe': True
        }
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """Extract error codes using pattern matching + AI"""
        try:
            # Get document
            document = await self.database_service.get_document(context.document_id)
            if not document:
                raise ProcessingError("Document not found", self.name, "DOC_NOT_FOUND")
            
            # DocumentModel is a Pydantic model, not a dict
            manufacturer = getattr(document, 'manufacturer', 'generic')
            if manufacturer:
                manufacturer = manufacturer.lower()
            else:
                manufacturer = 'generic'
            
            # Method 1: Pattern-based extraction from text
            text_error_codes = await self._extract_error_codes_from_text(
                context.file_path, manufacturer
            )
            
            # Method 2: AI-based extraction from images (if AI service available)
            ai_error_codes = []
            if self.ai_service:
                ai_error_codes = await self._extract_error_codes_from_images_ai(
                    context.document_id, manufacturer
                )
            
            # Merge and deduplicate
            all_error_codes = self._merge_error_codes(text_error_codes, ai_error_codes)
            
            # Store in database
            manufacturer_id = getattr(document, 'manufacturer_id', None)
            error_code_ids = await self._store_error_codes(
                all_error_codes, context.document_id, manufacturer_id
            )
            
            self.logger.info(
                f"Extracted {len(error_code_ids)} error codes "
                f"({len(text_error_codes)} pattern, {len(ai_error_codes)} AI)"
            )
            
            return self.create_success_result({
                'error_codes_found': len(error_code_ids),
                'error_code_ids': error_code_ids,
                'pattern_extracted': len(text_error_codes),
                'ai_extracted_count': len(ai_error_codes)
            }, {
                'processing_timestamp': datetime.utcnow().isoformat(),
                'manufacturer': manufacturer
            })
            
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            raise ProcessingError(f"Metadata processing failed: {str(e)}", self.name, "PROCESSING_FAILED")
    
    async def _extract_error_codes_from_text(self, file_path: str, manufacturer: str) -> List[Dict]:
        """Extract error codes from document text using pattern matching"""
        error_codes = []
        
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            
            # Get patterns for manufacturer
            patterns = self.error_patterns.get(manufacturer, []) + self.error_patterns.get('generic', [])
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                # Apply all patterns
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        code = match.group(1) if match.lastindex else match.group(0)
                        
                        # Get context around error code
                        context = self._get_context_around_match(text, match.start(), match.end())
                        
                        # Try to extract solution from context
                        solution = self._extract_solution_from_context(context)
                        
                        error_codes.append({
                            'error_code': code.strip(),
                            'page_number': page_num + 1,
                            'context_text': context,
                            'extraction_method': 'pattern_matching',
                            'confidence_score': 0.75,  # Pattern match confidence
                            'solution_text': solution,
                            'ai_extracted': False
                        })
            
            doc.close()
            
            # Deduplicate by code
            unique_codes = {}
            for ec in error_codes:
                code_key = ec['error_code']
                if code_key not in unique_codes:
                    unique_codes[code_key] = ec
                else:
                    # Keep the one with better context/solution
                    if len(ec.get('solution_text', '')) > len(unique_codes[code_key].get('solution_text', '')):
                        unique_codes[code_key] = ec
            
            return list(unique_codes.values())
            
        except ImportError:
            self.logger.warning("PyMuPDF not available - skipping text extraction")
            return []
        except Exception as e:
            self.logger.error(f"Text extraction failed: {e}")
            return []
    
    def _get_context_around_match(self, text: str, start: int, end: int, window: int = 200) -> str:
        """Get text context around a match"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()
    
    def _extract_solution_from_context(self, context: str) -> Optional[str]:
        """Try to extract solution text from context"""
        # Look for common solution indicators
        solution_patterns = [
            r'solution[:\s]+(.+?)(?:\n\n|\Z)',
            r'fix[:\s]+(.+?)(?:\n\n|\Z)',
            r'remedy[:\s]+(.+?)(?:\n\n|\Z)',
            r'action[:\s]+(.+?)(?:\n\n|\Z)',
        ]
        
        for pattern in solution_patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.DOTALL)
            if match:
                solution = match.group(1).strip()
                # Limit solution length
                if len(solution) > 500:
                    solution = solution[:500] + '...'
                return solution
        
        return None
    
    async def _extract_error_codes_from_images_ai(self, document_id: str, manufacturer: str) -> List[Dict]:
        """Extract error codes from images using GPT-4 Vision"""
        error_codes = []
        
        if not self.ai_service:
            return []
        
        try:
            # Get all images for document
            images = await self.database_service.get_images_by_document(document_id)
            
            for image in images:
                # Only process images that might contain error codes
                # (screens, diagrams, control panels)
                image_type = image.get('image_type', '').lower()
                if image_type not in ['screenshot', 'diagram', 'control_panel', 'display', 'screen']:
                    continue
                
                # Use AI to extract error codes from image
                ai_result = await self.ai_service.extract_error_codes_from_image(
                    image_url=image.get('storage_url'),
                    image_id=image.get('id'),
                    manufacturer=manufacturer
                )
                
                if ai_result and ai_result.get('error_codes'):
                    for ec in ai_result['error_codes']:
                        error_codes.append({
                            'error_code': ec.get('code'),
                            'error_description': ec.get('description'),
                            'solution_text': ec.get('solution'),
                            'page_number': image.get('page_number'),
                            'image_id': image.get('id'),
                            'context_text': ec.get('context'),
                            'extraction_method': 'gpt4_vision',
                            'confidence_score': ec.get('confidence', 0.85),
                            'ai_extracted': True,
                            'metadata': {
                                'model': ai_result.get('model', 'gpt-4-vision'),
                                'tokens_used': ai_result.get('tokens_used', 0)
                            }
                        })
            
            self.logger.info(f"AI extracted {len(error_codes)} error codes from images")
            return error_codes
            
        except Exception as e:
            self.logger.error(f"AI image extraction failed: {e}")
            return []
    
    def _merge_error_codes(self, pattern_codes: List[Dict], ai_codes: List[Dict]) -> List[Dict]:
        """Merge and deduplicate error codes from different sources"""
        merged = {}
        
        # Add pattern codes
        for ec in pattern_codes:
            code_key = ec['error_code']
            merged[code_key] = ec
        
        # Add/update with AI codes (AI has higher priority if better data)
        for ec in ai_codes:
            code_key = ec['error_code']
            if code_key not in merged:
                merged[code_key] = ec
            else:
                # If AI has better description/solution, use it
                existing = merged[code_key]
                if len(ec.get('error_description', '')) > len(existing.get('error_description', '')):
                    merged[code_key] = ec
                elif ec.get('solution_text') and not existing.get('solution_text'):
                    merged[code_key] = ec
        
        return list(merged.values())
    
    async def _store_error_codes(self, error_codes: List[Dict], document_id: str, 
                                 manufacturer_id: Optional[str]) -> List[str]:
        """Store error codes in database"""
        stored_ids = []
        
        for ec in error_codes:
            try:
                # Check if error code already exists for this document
                existing = await self._check_duplicate_error_code(
                    ec['error_code'], document_id
                )
                
                if existing:
                    self.logger.debug(f"Error code {ec['error_code']} already exists for document")
                    continue
                
                # Determine severity (can be enhanced with AI)
                severity = self._determine_severity(ec)
                
                # Create error code model
                error_code_model = ErrorCodeModel(
                    document_id=document_id,
                    manufacturer_id=manufacturer_id,
                    error_code=ec['error_code'],
                    error_description=ec.get('error_description', f"Error code {ec['error_code']}"),
                    solution_text=ec.get('solution_text', 'Refer to service manual'),
                    page_number=ec.get('page_number', 1),
                    confidence_score=ec.get('confidence_score', 0.75),
                    extraction_method=ec.get('extraction_method', 'pattern_matching'),
                    severity_level=severity,
                    image_id=ec.get('image_id'),
                    context_text=ec.get('context_text'),
                    metadata=ec.get('metadata', {}),
                    ai_extracted=ec.get('ai_extracted', False)
                )
                
                # Store in database
                error_code_id = await self.database_service.create_error_code(error_code_model)
                if error_code_id:
                    stored_ids.append(error_code_id)
                    
            except Exception as e:
                self.logger.error(f"Failed to store error code {ec['error_code']}: {e}")
        
        return stored_ids
    
    async def _check_duplicate_error_code(self, error_code: str, document_id: str) -> bool:
        """Check if error code already exists for document"""
        try:
            # Query database for existing error code
            # Implementation depends on database service method
            return False  # For now, always insert
        except:
            return False
    
    def _determine_severity(self, error_code: Dict) -> str:
        """Determine error severity level"""
        # Simple heuristic - can be enhanced with AI
        code = error_code.get('error_code', '').upper()
        description = error_code.get('error_description', '').lower()
        solution = error_code.get('solution_text', '').lower()
        
        # Critical keywords
        if any(word in description or word in solution for word in ['jam', 'stuck', 'fatal', 'critical']):
            return 'high'
        
        # Warning keywords
        if any(word in description or word in solution for word in ['warning', 'check', 'clean', 'replace soon']):
            return 'medium'
        
        # Default
        return 'low'
