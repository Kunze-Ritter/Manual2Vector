"""
Database Service for KR-AI-Engine
Supabase Cloud integration with MCP Server support
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

try:
    from supabase import create_client, Client
    from supabase.client import Client as SupabaseClient
    SUPABASE_AVAILABLE = True
except ImportError:
    SupabaseClient = None
    create_client = None
    Client = None
    SUPABASE_AVAILABLE = False

from core.data_models import (
    DocumentModel, ManufacturerModel, ProductSeriesModel, ProductModel,
    ChunkModel, ImageModel, IntelligenceChunkModel, EmbeddingModel,
    ErrorCodeModel, SearchAnalyticsModel, ProcessingQueueModel,
    AuditLogModel, SystemMetricsModel, PrintDefectModel
)

class DatabaseService:
    """
    Database service for Supabase Cloud integration
    
    Handles all database operations for the KR-AI-Engine:
    - krai_core: manufacturers, products, product_series, documents
    - krai_content: chunks, images, print_defects
    - krai_intelligence: chunks, embeddings, error_codes, search_analytics
    - krai_system: processing_queue, audit_log, system_metrics
    """
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Optional[SupabaseClient] = None
        self.logger = logging.getLogger("krai.database")
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for database service"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - Database - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def connect(self):
        """Connect to Supabase database"""
        try:
            if not SUPABASE_AVAILABLE:
                self.logger.warning("Supabase client not available. Running in mock mode.")
                return
            
            self.client = create_client(self.supabase_url, self.supabase_key)
            self.logger.info("Connected to Supabase database")
            
            # Test connection
            await self.test_connection()
            
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def test_connection(self):
        """Test database connection"""
        try:
            if self.client is None:
                self.logger.info("Database connection test skipped (mock mode)")
                return
            
            # Simple query to test connection
            result = self.client.table("system_metrics").select("id").limit(1).execute()
            self.logger.info("Database connection test successful")
        except Exception as e:
            self.logger.warning(f"Database connection test failed: {e}")
    
    # Document Operations
    async def create_document(self, document: DocumentModel) -> str:
        """Create a new document in krai_core.documents"""
        try:
            if self.client is None:
                # Mock mode for testing
                document_id = f"mock_doc_{document.id}"
                self.logger.info(f"Created document {document_id} (mock)")
                return document_id
            
            # Convert datetime objects to ISO strings for JSON serialization
            document_data = document.dict(exclude_unset=True)
            for key, value in document_data.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    document_data[key] = value.isoformat()
            
            result = self.client.table("documents").insert(document_data).execute()
            document_id = result.data[0]["id"]
            self.logger.info(f"Created document {document_id}")
            return document_id
        except Exception as e:
            self.logger.error(f"Failed to create document: {e}")
            raise
    
    async def get_document(self, document_id: str) -> Optional[DocumentModel]:
        """Get document by ID"""
        try:
            if self.client is None:
                # Mock mode for testing
                return DocumentModel(
                    id=document_id,
                    filename="test_document.pdf",
                    original_filename="test_document.pdf",
                    file_size=1024,
                    file_hash="test_hash_123",
                    document_type="service_manual",
                    language="en",
                    processing_status="pending"
                )
            
            result = self.client.table("documents").select("*").eq("id", document_id).execute()
            if result.data:
                return DocumentModel(**result.data[0])
            return None
        except Exception as e:
            self.logger.error(f"Failed to get document {document_id}: {e}")
            raise
    
    async def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update document"""
        try:
            if self.client is None:
                # Mock mode for testing
                self.logger.info(f"Updated document {document_id} (mock)")
                return True
            
            updates["updated_at"] = datetime.utcnow().isoformat()
            result = self.client.table("documents").update(updates).eq("id", document_id).execute()
            self.logger.info(f"Updated document {document_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update document {document_id}: {e}")
            raise
    
    # Manufacturer Operations
    async def create_manufacturer(self, manufacturer: ManufacturerModel) -> str:
        """Create a new manufacturer"""
        try:
            if self.client is None:
                # Mock mode for testing
                manufacturer_id = f"mock_manufacturer_{manufacturer.id}"
                self.logger.info(f"Created manufacturer {manufacturer_id} (mock)")
                return manufacturer_id
            
            result = self.client.table("manufacturers").insert(manufacturer.dict()).execute()
            manufacturer_id = result.data[0]["id"]
            self.logger.info(f"Created manufacturer {manufacturer_id}")
            return manufacturer_id
        except Exception as e:
            self.logger.error(f"Failed to create manufacturer: {e}")
            raise
    
    async def get_manufacturer_by_name(self, name: str) -> Optional[ManufacturerModel]:
        """Get manufacturer by name"""
        try:
            if self.client is None:
                # Mock mode for testing
                self.logger.info(f"Getting manufacturer {name} (mock)")
                return None  # Return None to trigger creation
            
            result = self.client.table("manufacturers").select("*").eq("name", name).execute()
            if result.data:
                return ManufacturerModel(**result.data[0])
            return None
        except Exception as e:
            self.logger.error(f"Failed to get manufacturer {name}: {e}")
            raise
    
    # Product Series Operations
    async def create_product_series(self, series: ProductSeriesModel) -> str:
        """Create a new product series"""
        try:
            if self.client is None:
                # Mock mode for testing
                series_id = f"mock_series_{series.id}"
                self.logger.info(f"Created product series {series_id} (mock)")
                return series_id
            
            result = self.client.table("product_series").insert(series.dict()).execute()
            series_id = result.data[0]["id"]
            self.logger.info(f"Created product series {series_id}")
            return series_id
        except Exception as e:
            self.logger.error(f"Failed to create product series: {e}")
            raise
    
    async def get_product_series_by_name(self, name: str, manufacturer_id: str) -> Optional[ProductSeriesModel]:
        """Get product series by name and manufacturer"""
        try:
            if self.client is None:
                # Mock mode for testing
                self.logger.info(f"Getting product series {name} (mock)")
                return None  # Return None to trigger creation
            
            result = self.client.table("product_series").select("*").eq("series_name", name).eq("manufacturer_id", manufacturer_id).execute()
            if result.data:
                return ProductSeriesModel(**result.data[0])
            return None
        except Exception as e:
            self.logger.error(f"Failed to get product series {name}: {e}")
            raise
    
    # Product Operations
    async def create_product(self, product: ProductModel) -> str:
        """Create a new product"""
        try:
            if self.client is None:
                # Mock mode for testing
                product_id = f"mock_product_{product.id}"
                self.logger.info(f"Created product {product_id} (mock)")
                return product_id
            
            result = self.client.table("products").insert(product.dict()).execute()
            product_id = result.data[0]["id"]
            self.logger.info(f"Created product {product_id}")
            return product_id
        except Exception as e:
            self.logger.error(f"Failed to create product: {e}")
            raise
    
    async def get_product_by_model(self, model_number: str, manufacturer_id: str) -> Optional[ProductModel]:
        """Get product by model number and manufacturer"""
        try:
            if self.client is None:
                # Mock mode for testing
                self.logger.info(f"Getting product {model_number} (mock)")
                return None  # Return None to trigger creation
            
            result = self.client.table("products").select("*").eq("model_number", model_number).eq("manufacturer_id", manufacturer_id).execute()
            if result.data:
                return ProductModel(**result.data[0])
            return None
        except Exception as e:
            self.logger.error(f"Failed to get product {model_number}: {e}")
            raise
    
    # Content Operations
    async def create_chunk(self, chunk: ChunkModel) -> str:
        """Create a new content chunk"""
        try:
            if self.client is None:
                # Mock mode for testing
                chunk_id = f"mock_chunk_{chunk.id}"
                self.logger.info(f"Created chunk {chunk_id} (mock)")
                return chunk_id
            
            result = self.client.table("chunks").insert(chunk.dict()).execute()
            chunk_id = result.data[0]["id"]
            self.logger.info(f"Created chunk {chunk_id}")
            return chunk_id
        except Exception as e:
            self.logger.error(f"Failed to create chunk: {e}")
            raise
    
    async def create_image(self, image: ImageModel) -> str:
        """Create a new image record"""
        try:
            if self.client is None:
                # Mock mode for testing
                image_id = f"mock_image_{image.id}"
                self.logger.info(f"Created image {image_id} (mock)")
                return image_id
            
            result = self.client.table("images").insert(image.dict()).execute()
            image_id = result.data[0]["id"]
            self.logger.info(f"Created image {image_id}")
            return image_id
        except Exception as e:
            self.logger.error(f"Failed to create image: {e}")
            raise
    
    # Intelligence Operations
    async def create_intelligence_chunk(self, chunk: IntelligenceChunkModel) -> str:
        """Create a new intelligence chunk"""
        try:
            if self.client is None:
                # Mock mode for testing
                chunk_id = f"mock_intelligence_chunk_{chunk.id}"
                self.logger.info(f"Created intelligence chunk {chunk_id} (mock)")
                return chunk_id
            
            result = self.client.table("intelligence_chunks").insert(chunk.dict()).execute()
            chunk_id = result.data[0]["id"]
            self.logger.info(f"Created intelligence chunk {chunk_id}")
            return chunk_id
        except Exception as e:
            self.logger.error(f"Failed to create intelligence chunk: {e}")
            raise
    
    async def create_embedding(self, embedding: EmbeddingModel) -> str:
        """Create a new embedding"""
        try:
            if self.client is None:
                # Mock mode for testing
                embedding_id = f"mock_embedding_{embedding.id}"
                self.logger.info(f"Created embedding {embedding_id} (mock)")
                return embedding_id
            
            result = self.client.table("embeddings").insert(embedding.dict()).execute()
            embedding_id = result.data[0]["id"]
            self.logger.info(f"Created embedding {embedding_id}")
            return embedding_id
        except Exception as e:
            self.logger.error(f"Failed to create embedding: {e}")
            raise
    
    async def create_error_code(self, error_code: ErrorCodeModel) -> str:
        """Create a new error code"""
        try:
            if self.client is None:
                # Mock mode for testing
                error_code_id = f"mock_error_code_{error_code.id}"
                self.logger.info(f"Created error code {error_code_id} (mock)")
                return error_code_id
            
            result = self.client.table("error_codes").insert(error_code.dict()).execute()
            error_code_id = result.data[0]["id"]
            self.logger.info(f"Created error code {error_code_id}")
            return error_code_id
        except Exception as e:
            self.logger.error(f"Failed to create error code: {e}")
            raise
    
    # Vector Search Operations
    async def vector_search(self, query_embedding: List[float], limit: int = 10, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        try:
            if self.client is None:
                # Mock mode for testing
                self.logger.info("Vector search skipped (mock mode)")
                return []
            
            # Use pgvector for similarity search
            result = self.client.rpc(
                "match_documents",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": threshold,
                    "match_count": limit
                }
            ).execute()
            
            self.logger.info(f"Vector search returned {len(result.data)} results")
            return result.data
        except Exception as e:
            self.logger.error(f"Failed to perform vector search: {e}")
            raise
    
    # System Operations
    async def create_processing_queue_item(self, item: ProcessingQueueModel) -> str:
        """Create a new processing queue item"""
        try:
            if self.client is None:
                # Mock mode for testing
                item_id = f"mock_queue_item_{item.id}"
                self.logger.info(f"Created processing queue item {item_id} (mock)")
                return item_id
            
            result = self.client.table("processing_queue").insert(item.dict()).execute()
            item_id = result.data[0]["id"]
            self.logger.info(f"Created processing queue item {item_id}")
            return item_id
        except Exception as e:
            self.logger.error(f"Failed to create processing queue item: {e}")
            raise
    
    async def update_processing_queue_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update processing queue item"""
        try:
            if self.client is None:
                # Mock mode for testing
                self.logger.info(f"Updated processing queue item {item_id} (mock)")
                return True
            
            result = self.client.table("processing_queue").update(updates).eq("id", item_id).execute()
            self.logger.info(f"Updated processing queue item {item_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update processing queue item {item_id}: {e}")
            raise
    
    async def get_pending_queue_items(self, processor_name: str) -> List[ProcessingQueueModel]:
        """Get pending queue items for a processor"""
        try:
            if self.client is None:
                # Mock mode for testing
                self.logger.info(f"Getting pending queue items for {processor_name} (mock)")
                return []
            
            result = self.client.table("processing_queue").select("*").eq("processor_name", processor_name).eq("status", "pending").execute()
            return [ProcessingQueueModel(**item) for item in result.data]
        except Exception as e:
            self.logger.error(f"Failed to get pending queue items for {processor_name}: {e}")
            raise
    
    # Audit Logging
    async def log_audit(self, action: str, entity_type: str, entity_id: str, details: Dict[str, Any] = None):
        """Log audit event - TEMPORARILY DISABLED TO PREVENT SYSTEM FAILURE"""
        try:
            # TEMPORARILY DISABLED - Audit logging causes system failure
            self.logger.info(f"Audit event (disabled): {action} on {entity_type} {entity_id}")
            return
            
            if self.client is None:
                # Mock mode for testing
                self.logger.info(f"Logged audit event: {action} on {entity_type} {entity_id} (mock)")
                return
            
            audit_log = AuditLogModel(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details or {}
            )
            
            # Convert datetime objects to ISO strings for JSON serialization
            audit_data = audit_log.dict(exclude_unset=True)
            for key, value in audit_data.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    audit_data[key] = value.isoformat()
            
            result = self.client.table("audit_log").insert(audit_data).execute()
            self.logger.info(f"Logged audit event: {action} on {entity_type} {entity_id}")
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
    
    # Health Check
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            if self.client is None:
                return {
                    "status": "mock_mode",
                    "response_time_ms": 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            start_time = datetime.utcnow()
            
            # Test basic query
            result = self.client.table("system_metrics").select("id").limit(1).execute()
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "response_time_ms": response_time * 1000,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
