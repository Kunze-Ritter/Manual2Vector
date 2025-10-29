"""
Text Processor (Optimized) - Extract and chunk text from PDFs

Stage 2 of the processing pipeline.

Extracts text from PDFs using PyMuPDF and creates intelligent chunks
for embedding and search.
"""

import os
from pathlib import Path
from typing import Any, Dict, List
from uuid import UUID
import hashlib

from backend.core.base_processor import BaseProcessor, Stage
from .text_extractor import TextExtractor
from .chunker import SmartChunker
from .models import TextChunk


class OptimizedTextProcessor(BaseProcessor):
    """
    Stage 2: Text Processor (Optimized)
    
    Extracts text from PDFs and creates chunks for processing.
    Uses PyMuPDF for fast text extraction and SmartChunker for intelligent chunking.
    """
    
    def __init__(self, database_service=None, config_service=None):
        """
        Initialize text processor
        
        Args:
            database_service: Database service instance
            config_service: Config service instance
        """
        super().__init__(name="text_processor")
        self.stage = Stage.TEXT_EXTRACTION
        self.database_service = database_service
        self.config_service = config_service
        
        # Initialize text extractor
        enable_ocr = os.getenv("ENABLE_OCR_FALLBACK", "false").lower() in {"1", "true", "yes", "on"}
        pdf_engine = os.getenv("PDF_ENGINE", "pymupdf")
        self.text_extractor = TextExtractor(prefer_engine=pdf_engine, enable_ocr_fallback=enable_ocr)
        
        # Initialize chunker with config or defaults
        chunk_size = 1000
        chunk_overlap = 100
        
        if config_service and hasattr(config_service, 'get_chunk_settings'):
            settings = config_service.get_chunk_settings()
            chunk_size = settings.get('chunk_size', 1000)
            chunk_overlap = settings.get('chunk_overlap', 100)
        
        self.chunker = SmartChunker(chunk_size=chunk_size, overlap_size=chunk_overlap)
        
        self.logger.info(f"OptimizedTextProcessor initialized (chunk_size={chunk_size}, overlap={chunk_overlap})")
    
    async def process(self, context) -> Any:
        """
        Process text extraction and chunking
        
        Args:
            context: Processing context with file_path and document_id
            
        Returns:
            Processing result with chunks_created count
        """
        with self.logger_context(
            document_id=getattr(context, "document_id", None),
            stage=self.stage
        ) as adapter:
            try:
                file_path = Path(context.file_path)

                if not file_path.exists():
                    adapter.warning("File not found: %s", file_path)
                    return self._create_result(
                        success=False,
                        message=f"File not found: {file_path}",
                        data={}
                    )

                adapter.info("Extracting text from %s", file_path.name)
                page_texts, metadata = self.text_extractor.extract_text(file_path)

                if not page_texts:
                    adapter.warning("No text extracted from PDF")
                    return self._create_result(
                        success=False,
                        message="No text extracted from PDF",
                        data={'pages_processed': 0}
                    )

                self.logger.success(f"✅ Extracted text from {len(page_texts)} pages")

                adapter.info("Creating chunks...")
                chunks = self.chunker.chunk_document(
                    page_texts=page_texts,
                    document_id=UUID(context.document_id) if isinstance(context.document_id, str) else context.document_id
                )

                if not chunks:
                    adapter.warning("No chunks created")
                    return self._create_result(
                        success=False,
                        message="No chunks created",
                        data={'pages_processed': len(page_texts)}
                    )

                self.logger.success(f"✅ Created {len(chunks)} chunks")

                if self.database_service:
                    adapter.info("Saving chunks to database...")
                    chunks_saved = await self._save_chunks_to_db(chunks, context.document_id)
                    self.logger.success(f"✅ Saved {chunks_saved} chunks to database")
                else:
                    adapter.warning("No database service - chunks not saved")
                    chunks_saved = 0

                return self._create_result(
                    success=True,
                    message=f"Text processing completed: {len(chunks)} chunks created",
                    data={
                        'pages_processed': len(page_texts),
                        'chunks_created': len(chunks),
                        'chunks_saved': chunks_saved,
                        'total_characters': sum(len(chunk.content) for chunk in chunks),
                        'metadata': metadata
                    }
                )

            except Exception as e:
                adapter.error("Text processing failed: %s", e)
                self.logger.error(f"Text processing failed: {e}")
                return self._create_result(
                    success=False,
                    message=f"Text processing error: {str(e)}",
                    data={}
                )
    
    async def _save_chunks_to_db(self, chunks: List[TextChunk], document_id: str) -> int:
        """
        Save chunks to database
        
        Args:
            chunks: List of TextChunk objects
            document_id: Document UUID
            
        Returns:
            Number of chunks saved
        """
        saved_count = 0
        
        for chunk in chunks:
            try:
                # Prepare chunk data for database
                chunk_data = {
                    'document_id': str(document_id),
                    'chunk_index': chunk.chunk_index,
                    'page_start': chunk.page_start,
                    'page_end': chunk.page_end,
                    'content': chunk.content,
                    'content_hash': chunk.content_hash,
                    'char_count': chunk.char_count,
                    'metadata': chunk.metadata
                }
                
                # Insert into database (krai_intelligence.chunks)
                if hasattr(self.database_service, 'insert_chunk'):
                    await self.database_service.insert_chunk(chunk_data)
                    saved_count += 1
                elif hasattr(self.database_service, 'client'):
                    # Fallback to direct Supabase client
                    result = self.database_service.client.table('chunks').insert(chunk_data).execute()
                    if result.data:
                        saved_count += 1
                        
            except Exception as e:
                self.logger.warning(f"Failed to save chunk {chunk.chunk_index}: {e}")
        
        return saved_count
    
    def _create_result(self, success: bool, message: str, data: Dict) -> Any:
        """Create a processing result object"""
        class Result:
            def __init__(self, success, message, data):
                self.success = success
                self.message = message
                self.data = data
        
        return Result(success, message, data)
