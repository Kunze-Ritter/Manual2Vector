"""
Metadata Processor for KR-AI-Engine
Stage 5: Metadata extraction and error code processing
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult, ProcessingError
from core.data_models import ErrorCodeModel
from services.database_service import DatabaseService
from services.config_service import ConfigService
from utils.pattern_utils import PatternMatcher

class MetadataProcessor(BaseProcessor):
    """
    Metadata Processor - Stage 5 of the processing pipeline
    
    Responsibilities:
    - Error code extraction
    - Version detection
    - Metadata enrichment
    
    Output: krai_intelligence.error_codes
    """
    
    def __init__(self, database_service: DatabaseService, config_service: ConfigService):
        super().__init__("metadata_processor")
        self.database_service = database_service
        self.config_service = config_service
        self.pattern_matcher = PatternMatcher()
    
    def get_required_inputs(self) -> List[str]:
        """Get required inputs for metadata processor"""
        return ['document_id', 'file_path']
    
    def get_outputs(self) -> List[str]:
        """Get outputs from metadata processor"""
        return ['error_codes', 'versions', 'metadata']
    
    def get_output_tables(self) -> List[str]:
        """Get database tables this processor writes to"""
        return ['krai_intelligence.error_codes']
    
    def get_dependencies(self) -> List[str]:
        """Get processor dependencies"""
        return ['text_processor', 'classification_processor']
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        """Get resource requirements for metadata processor"""
        return {
            'cpu_intensive': True,
            'memory_intensive': False,
            'gpu_required': False,
            'estimated_ram_gb': 1.0,
            'estimated_gpu_gb': 0.0,
            'parallel_safe': True
        }
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Process metadata extraction
        
        Args:
            context: Processing context with document information
            
        Returns:
            ProcessingResult: Metadata processing result
        """
        try:
            # Get document info
            document = await self.database_service.get_document(context.document_id)
            if not document:
                raise ProcessingError(
                    f"Document not found: {context.document_id}",
                    self.name,
                    "DOCUMENT_NOT_FOUND"
                )
            
            # Extract text for metadata processing
            document_text = await self._extract_document_text(context.file_path)
            
            # Extract error codes
            error_codes = await self._extract_error_codes(
                document_text, 
                document.manufacturer or "Unknown"
            )
            
            # Extract versions
            versions = await self._extract_versions(document_text, document.document_type.value)
            
            # Store error codes in database
            error_code_ids = []
            for error_code in error_codes:
                error_code_model = ErrorCodeModel(
                    document_id=context.document_id,
                    error_code=error_code['code'],
                    error_description=error_code['description'],
                    solution_text=error_code['solution'],
                    page_number=error_code.get('page_number', 1),
                    confidence_score=error_code.get('confidence', 0.8),
                    extraction_method='pattern_matching',
                    requires_technician=error_code.get('requires_technician', False),
                    requires_parts=error_code.get('requires_parts', False),
                    estimated_fix_time_minutes=error_code.get('estimated_fix_time'),
                    severity_level=error_code.get('severity', 'low'),
                    manufacturer=document.manufacturer,
                    model=document.models[0] if document.models else None
                )
                
                error_code_id = await self.database_service.create_error_code(error_code_model)
                error_code_ids.append(error_code_id)
            
            # Log audit event
            await self.database_service.log_audit(
                action="metadata_extracted",
                entity_type="document",
                entity_id=context.document_id,
                details={
                    'error_codes_found': len(error_codes),
                    'versions_found': len(versions),
                    'manufacturer': document.manufacturer
                }
            )
            
            # Return success result
            data = {
                'error_codes': error_code_ids,
                'versions': versions,
                'metadata': {
                    'error_codes_count': len(error_codes),
                    'versions_count': len(versions),
                    'manufacturer': document.manufacturer
                }
            }
            
            metadata = {
                'processing_timestamp': datetime.utcnow().isoformat(),
                'extraction_method': 'pattern_matching'
            }
            
            return self.create_success_result(data, metadata)
            
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            else:
                raise ProcessingError(
                    f"Metadata processing failed: {str(e)}",
                    self.name,
                    "METADATA_PROCESSING_FAILED"
                )
    
    async def _extract_document_text(self, file_path: str) -> str:
        """Extract text from document for metadata processing"""
        try:
            import PyMuPDF as fitz
            
            doc = fitz.open(file_path)
            text_content = ""
            
            # Extract text from all pages
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text_content += page.get_text() + "\n"
            
            doc.close()
            return text_content
            
        except Exception as e:
            self.logger.error(f"Failed to extract document text: {e}")
            return ""
    
    async def _extract_error_codes(self, text: str, manufacturer: str) -> List[Dict[str, Any]]:
        """Extract error codes from text"""
        try:
            # Get manufacturer-specific patterns
            patterns = self.config_service.get_error_patterns_for_manufacturer(manufacturer)
            
            # Use pattern matcher
            matches = self.pattern_matcher.match_error_codes(text, manufacturer)
            
            error_codes = []
            for match in matches:
                error_code = {
                    'code': match['error_code'],
                    'description': f"Error code {match['error_code']}",
                    'solution': "Refer to service manual for solution",
                    'page_number': 1,  # Would need page mapping
                    'confidence': 0.8,
                    'requires_technician': True,
                    'requires_parts': False,
                    'severity': 'medium'
                }
                error_codes.append(error_code)
            
            self.logger.info(f"Extracted {len(error_codes)} error codes for {manufacturer}")
            return error_codes
            
        except Exception as e:
            self.logger.error(f"Failed to extract error codes: {e}")
            return []
    
    async def _extract_versions(self, text: str, document_type: str) -> List[Dict[str, Any]]:
        """Extract version information from text"""
        try:
            # Get version patterns for document type
            patterns = self.config_service.get_version_patterns_for_document(document_type)
            
            # Use pattern matcher
            versions = self.pattern_matcher.extract_versions(text, document_type)
            
            self.logger.info(f"Extracted {len(versions)} versions")
            return versions
            
        except Exception as e:
            self.logger.error(f"Failed to extract versions: {e}")
            return []
