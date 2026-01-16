"""
Database Adapter Base Class

Defines the interface for all database adapters in the KR-AI-Engine.
All database adapters must inherit from this base class and implement its methods.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import logging

from backend.core.data_models import (
    DocumentModel, ManufacturerModel, ProductSeriesModel, ProductModel,
    ChunkModel, ImageModel, IntelligenceChunkModel, EmbeddingModel,
    ErrorCodeModel, SearchAnalyticsModel, ProcessingQueueModel,
    AuditLogModel, SystemMetricsModel, PrintDefectModel
)


class DatabaseAdapter(ABC):
    """
    Abstract base class for all database adapters.
    
    Defines the interface that all database adapters must implement.
    Supports PostgreSQL database backend.
    """
    
    def __init__(self):
        """Initialize the database adapter with a logger."""
        self.logger = logging.getLogger(self.__class__.__module__)
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the database adapter."""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    # Connection Management
    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection(s)."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the database connection."""
        pass
    
    # Document Operations
    @abstractmethod
    async def create_document(self, document: DocumentModel) -> str:
        """Create a new document with deduplication."""
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[DocumentModel]:
        """Get a document by ID."""
        pass
    
    @abstractmethod
    async def get_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get document by file hash for deduplication."""
        pass
    
    @abstractmethod
    async def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update a document."""
        pass
    
    # Manufacturer Operations
    @abstractmethod
    async def create_manufacturer(self, manufacturer: ManufacturerModel) -> str:
        """Create a new manufacturer with deduplication."""
        pass
    
    @abstractmethod
    async def get_manufacturer_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get manufacturer by name for deduplication."""
        pass
    
    # Product Series Operations
    @abstractmethod
    async def create_product_series(self, series: ProductSeriesModel) -> str:
        """Create a new product series with deduplication."""
        pass
    
    @abstractmethod
    async def get_product_series_by_name(self, name: str, manufacturer_id: str) -> Optional[Dict[str, Any]]:
        """Get product series by name and manufacturer for deduplication."""
        pass
    
    # Product Operations
    @abstractmethod
    async def create_product(self, product: ProductModel) -> str:
        """Create a new product with deduplication."""
        pass
    
    @abstractmethod
    async def get_product_by_model(self, model_number: str, manufacturer_id: str) -> Optional[Dict[str, Any]]:
        """Get product by model number and manufacturer for deduplication."""
        pass
    
    # Chunk Operations
    @abstractmethod
    async def create_chunk(self, chunk: ChunkModel) -> str:
        """Create a new content chunk with deduplication."""
        pass
    
    @abstractmethod
    async def create_chunk_async(self, chunk_data: Dict[str, Any]) -> str:
        """Create chunk from dictionary data (for parallel processing)."""
        pass
    
    @abstractmethod
    async def get_chunk_by_document_and_index(self, document_id: str, chunk_index: int) -> Optional[Dict[str, Any]]:
        """Get chunk by document_id and chunk_index for deduplication."""
        pass
    
    # Image Operations
    @abstractmethod
    async def create_image(self, image: ImageModel) -> str:
        """Create a new image with deduplication."""
        pass
    
    @abstractmethod
    async def get_image_by_hash(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """Get image by hash for deduplication."""
        pass
    
    @abstractmethod
    async def get_images_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all images for a document."""
        pass
    
    # Intelligence Chunk Operations
    @abstractmethod
    async def create_intelligence_chunk(self, chunk: IntelligenceChunkModel) -> str:
        """Create a new intelligence chunk."""
        pass
    
    # Embedding Operations
    @abstractmethod
    async def create_embedding(self, embedding: EmbeddingModel) -> str:
        """Create a new embedding."""
        pass
    
    @abstractmethod
    async def get_embedding_by_chunk_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get embedding by chunk_id for deduplication."""
        pass
    
    @abstractmethod
    async def get_embeddings_by_chunk_ids(self, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple embeddings by chunk_ids (batch query for performance)."""
        pass
    
    # Search Operations
    @abstractmethod
    async def search_embeddings(
        self, 
        query_embedding: List[float], 
        limit: int = 10,
        match_threshold: float = 0.7,
        match_count: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar embeddings using vector search."""
        pass
    
    # Error Code Operations
    @abstractmethod
    async def create_error_code(self, error_code: ErrorCodeModel) -> str:
        """Create a new error code."""
        pass
    
    # Search Analytics Operations
    @abstractmethod
    async def log_search_analytics(self, analytics: SearchAnalyticsModel) -> str:
        """Log search analytics."""
        pass
    
    # Processing Queue Operations
    @abstractmethod
    async def create_processing_queue_item(self, item: ProcessingQueueModel) -> str:
        """Create a new processing queue item."""
        pass
    
    @abstractmethod
    async def update_processing_queue_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update a processing queue item."""
        pass
    
    # System Operations
    @abstractmethod
    async def log_audit_event(self, event: AuditLogModel) -> str:
        """Log an audit event."""
        pass
    
    @abstractmethod
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status including metrics."""
        pass
    
    # Cross-Schema Helper Methods
    @abstractmethod
    async def count_chunks_by_document(self, document_id: str) -> int:
        """Count chunks for a document (cross-schema query)."""
        pass
    
    @abstractmethod
    async def count_images_by_document(self, document_id: str) -> int:
        """Count images for a document (cross-schema query)."""
        pass
    
    @abstractmethod
    async def check_embedding_exists(self, chunk_id: str) -> bool:
        """Check if embedding exists for chunk_id (cross-schema query)."""
        pass
    
    @abstractmethod
    async def count_links_by_document(self, document_id: str) -> int:
        """Count links for a document (cross-schema query)."""
        pass
    
    # Link Operations
    @abstractmethod
    async def create_link(self, link_data: Dict[str, Any]) -> str:
        """Create or update a link (upsert)."""
        pass
    
    # Video Operations
    @abstractmethod
    async def create_video(self, video_data: Dict[str, Any]) -> str:
        """Create or update a video (upsert)."""
        pass
    
    # Print Defect Operations
    @abstractmethod
    async def create_print_defect(self, defect: PrintDefectModel) -> str:
        """Create a new print defect."""
        pass
    
    # Batch Operations (Optional - for performance optimization)
    async def execute_batch(self, queries: List[str], params: List[List[Any]]) -> List[Any]:
        """
        Execute a batch of SQL queries with parameters.
        Optional method - adapters can override for performance optimization.
        """
        raise NotImplementedError("Batch operations not implemented for this adapter")
    
    # Generic Query Execution
    @abstractmethod
    async def execute_query(
        self,
        query: str,
        params: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw SQL query with parameters.
        
        Args:
            query: SQL query string with %s placeholders
            params: List of parameters for the query
            
        Returns:
            List of dictionaries representing query results
        """
        pass
    
    @abstractmethod
    async def fetch_one(
        self,
        query: str,
        params: Optional[List[Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single row from the database.
        
        Args:
            query: SQL query string with $1, $2, etc. placeholders (PostgreSQL style)
            params: List of parameters for the query
            
        Returns:
            Dictionary representing the row, or None if no row found
        """
        pass
    
    @abstractmethod
    async def fetch_all(
        self,
        query: str,
        params: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch multiple rows from the database.
        
        Args:
            query: SQL query string with $1, $2, etc. placeholders (PostgreSQL style)
            params: List of parameters for the query
            
        Returns:
            List of dictionaries representing the rows
        """
        pass
    
    # RPC Method (Optional - PostgreSQL functions)
    async def rpc(
        self,
        function_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a database RPC function (PostgreSQL stored procedures).
        
        Optional method - only implemented by adapters that support RPC.
        PostgreSQL adapter can implement this for stored procedures.
        
        Args:
            function_name: Name of the RPC function
            params: Parameters for the function
            
        Returns:
            Function result
            
        Raises:
            NotImplementedError: If adapter doesn't support RPC
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support RPC calls. "
            "Use direct SQL queries or implement stored procedures."
        )
