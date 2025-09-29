"""
Base Processor Interface
Foundation for all 8 specialized processors in the KR-AI-Engine pipeline
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

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
    """Context information for processing operations"""
    document_id: str
    file_path: str
    file_hash: str
    document_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    series: Optional[str] = None
    version: Optional[str] = None
    language: str = "en"
    processing_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.processing_config is None:
            self.processing_config = {}

class BaseProcessor(ABC):
    """
    Base class for all processors in the KR-AI-Engine pipeline
    
    Follows the 9-stage processing pipeline:
    1. Upload Processor → krai_core.documents (Database only)
    2. Text Processor → krai_content.chunks + krai_intelligence.chunks
    3. Image Processor → krai_content.images (Object Storage)
    4. Classification Processor → krai_core.manufacturers, products, product_series
    5. Metadata Processor → krai_intelligence.error_codes
    6. Storage Processor → Cloudflare R2 (NUR Bilder)
    7. Text Chunking → krai_intelligence.chunks
    8. Embedding Processor → krai_intelligence.embeddings
    9. Finalization → krai_system.processing_queue
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"krai.{name}")
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the processor"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            f'%(asctime)s - {self.name} - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
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
    
    @abstractmethod
    def get_required_inputs(self) -> List[str]:
        """
        Get list of required input data for this processor
        
        Returns:
            List[str]: List of required input keys
        """
        pass
    
    @abstractmethod
    def get_outputs(self) -> List[str]:
        """
        Get list of output data produced by this processor
        
        Returns:
            List[str]: List of output keys
        """
        pass
    
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
        self.logger.info(f"Starting {self.name} processing for document {context.document_id}")
        self.logger.debug(f"Context: {context}")
    
    def log_processing_end(self, result: ProcessingResult):
        """Log the end of processing"""
        if result.success:
            self.logger.info(f"Completed {self.name} processing in {result.processing_time:.2f}s")
        else:
            self.logger.error(f"Failed {self.name} processing: {result.error}")
    
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
    
    def create_error_result(self, error: ProcessingError, metadata: Dict[str, Any] = None) -> ProcessingResult:
        """Create a failed processing result"""
        return ProcessingResult(
            success=False,
            processor=self.name,
            status=ProcessingStatus.FAILED,
            data={},
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
