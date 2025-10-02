"""
Chunk Preprocessor - Prepares content chunks for AI processing
Fills krai_intelligence.chunks from krai_content.chunks
"""

import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult, ProcessingError

class ChunkPreprocessor(BaseProcessor):
    """
    Chunk Preprocessor - Stage 4b
    
    Responsibilities:
    - Read chunks from krai_content.chunks
    - Generate fingerprints for deduplication
    - Add metadata and status tracking
    - Write to krai_intelligence.chunks for embedding processing
    
    Input: krai_content.chunks (raw chunks from text processor)
    Output: krai_intelligence.chunks (AI-ready chunks with fingerprints)
    """
    
    def __init__(self, database_service):
        super().__init__("chunk_preprocessor")
        self.database_service = database_service
        self.logger = logging.getLogger("krai.chunk_preprocessor")
    
    def get_required_inputs(self) -> List[str]:
        return ['document_id']
    
    def get_outputs(self) -> List[str]:
        return ['chunks_preprocessed', 'chunks_deduplicated', 'intelligence_chunk_ids']
    
    def get_output_tables(self) -> List[str]:
        return ['krai_intelligence.chunks']
    
    def get_dependencies(self) -> List[str]:
        return ['text_processor']
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'cpu_intensive': False,
            'memory_intensive': False,
            'gpu_required': False,
            'estimated_ram_gb': 0.5,
            'parallel_safe': True
        }
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """Preprocess content chunks for AI processing"""
        try:
            self.logger.info(f"Preprocessing chunks for document: {context.document_id}")
            
            # Get raw chunks from krai_content.chunks
            content_chunks = await self._get_content_chunks(context.document_id)
            
            if not content_chunks:
                self.logger.warning(f"No content chunks found for document {context.document_id}")
                return self.create_success_result({
                    'chunks_preprocessed': 0,
                    'chunks_deduplicated': 0,
                    'intelligence_chunk_ids': []
                })
            
            # Process and deduplicate chunks
            intelligence_chunks = await self._preprocess_chunks(content_chunks, context.document_id)
            
            # Store in krai_intelligence.chunks
            chunk_ids = await self._store_intelligence_chunks(intelligence_chunks)
            
            # Calculate deduplication stats
            deduplicated_count = len(content_chunks) - len(intelligence_chunks)
            
            self.logger.info(
                f"Preprocessed {len(intelligence_chunks)} chunks "
                f"({deduplicated_count} duplicates removed)"
            )
            
            return self.create_success_result({
                'chunks_preprocessed': len(intelligence_chunks),
                'chunks_deduplicated': deduplicated_count,
                'intelligence_chunk_ids': chunk_ids
            }, {
                'processing_timestamp': datetime.utcnow().isoformat(),
                'original_chunks': len(content_chunks),
                'final_chunks': len(intelligence_chunks)
            })
            
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            raise ProcessingError(
                f"Chunk preprocessing failed: {str(e)}", 
                self.name, 
                "PREPROCESSING_FAILED"
            )
    
    async def _get_content_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get raw chunks from krai_content.chunks"""
        try:
            # Use database service method
            chunks = await self.database_service.get_chunks_by_document(document_id)
            return chunks
            
        except Exception as e:
            self.logger.error(f"Failed to get content chunks: {e}")
            return []
    
    async def _preprocess_chunks(self, content_chunks: List[Dict], document_id: str) -> List[Dict]:
        """Preprocess chunks: generate fingerprints, deduplicate, add metadata"""
        processed_chunks = []
        seen_fingerprints = set()
        
        for idx, chunk in enumerate(content_chunks):
            try:
                # Extract text content (column name varies)
                text_content = chunk.get('content') or chunk.get('text_chunk') or ""
                
                if not text_content or len(text_content.strip()) < 10:
                    # Skip empty or very short chunks
                    continue
                
                # Generate fingerprint for deduplication
                fingerprint = self._generate_fingerprint(text_content)
                
                # Check for duplicates
                if fingerprint in seen_fingerprints:
                    self.logger.debug(f"Duplicate chunk detected (fingerprint: {fingerprint[:16]}...)")
                    continue
                
                seen_fingerprints.add(fingerprint)
                
                # Create intelligence chunk
                intelligence_chunk = {
                    'document_id': document_id,
                    'text_chunk': text_content,
                    'chunk_index': chunk.get('chunk_index', idx),
                    'page_start': chunk.get('page_number', 1),
                    'page_end': chunk.get('page_number', 1),
                    'processing_status': 'pending',
                    'fingerprint': fingerprint,
                    'metadata': {
                        'chunk_type': chunk.get('chunk_type', 'text'),
                        'section_title': chunk.get('section_title'),
                        'language': chunk.get('language', 'en'),
                        'confidence_score': chunk.get('confidence_score', 1.0),
                        'source_chunk_id': str(chunk.get('id', '')),
                        'preprocessed_at': datetime.utcnow().isoformat()
                    }
                }
                
                processed_chunks.append(intelligence_chunk)
                
            except Exception as e:
                self.logger.error(f"Failed to preprocess chunk {idx}: {e}")
                continue
        
        return processed_chunks
    
    def _generate_fingerprint(self, text: str) -> str:
        """Generate fingerprint for chunk deduplication"""
        # Normalize text
        normalized = text.lower().strip()
        normalized = ' '.join(normalized.split())  # Normalize whitespace
        
        # Generate SHA256 hash
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    async def _store_intelligence_chunks(self, chunks: List[Dict]) -> List[str]:
        """Store preprocessed chunks in krai_intelligence.chunks"""
        chunk_ids = []
        
        for chunk in chunks:
            try:
                # Insert into krai_intelligence.chunks
                chunk_id = await self.database_service.create_intelligence_chunk(chunk)
                if chunk_id:
                    chunk_ids.append(chunk_id)
                    
            except Exception as e:
                self.logger.error(f"Failed to store intelligence chunk: {e}")
                # Continue with other chunks
        
        return chunk_ids
