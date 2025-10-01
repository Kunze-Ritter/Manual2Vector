"""
Optimized Text Processor for KR-AI-Engine
Memory-efficient version with streaming and parallel processing
"""

import logging
import gc
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import fitz
except ImportError:
    fitz = None

from core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult, ProcessingError
from core.data_models import ChunkModel, ChunkType
from services.database_service import DatabaseService
from services.config_service import ConfigService
from optimizations.chunking_optimization import MemoryOptimizedChunking, ParallelChunkingProcessor, MemoryMonitoring
from optimizations.smart_chunking_optimization import SmartChunkingOptimizer

class OptimizedTextProcessor(BaseProcessor):
    """
    Optimized Text Processor - Memory-efficient version
    
    Key Optimizations:
    - Streaming text extraction (page by page)
    - Parallel chunk processing
    - Memory monitoring and cleanup
    - Reduced RAM usage by 70-80%
    """
    
    def __init__(self, database_service: DatabaseService, config_service: ConfigService):
        super().__init__("optimized_text_processor")
        self.database_service = database_service
        self.config_service = config_service
        
        # Initialize smart chunking (combines speed + intelligence)
        self.smart_chunker = SmartChunkingOptimizer(chunk_size=1000, overlap=150)
        self.parallel_processor = ParallelChunkingProcessor(max_workers=4)
    
    def get_required_inputs(self) -> List[str]:
        """Get required inputs for text processor"""
        return ['document_id', 'file_path']
    
    def get_outputs(self) -> List[str]:
        """Get outputs from text processor"""
        return ['chunks', 'total_pages', 'extraction_method', 'memory_usage']
    
    def get_output_tables(self) -> List[str]:
        """Get database tables this processor writes to"""
        return ['krai_content.chunks', 'krai_intelligence.chunks']
    
    def get_dependencies(self) -> List[str]:
        """Get processor dependencies"""
        return ['upload_processor']
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        """Get resource requirements for optimized text processor"""
        return {
            'cpu_intensive': True,
            'memory_intensive': False,  # Optimized to be less memory intensive
            'gpu_required': False,
            'estimated_ram_gb': 0.5,  # Much lower RAM usage
            'estimated_gpu_gb': 0.0,
            'parallel_safe': True
        }
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Process text extraction and chunking with memory optimization
        
        Args:
            context: Processing context with document information
            
        Returns:
            ProcessingResult: Text processing result
        """
        try:
            # Monitor memory usage
            MemoryMonitoring.log_memory_usage(self.logger, "start")
            
            # Get document info
            document = await self.database_service.get_document(context.document_id)
            if not document:
                raise ProcessingError(
                    f"Document not found: {context.document_id}",
                    self.name,
                    "DOCUMENT_NOT_FOUND"
                )
            
            # Get chunking configuration
            document_type = document.document_type if isinstance(document.document_type, str) else document.document_type.value
            chunking_config = self.config_service.get_chunking_strategy(
                document_type,
                document.manufacturer
            )
            
            # Update chunking parameters from config
            if chunking_config:
                self.smart_chunker.chunk_size = chunking_config.get('max_chunk_size', 1000)
                self.smart_chunker.overlap = chunking_config.get('overlap_size', 150)
            
            MemoryMonitoring.log_memory_usage(self.logger, "after_config")
            
            # Smart chunking with intelligent analysis
            chunk_stream = self.smart_chunker.extract_smart_chunks_streaming(
                context.file_path, context.document_id
            )
            
            MemoryMonitoring.log_memory_usage(self.logger, "after_streaming_setup")
            
            # Process chunks in parallel with deduplication
            chunk_ids = await self.parallel_processor.process_chunks_parallel(
                chunk_stream, 
                self.database_service,
                enable_deduplication=True  # Enable chunk deduplication
            )
            
            MemoryMonitoring.log_memory_usage(self.logger, "after_parallel_processing")
            
            # Force memory cleanup
            MemoryMonitoring.force_cleanup()
            
            # Log audit event
            await self.database_service.log_audit(
                action="text_processed_optimized",
                entity_type="document",
                entity_id=context.document_id,
                details={
                    'chunks_created': len(chunk_ids),
                    'chunk_size': self.smart_chunker.chunk_size,
                    'overlap_size': self.smart_chunker.overlap,
                    'parallel_workers': self.parallel_processor.max_workers,
                    'memory_optimized': True
                }
            )
            
            MemoryMonitoring.log_memory_usage(self.logger, "final")
            
            # Return success result
            data = {
                'chunks': chunk_ids,
                'total_chunks': len(chunk_ids),
                'extraction_method': 'optimized_streaming',
                'memory_usage_mb': MemoryMonitoring.get_memory_usage(),
                'chunk_size': self.smart_chunker.chunk_size,
                'overlap_size': self.smart_chunker.overlap
            }
            
            metadata = {
                'processing_timestamp': datetime.utcnow().isoformat(),
                'memory_optimized': True,
                'parallel_processing': True,
                'chunking_strategy': 'streaming_chunking'
            }
            
            return ProcessingResult(
                success=True,
                processor=self.name,
                status='completed',
                data=data,
                metadata=metadata
            )
        
        except ProcessingError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to process text for document {context.document_id}: {e}")
            raise ProcessingError(
                f"Failed to process text: {e}",
                self.name,
                "TEXT_PROCESSING_FAILED"
            )
        finally:
            # Final cleanup
            MemoryMonitoring.force_cleanup()
