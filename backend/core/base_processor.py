"""
Base Processor Interface
Foundation for all 8 specialized processors in the KR-AI-Engine pipeline
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import contextlib
import logging
from uuid import UUID

from backend.processors.logger import get_logger

class ProcessingStatus(Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProcessingError(Exception):
    """Custom exception for processing errors"""
    def __init__(self, message: str, processor: str, error_code: str = None):
        self.message = message
        self.processor = processor
        self.error_code = error_code
        super().__init__(f"[{processor}] {message}")

@dataclass
class ProcessingResult:
    """Result of a processing operation"""
    success: bool
    processor: str
    status: ProcessingStatus
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Optional[ProcessingError] = None
    processing_time: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class ProcessingContext:
    """Context information for processing operations
    
    Extended with Phase 5 context extraction support:
    - page_texts: Page text from TextProcessor (key: page_number, value: text)
    - images/tables/links/videos: Extracted media with context metadata
    - pdf_path: Alias for file_path for clarity
    """
    document_id: str
    file_path: str
    document_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    series: Optional[str] = None
    version: Optional[str] = None
    language: str = "en"
    processing_config: Dict[str, Any] = None
    file_hash: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    file_size: Optional[int] = None
    # Phase 5: Context extraction fields
    page_texts: Optional[Dict[int, str]] = None  # Page text from TextProcessor
    pdf_path: Optional[str] = None  # PDF path (alias for file_path)
    images: Optional[List[Dict[str, Any]]] = None  # Extracted images with context
    tables: Optional[List[Dict[str, Any]]] = None  # Extracted tables with context
    links: Optional[List[Dict[str, Any]]] = None  # Extracted links with context
    videos: Optional[List[Dict[str, Any]]] = None  # Extracted videos with context
    
    def __post_init__(self):
        if self.processing_config is None:
            self.processing_config = {}
        # Auto-populate pdf_path from file_path for clarity
        if self.pdf_path is None:
            self.pdf_path = self.file_path

class Stage(Enum):
    """Canonical stage names for pipeline processors."""

    UPLOAD = "upload"
    TEXT_EXTRACTION = "text_extraction"
    TABLE_EXTRACTION = "table_extraction"  # Stage 2b: Table Processor → krai_intelligence.structured_tables
    SVG_PROCESSING = "svg_processing"  # Stage 3a: SVG Processor → Convert vector graphics to PNG
    IMAGE_PROCESSING = "image_processing"
    VISUAL_EMBEDDING = "visual_embedding"  # Stage 3b: Visual Embedding Processor → krai_intelligence.embeddings_v2 (images)
    LINK_EXTRACTION = "link_extraction"
    CHUNK_PREPROCESSING = "chunk_prep"
    CLASSIFICATION = "classification"
    METADATA_EXTRACTION = "metadata_extraction"
    PARTS_EXTRACTION = "parts_extraction"
    SERIES_DETECTION = "series_detection"
    STORAGE = "storage"
    EMBEDDING = "embedding"  # Stage 7: Embedding Processor → krai_intelligence.chunks (legacy) + embeddings_v2 (new)
    SEARCH_INDEXING = "search_indexing"


class BaseProcessor(ABC):
    """
    Base class for all processors in the KR-AI-Engine pipeline
    
    Follows the enhanced processing pipeline with multi-modal support:
    1. Upload Processor → krai_core.documents (Database only)
    2. Text Processor → krai_content.chunks + krai_intelligence.chunks
    2b. Table Processor → krai_intelligence.structured_tables
    3a. SVG Processor → Convert vector graphics to PNG for Vision AI
    3. Image Processor → krai_content.images (Object Storage)
    3b. Visual Embedding Processor → krai_intelligence.embeddings_v2 (images)
    4. Classification Processor → krai_core.manufacturers, products, product_series
    5. Metadata Processor → krai_intelligence.error_codes
    6. Storage Processor → Cloudflare R2 (NUR Bilder)
    7. Text Chunking → krai_intelligence.chunks
    8. Embedding Processor → krai_intelligence.chunks (legacy) + embeddings_v2 (new)
    9. Finalization → krai_system.processing_queue
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        processor_logger = get_logger(name=f"processor.{name}")
        self.logger = processor_logger  # ProcessorLogger interface (info, success, etc.)
        self.log = processor_logger
        self._base_logger = processor_logger.logger
        self._base_extra: Dict[str, Any] = {"processor": self.name}
        self._logger_adapter = logging.LoggerAdapter(self._base_logger, dict(self._base_extra))

    @contextlib.contextmanager
    def logger_context(
        self,
        document_id: Optional[Union[str, UUID]] = None,
        stage: Optional[Union[Stage, str]] = None,
        **extra: Any
    ):
        """Attach contextual fields (processor/document/stage) to logger."""

        merged_extra: Dict[str, Any] = dict(self._base_extra)
        if document_id is not None:
            merged_extra["document_id"] = str(document_id)
        if stage is not None:
            merged_extra["stage"] = stage.value if isinstance(stage, Stage) else stage
        merged_extra.update({k: v for k, v in extra.items() if v is not None})

        adapter = logging.LoggerAdapter(self._base_logger, merged_extra)
        previous_adapter = self._logger_adapter
        self._logger_adapter = adapter
        try:
            yield adapter
        finally:
            self._logger_adapter = previous_adapter

    @abstractmethod
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Main processing method - MUST be implemented by subclasses
        
        Args:
            context: Processing context with document information
            
        Returns:
            ProcessingResult: Result of the processing operation
            
        Raises:
            ProcessingError: If processing fails (Error = Stopp!)
        """
        pass
    
    def get_required_inputs(self) -> List[str]:
        """
        Get list of required input data for this processor.

        Subclasses can override to declare specific requirements. Defaults to []
        """
        return []
    
    def get_outputs(self) -> List[str]:
        """
        Get list of output data produced by this processor.

        Subclasses can override to declare structured outputs. Defaults to []
        """
        return []
    
    def validate_inputs(self, context: ProcessingContext) -> bool:
        """
        Validate that all required inputs are present
        
        Args:
            context: Processing context to validate
            
        Returns:
            bool: True if inputs are valid
            
        Raises:
            ProcessingError: If validation fails
        """
        required_inputs = self.get_required_inputs()
        
        for input_key in required_inputs:
            if not hasattr(context, input_key) or getattr(context, input_key) is None:
                raise ProcessingError(
                    f"Missing required input: {input_key}",
                    self.name,
                    "MISSING_INPUT"
                )
        
        return True
    
    def log_processing_start(self, context: ProcessingContext):
        """Log the start of processing"""
        with self.logger_context(document_id=context.document_id) as adapter:
            adapter.info(
                "Starting %s processing for document %s",
                self.name,
                context.document_id,
            )
            adapter.debug("Context: %s", context)
    
    def log_processing_end(self, result: ProcessingResult):
        """Log the end of processing"""
        document_id = None
        stage = None
        if result.metadata:
            document_id = result.metadata.get("document_id") or result.metadata.get("document")
            stage = result.metadata.get("stage")

        with self.logger_context(document_id=document_id, stage=stage) as adapter:
            if result.success:
                adapter.info(
                    "Completed %s processing in %.2fs",
                    self.name,
                    result.processing_time,
                )
                self.logger.success(
                    f"{self.name} completed in {result.processing_time:.2f}s"
                )
            else:
                adapter.error(
                    "Failed %s processing: %s",
                    self.name,
                    result.error,
                )
                self.logger.error(
                    f"{self.name} failed: {result.error}"
                )
    
    def create_success_result(self, data: Dict[str, Any], metadata: Dict[str, Any] = None) -> ProcessingResult:
        """Create a successful processing result"""
        return ProcessingResult(
            success=True,
            processor=self.name,
            status=ProcessingStatus.COMPLETED,
            data=data,
            metadata=metadata or {},
            processing_time=0.0  # Will be set by caller
        )
    
    def create_error_result(
        self,
        error: ProcessingError,
        metadata: Dict[str, Any] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> ProcessingResult:
        """Create a failed processing result"""
        return ProcessingResult(
            success=False,
            processor=self.name,
            status=ProcessingStatus.FAILED,
            data=data or {},
            metadata=metadata or {},
            error=error,
            processing_time=0.0  # Will be set by caller
        )
    
    async def safe_process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Safely execute processing with error handling
        
        Args:
            context: Processing context
            
        Returns:
            ProcessingResult: Result of processing (success or failure)
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate inputs
            self.validate_inputs(context)
            
            # Log start
            self.log_processing_start(context)
            
            # Execute processing
            result = await self.process(context)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.processing_time = processing_time
            
            # Log end
            self.log_processing_end(result)
            
            return result
            
        except ProcessingError as e:
            # Processing error - log and return error result
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result = self.create_error_result(e)
            result.processing_time = processing_time
            self.log_processing_end(result)
            return result
            
        except Exception as e:
            # Unexpected error - convert to ProcessingError
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            error = ProcessingError(
                f"Unexpected error: {str(e)}",
                self.name,
                "UNEXPECTED_ERROR"
            )
            result = self.create_error_result(error)
            result.processing_time = processing_time
            self.log_processing_end(result)
            return result
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        """
        Get resource requirements for this processor
        
        Returns:
            Dict[str, Any]: Resource requirements
        """
        return {
            'cpu_intensive': False,
            'memory_intensive': False,
            'gpu_required': False,
            'estimated_ram_gb': 1.0,
            'estimated_gpu_gb': 0.0,
            'parallel_safe': True
        }
    
    def get_dependencies(self) -> List[str]:
        """
        Get list of processors this processor depends on
        
        Returns:
            List[str]: List of processor names this depends on
        """
        return []
    
    def get_output_tables(self) -> List[str]:
        """
        Get list of database tables this processor writes to
        
        Returns:
            List[str]: List of table names
        """
        return []
    
    def get_storage_buckets(self) -> List[str]:
        """
        Get list of storage buckets this processor uses
        
        Returns:
            List[str]: List of bucket names
        """
        return []
