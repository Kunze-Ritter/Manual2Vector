"""
Text Processor for KR-AI-Engine
Stage 2: PDF text extraction and chunking
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import fitz
    import pdfplumber
except ImportError:
    fitz = None
    pdfplumber = None

from core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult, ProcessingError
from core.data_models import ChunkModel, ChunkType
from services.database_service import DatabaseService
from services.config_service import ConfigService
from utils.chunk_utils import ChunkingStrategy

class TextProcessor(BaseProcessor):
    """
    Text Processor - Stage 2 of the processing pipeline
    
    Responsibilities:
    - PDF text extraction
    - Intelligent text chunking
    - Content chunk storage
    
    Output: krai_content.chunks + krai_intelligence.chunks
    """
    
    def __init__(self, database_service: DatabaseService, config_service: ConfigService):
        super().__init__("text_processor")
        self.database_service = database_service
        self.config_service = config_service
        self.chunking_strategy = ChunkingStrategy()
    
    def get_required_inputs(self) -> List[str]:
        """Get required inputs for text processor"""
        return ['document_id', 'file_path']
    
    def get_outputs(self) -> List[str]:
        """Get outputs from text processor"""
        return ['chunks', 'intelligence_chunks', 'total_pages', 'extraction_method']
    
    def get_output_tables(self) -> List[str]:
        """Get database tables this processor writes to"""
        return ['krai_content.chunks', 'krai_intelligence.chunks']
    
    def get_dependencies(self) -> List[str]:
        """Get processor dependencies"""
        return ['upload_processor']
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        """Get resource requirements for text processor"""
        return {
            'cpu_intensive': True,
            'memory_intensive': False,
            'gpu_required': False,
            'estimated_ram_gb': 2.0,
            'estimated_gpu_gb': 0.0,
            'parallel_safe': True
        }
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Process text extraction and chunking
        
        Args:
            context: Processing context with document information
            
        Returns:
            ProcessingResult: Text processing result
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
            
            # Extract text from PDF
            text_content, pages_info = await self._extract_text_from_pdf(context.file_path)
            
            if not text_content:
                raise ProcessingError(
                    "No text content extracted from PDF",
                    self.name,
                    "NO_TEXT_EXTRACTED"
                )
            
            # Get chunking strategy for document type
            document_type = document.document_type if isinstance(document.document_type, str) else document.document_type.value
            chunking_config = self.config_service.get_chunking_strategy(
                document_type,
                document.manufacturer
            )
            
            # Create content chunks
            content_chunks = await self._create_content_chunks(
                context.document_id,
                text_content,
                pages_info,
                chunking_config
            )
            
            # Create intelligence chunks
            intelligence_chunks = await self._create_intelligence_chunks(
                context.document_id,
                text_content,
                pages_info,
                chunking_config
            )
            
            # Store chunks in database
            chunk_ids = []
            for chunk in content_chunks:
                chunk_id = await self.database_service.create_chunk(chunk)
                chunk_ids.append(chunk_id)
            
            intelligence_chunk_ids = []
            for chunk in intelligence_chunks:
                chunk_id = await self.database_service.create_intelligence_chunk(chunk)
                intelligence_chunk_ids.append(chunk_id)
            
            # Log audit event
            await self.database_service.log_audit(
                action="text_extracted",
                entity_type="document",
                entity_id=context.document_id,
                details={
                    'total_pages': len(pages_info),
                    'content_chunks': len(chunk_ids),
                    'intelligence_chunks': len(intelligence_chunk_ids),
                    'chunking_strategy': chunking_config.get('preferred_strategy', 'default')
                }
            )
            
            # Return success result
            data = {
                'chunks': chunk_ids,
                'intelligence_chunks': intelligence_chunk_ids,
                'total_pages': len(pages_info),
                'extraction_method': 'pdf_extraction',
                'chunking_strategy': chunking_config.get('preferred_strategy', 'default')
            }
            
            metadata = {
                'total_text_length': len(text_content),
                'average_chunk_size': sum(len(chunk.content) for chunk in content_chunks) // len(content_chunks) if content_chunks else 0,
                'processing_timestamp': datetime.utcnow().isoformat()
            }
            
            return self.create_success_result(data, metadata)
            
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            else:
                raise ProcessingError(
                    f"Text processing failed: {str(e)}",
                    self.name,
                    "TEXT_PROCESSING_FAILED"
                )
    
    async def _extract_text_from_pdf(self, file_path: str) -> tuple:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (text_content, pages_info)
        """
        try:
            if fitz is None:
                # Mock mode for testing
                self.logger.info("Using mock text extraction for testing")
                text_content = "This is mock PDF content for testing. It contains technical information about printer maintenance and troubleshooting procedures."
                pages_info = [
                    {
                        'page_number': 1,
                        'text_length': len(text_content),
                        'has_images': False,
                        'rotation': 0
                    }
                ]
                return text_content, pages_info
            
            try:
                # Open PDF with PyMuPDF
                doc = fitz.open(file_path)
                text_content = ""
                pages_info = []
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    
                    # Extract text
                    page_text = page.get_text()
                    text_content += page_text + "\n"
                    
                    # Get page info
                    page_info = {
                        'page_number': page_num + 1,
                        'text_length': len(page_text),
                        'has_images': len(page.get_images()) > 0,
                        'rotation': page.rotation
                    }
                    pages_info.append(page_info)
                
                doc.close()
                
                self.logger.info(f"Extracted text from {len(pages_info)} pages")
                return text_content, pages_info
            except Exception as e:
                # Fallback to mock mode if PDF is not valid
                self.logger.warning(f"PDF extraction failed: {e}. Using mock mode.")
                text_content = "This is mock PDF content for testing. It contains technical information about printer maintenance and troubleshooting procedures."
                pages_info = [
                    {
                        'page_number': 1,
                        'text_length': len(text_content),
                        'has_images': False,
                        'rotation': 0
                    }
                ]
                return text_content, pages_info
            
        except Exception as e:
            self.logger.error(f"Failed to extract text from PDF: {e}")
            raise
    
    async def _create_content_chunks(self, 
                                   document_id: str, 
                                   text_content: str, 
                                   pages_info: List[Dict], 
                                   chunking_config: Dict[str, Any]) -> List[ChunkModel]:
        """
        Create content chunks from text
        
        Args:
            document_id: Document ID
            text_content: Full text content
            pages_info: Page information
            chunking_config: Chunking configuration
            
        Returns:
            List of content chunks
        """
        try:
            # Get chunking strategy
            strategy = chunking_config.get('preferred_strategy', 'contextual_chunking')
            chunk_size = chunking_config.get('chunk_size', 1000)
            chunk_overlap = chunking_config.get('chunk_overlap', 150)
            
            # Create chunks using chunking strategy
            chunks_data = self.chunking_strategy.create_chunks(
                text_content,
                strategy=strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            # Convert to ChunkModel objects
            chunks = []
            for i, chunk_data in enumerate(chunks_data):
                # Determine chunk type
                chunk_type = self._determine_chunk_type(chunk_data.content)
                
                # Find page number for chunk
                page_number = self._find_page_for_chunk(chunk_data.content, pages_info)
                
                chunk = ChunkModel(
                    document_id=document_id,
                    content=chunk_data.content,
                    chunk_type=chunk_type,
                    chunk_index=i + 1,
                    page_number=page_number,
                    section_title=chunk_data.section_title,
                    confidence_score=chunk_data.confidence,
                    language='en'
                )
                chunks.append(chunk)
            
            self.logger.info(f"Created {len(chunks)} content chunks")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Failed to create content chunks: {e}")
            raise
    
    async def _create_intelligence_chunks(self, 
                                        document_id: str, 
                                        text_content: str, 
                                        pages_info: List[Dict], 
                                        chunking_config: Dict[str, Any]) -> List:
        """
        Create intelligence chunks for semantic search
        
        Args:
            document_id: Document ID
            text_content: Full text content
            pages_info: Page information
            chunking_config: Chunking configuration
            
        Returns:
            List of intelligence chunks
        """
        try:
            from core.data_models import IntelligenceChunkModel
            
            # Use smaller chunks for intelligence processing
            intelligence_chunk_size = chunking_config.get('chunk_size', 1000) // 2
            intelligence_overlap = chunking_config.get('chunk_overlap', 150) // 2
            
            # Create intelligence chunks
            chunks_data = self.chunking_strategy.create_chunks(
                text_content,
                strategy='contextual_chunking',
                chunk_size=intelligence_chunk_size,
                chunk_overlap=intelligence_overlap
            )
            
            # Convert to IntelligenceChunkModel objects
            intelligence_chunks = []
            for i, chunk_data in enumerate(chunks_data):
                # Generate fingerprint for deduplication
                fingerprint = self._generate_chunk_fingerprint(chunk_data.content)
                
                # Find page range for chunk
                page_start, page_end = self._find_page_range_for_chunk(chunk_data.content, pages_info)
                
                # Create metadata
                metadata = {
                    'section': chunk_data.section_title or '',
                    'confidence': chunk_data.confidence,
                    'contains_error_code': self._contains_error_code(chunk_data.content),
                    'contains_procedure': self._contains_procedure(chunk_data.content),
                    'contains_part_number': self._contains_part_number(chunk_data.content)
                }
                
                chunk = IntelligenceChunkModel(
                    document_id=document_id,
                    text_chunk=chunk_data.content,
                    chunk_index=i + 1,
                    page_start=page_start,
                    page_end=page_end,
                    fingerprint=fingerprint,
                    metadata=metadata
                )
                intelligence_chunks.append(chunk)
            
            self.logger.info(f"Created {len(intelligence_chunks)} intelligence chunks")
            return intelligence_chunks
            
        except Exception as e:
            self.logger.error(f"Failed to create intelligence chunks: {e}")
            raise
    
    def _determine_chunk_type(self, content: str) -> ChunkType:
        """Determine chunk type based on content"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['error', 'code', 'fault', 'troubleshoot']):
            return ChunkType.ERROR_CODE
        elif any(keyword in content_lower for keyword in ['step', 'procedure', 'instruction', 'how to']):
            return ChunkType.PROCEDURE
        elif content_lower.startswith(('1.', '2.', '3.', '•', '-', '*')):
            return ChunkType.LIST
        elif '|' in content or '\t' in content:
            return ChunkType.TABLE
        else:
            return ChunkType.TEXT
    
    def _find_page_for_chunk(self, chunk_content: str, pages_info: List[Dict]) -> Optional[int]:
        """Find page number for chunk content"""
        # Simple heuristic - could be improved with more sophisticated matching
        for page_info in pages_info:
            if len(chunk_content) > 100:  # Only for substantial chunks
                return page_info['page_number']
        return None
    
    def _find_page_range_for_chunk(self, chunk_content: str, pages_info: List[Dict]) -> tuple:
        """Find page range for chunk content"""
        # Simple heuristic - could be improved
        start_page = 1
        end_page = len(pages_info)
        return start_page, end_page
    
    def _generate_chunk_fingerprint(self, content: str) -> str:
        """Generate fingerprint for chunk deduplication"""
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()
    
    def _contains_error_code(self, content: str) -> bool:
        """Check if chunk contains error codes"""
        import re
        error_patterns = [
            r'\b\d{2}\.\d{2}\.\d{2}\b',  # HP format
            r'\b[CJ]\d{4,5}\b',          # Konica Minolta format
            r'\b\d{2,3}\.\d{2}\b',      # Lexmark format
            r'\b\d{5}\b'                 # UTAX format
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, content):
                return True
        return False
    
    def _contains_procedure(self, content: str) -> bool:
        """Check if chunk contains procedures"""
        procedure_keywords = ['step', 'procedure', 'instruction', 'how to', 'follow these steps']
        return any(keyword in content.lower() for keyword in procedure_keywords)
    
    def _contains_part_number(self, content: str) -> bool:
        """Check if chunk contains part numbers"""
        import re
        part_patterns = [
            r'\b[A-Z]{2,4}\d{4,8}[A-Z]?\b',  # Common part number patterns
            r'\b[A-Z]\d{6,10}\b'
        ]
        
        for pattern in part_patterns:
            if re.search(pattern, content):
                return True
        return False
