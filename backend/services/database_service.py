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

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    asyncpg = None
    ASYNCPG_AVAILABLE = False

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
    
    def __init__(self, supabase_url: str, supabase_key: str, postgres_url: Optional[str] = None):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.postgres_url = postgres_url  # Direct PostgreSQL connection for cross-schema queries
        self.client: Optional[SupabaseClient] = None
        self.pg_pool: Optional[asyncpg.Pool] = None  # PostgreSQL connection pool
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
        """Connect to Supabase database (PostgREST) and PostgreSQL (direct)"""
        try:
            if not SUPABASE_AVAILABLE:
                raise ImportError("Supabase client not available. Please install: pip install supabase")
            
            # Connect Supabase client (PostgREST API)
            self.client = create_client(self.supabase_url, self.supabase_key)
            self.logger.info("Connected to Supabase database (PostgREST)")
            
            # Connect direct PostgreSQL for cross-schema queries (if URL provided)
            if self.postgres_url and ASYNCPG_AVAILABLE:
                try:
                    self.pg_pool = await asyncpg.create_pool(
                        self.postgres_url,
                        min_size=2,
                        max_size=10,
                        command_timeout=60
                    )
                    self.logger.info("Connected to PostgreSQL database (direct) - Cross-schema queries enabled")
                except Exception as pg_error:
                    self.logger.warning(f"PostgreSQL direct connection failed: {pg_error}. Cross-schema queries will use fallback.")
                    self.pg_pool = None
            
            # Test connection
            await self.test_connection()
            
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise RuntimeError(f"Cannot connect to Supabase database: {e}")
    
    async def test_connection(self):
        """Test database connection"""
        try:
            if self.client is None:
                raise RuntimeError("Database client not connected")
            
            # Simple query to test connection
            result = self.client.table("system_metrics").select("id").limit(1).execute()
            self.logger.info("Database connection test successful")
        except Exception as e:
            self.logger.warning(f"Database connection test failed: {e}")
    
    # Document Operations
    async def create_document(self, document: DocumentModel) -> str:
        """Create a new document in krai_core.documents with deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                document_id = f"mock_doc_{document.id}"
                self.logger.info(f"Created document {document_id} (mock)")
                return document_id
            
            # Check for existing document with same file_hash
            existing_doc = await self.get_document_by_hash(document.file_hash)
            if existing_doc:
                self.logger.info(f"Document with hash {document.file_hash[:16]}... already exists: {existing_doc['id']}")
                return existing_doc['id']
            
            # Convert datetime objects to ISO strings for JSON serialization
            document_data = document.dict(exclude_unset=True)
            for key, value in document_data.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    document_data[key] = value.isoformat()
            
            result = self.client.table("documents").insert(document_data).execute()
            document_id = result.data[0]["id"]
            self.logger.info(f"Created new document {document_id}")
            return document_id
        except Exception as e:
            self.logger.error(f"Failed to create document: {e}")
            raise
    
    async def get_document_by_hash(self, file_hash: str) -> Optional[Dict]:
        """Get document by file hash for deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                return None
            
            result = self.client.table("documents").select("id, filename, file_hash, created_at").eq("file_hash", file_hash).execute()
            if result.data:
                doc_data = result.data[0]
                self.logger.info(f"Found existing document with hash {file_hash[:16]}...")
                return doc_data
            else:
                return None
        except Exception as e:
            self.logger.error(f"Failed to get document by hash: {e}")
            return None

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
        """Create a new manufacturer with deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                manufacturer_id = f"mock_manufacturer_{manufacturer.id}"
                self.logger.info(f"Created manufacturer {manufacturer_id} (mock)")
                return manufacturer_id
            
            # Check for existing manufacturer with same name
            existing_manufacturer = await self.get_manufacturer_by_name(manufacturer.name)
            if existing_manufacturer:
                self.logger.info(f"Manufacturer '{manufacturer.name}' already exists: {existing_manufacturer['id']}")
                return existing_manufacturer['id']
            
            # Convert datetime objects to ISO strings for JSON serialization
            manufacturer_data = manufacturer.dict(exclude_unset=True)
            for key, value in manufacturer_data.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    manufacturer_data[key] = value.isoformat()
            
            result = self.client.table("manufacturers").insert(manufacturer_data).execute()
            manufacturer_id = result.data[0]["id"]
            self.logger.info(f"Created new manufacturer {manufacturer_id}")
            return manufacturer_id
        except Exception as e:
            self.logger.error(f"Failed to create manufacturer: {e}")
            raise
    
    async def get_manufacturer_by_name(self, name: str) -> Optional[Dict]:
        """Get manufacturer by name for deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                return None
            
            result = self.client.table("manufacturers").select("id, name").eq("name", name).execute()
            if result.data:
                manufacturer_data = result.data[0]
                self.logger.info(f"Found existing manufacturer: {name}")
                return manufacturer_data
            return None
        except Exception as e:
            self.logger.error(f"Failed to get manufacturer {name}: {e}")
            return None
    
    # Product Series Operations
    async def create_product_series(self, series: ProductSeriesModel) -> str:
        """Create a new product series with deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                series_id = f"mock_series_{series.id}"
                self.logger.info(f"Created product series {series_id} (mock)")
                return series_id
            
            # Check for existing product series with same name and manufacturer
            existing_series = await self.get_product_series_by_name(series.series_name, series.manufacturer_id)
            if existing_series:
                self.logger.info(f"Product series '{series.series_name}' already exists: {existing_series['id']}")
                return existing_series['id']
            
            # Convert datetime objects to ISO strings for JSON serialization
            series_data = series.dict(exclude_unset=True)
            for key, value in series_data.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    series_data[key] = value.isoformat()
            
            result = self.client.table("product_series").insert(series_data).execute()
            series_id = result.data[0]["id"]
            self.logger.info(f"Created new product series {series_id}")
            return series_id
        except Exception as e:
            self.logger.error(f"Failed to create product series: {e}")
            raise
    
    async def get_product_series_by_name(self, name: str, manufacturer_id: str) -> Optional[Dict]:
        """Get product series by name and manufacturer for deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                return None
            
            result = self.client.table("product_series").select("id, series_name").eq("series_name", name).eq("manufacturer_id", manufacturer_id).execute()
            if result.data:
                series_data = result.data[0]
                self.logger.info(f"Found existing product series: {name}")
                return series_data
            return None
        except Exception as e:
            self.logger.error(f"Failed to get product series {name}: {e}")
            return None
    
    # Product Operations
    async def create_product(self, product: ProductModel) -> str:
        """Create a new product with deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                product_id = f"mock_product_{product.id}"
                self.logger.info(f"Created product {product_id} (mock)")
                return product_id
            
            # Check for existing product with same model and manufacturer
            existing_product = await self.get_product_by_model(product.model_number, product.manufacturer_id)
            if existing_product:
                self.logger.info(f"Product '{product.model_number}' already exists: {existing_product['id']}")
                return existing_product['id']
            
            # Convert datetime objects to ISO strings for JSON serialization
            product_data = product.dict(exclude_unset=True)
            for key, value in product_data.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    product_data[key] = value.isoformat()
            
            result = self.client.table("products").insert(product_data).execute()
            product_id = result.data[0]["id"]
            self.logger.info(f"Created new product {product_id}")
            return product_id
        except Exception as e:
            self.logger.error(f"Failed to create product: {e}")
            raise
    
    async def get_product_by_model(self, model_number: str, manufacturer_id: str) -> Optional[Dict]:
        """Get product by model number and manufacturer for deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                return None
            
            result = self.client.table("products").select("id, model_number").eq("model_number", model_number).eq("manufacturer_id", manufacturer_id).execute()
            if result.data:
                product_data = result.data[0]
                self.logger.info(f"Found existing product: {model_number}")
                return product_data
            return None
        except Exception as e:
            self.logger.error(f"Failed to get product {model_number}: {e}")
            return None
    
    # Content Operations
    async def create_chunk_async(self, chunk_data: Dict[str, Any]) -> str:
        """Create chunk from dictionary data (for parallel processing)"""
        try:
            if self.client is None:
                # Mock mode for testing
                chunk_id = f"mock_chunk_{chunk_data.get('chunk_index', 'unknown')}"
                self.logger.info(f"Created chunk {chunk_id} (mock)")
                return chunk_id
            
            existing_chunk = await self.get_chunk_by_document_and_index(
                chunk_data['document_id'], chunk_data['chunk_index']
            )
            if existing_chunk:
                self.logger.info(f"Chunk {chunk_data['chunk_index']} for document {chunk_data['document_id']} already exists: {existing_chunk['id']}")
                return existing_chunk['id']
            
            # Remove metadata from main insert (store separately if needed)
            chunk_insert_data = {k: v for k, v in chunk_data.items() if k != 'metadata'}
            
            result = self.client.table("chunks").insert(chunk_insert_data).execute()
            chunk_id = result.data[0]["id"]
            self.logger.info(f"Created new smart chunk {chunk_id} (page: {chunk_data.get('page_number', 'N/A')}, section: {chunk_data.get('section_title', 'N/A')})")
            return chunk_id
        except Exception as e:
            self.logger.error(f"Failed to create chunk: {e}")
            raise

    async def create_chunk(self, chunk: ChunkModel) -> str:
        """Create a new content chunk with deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                chunk_id = f"mock_chunk_{chunk.id}"
                self.logger.info(f"Created chunk {chunk_id} (mock)")
                return chunk_id
            
            # Check for existing chunk with same document_id and chunk_index
            existing_chunk = await self.get_chunk_by_document_and_index(chunk.document_id, chunk.chunk_index)
            if existing_chunk:
                self.logger.info(f"Chunk {chunk.chunk_index} for document {chunk.document_id} already exists: {existing_chunk['id']}")
                return existing_chunk['id']
            
            # Convert datetime objects to ISO strings for JSON serialization
            chunk_data = chunk.dict(exclude_unset=True)
            for key, value in chunk_data.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    chunk_data[key] = value.isoformat()
            
            result = self.client.table("chunks").insert(chunk_data).execute()
            chunk_id = result.data[0]["id"]
            self.logger.info(f"Created new chunk {chunk_id}")
            return chunk_id
        except Exception as e:
            self.logger.error(f"Failed to create chunk: {e}")
            raise
    
    async def get_chunk_by_document_and_index(self, document_id: str, chunk_index: int) -> Optional[Dict]:
        """Get chunk by document_id and chunk_index for deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                return None
            
            result = self.client.table("chunks").select("id, document_id, chunk_index").eq("document_id", document_id).eq("chunk_index", chunk_index).execute()
            if result.data:
                chunk_data = result.data[0]
                self.logger.info(f"Found existing chunk: {chunk_index} for document {document_id}")
                return chunk_data
            return None
        except Exception as e:
            self.logger.error(f"Failed to get chunk by document and index: {e}")
            return None
    
    async def create_image(self, image: ImageModel) -> str:
        """Create a new image record with deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                image_id = f"mock_image_{image.id}"
                self.logger.info(f"Created image {image_id} (mock)")
                return image_id
            
            # Check for existing image with same file_hash
            existing_image = await self.get_image_by_hash(image.file_hash)
            if existing_image:
                self.logger.info(f"Image with hash {image.file_hash[:16]}... already exists: {existing_image['id']}")
                return existing_image['id']
            
            # Convert datetime objects to ISO strings for JSON serialization
            image_data = image.dict(exclude_unset=True)
            for key, value in image_data.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    image_data[key] = value.isoformat()
            
            result = self.client.table("images").insert(image_data).execute()
            image_id = result.data[0]["id"]
            self.logger.info(f"Created new image {image_id}")
            return image_id
        except Exception as e:
            self.logger.error(f"Failed to create image: {e}")
            raise
    
    async def get_image_by_hash(self, file_hash: str) -> Optional[Dict]:
        """Get image by file_hash for deduplication - Direct SQL for cross-schema access"""
        try:
            if self.client is None:
                # Mock mode for testing
                return None
            
            # Use direct PostgreSQL connection for cross-schema query
            if self.pg_pool:
                async with self.pg_pool.acquire() as conn:
                    result = await conn.fetchrow(
                        """
                        SELECT id, filename, file_hash, created_at, document_id, storage_url
                        FROM krai_content.images
                        WHERE file_hash = $1
                        LIMIT 1
                        """,
                        file_hash
                    )
                    
                    if result:
                        image_data = dict(result)
                        self.logger.info(f"Found existing image with hash {file_hash[:16]}...")
                        return image_data
            else:
                # Fallback: Try RPC if available, otherwise return None
                self.logger.debug(f"Direct PostgreSQL not available, skipping image deduplication check")
            
            return None
        except Exception as e:
            self.logger.error(f"Failed to get image by hash {file_hash[:16]}...: {e}")
            return None
    
    # Intelligence Operations
    async def create_intelligence_chunk(self, chunk: IntelligenceChunkModel) -> str:
        """Create a new intelligence chunk with deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                chunk_id = f"mock_intelligence_chunk_{chunk.id}"
                self.logger.info(f"Created intelligence chunk {chunk_id} (mock)")
                return chunk_id
            
            # Check for existing intelligence chunk with same chunk_id
            existing_chunk = await self.get_intelligence_chunk_by_chunk_id(chunk.chunk_id)
            if existing_chunk:
                self.logger.info(f"Intelligence chunk for chunk {chunk.chunk_id} already exists: {existing_chunk['id']}")
                return existing_chunk['id']
            
            result = self.client.table("intelligence_chunks").insert(chunk.dict()).execute()
            chunk_id = result.data[0]["id"]
            self.logger.info(f"Created new intelligence chunk {chunk_id}")
            return chunk_id
        except Exception as e:
            self.logger.error(f"Failed to create intelligence chunk: {e}")
            raise
    
    async def get_intelligence_chunk_by_chunk_id(self, chunk_id: str) -> Optional[Dict]:
        """Get intelligence chunk by chunk_id for deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                return None
            
            result = self.client.table("intelligence_chunks").select("id, chunk_id").eq("chunk_id", chunk_id).execute()
            if result.data:
                chunk_data = result.data[0]
                self.logger.info(f"Found existing intelligence chunk for chunk {chunk_id}")
                return chunk_data
            return None
        except Exception as e:
            self.logger.error(f"Failed to get intelligence chunk by chunk_id: {e}")
            return None
    
    async def create_embedding(self, embedding: EmbeddingModel) -> str:
        """Create a new embedding with deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                embedding_id = f"mock_embedding_{embedding.id}"
                self.logger.info(f"Created embedding {embedding_id} (mock)")
                return embedding_id
            
            # Check for existing embedding with same chunk_id
            existing_embedding = await self.get_embedding_by_chunk_id(embedding.chunk_id)
            if existing_embedding:
                self.logger.info(f"Embedding for chunk {embedding.chunk_id} already exists: {existing_embedding['id']}")
                return existing_embedding['id']
            
            # Convert datetime objects to ISO strings for JSON serialization
            embedding_data = embedding.dict(exclude_unset=True)
            for key, value in embedding_data.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    embedding_data[key] = value.isoformat()
            
            result = self.client.table("embeddings").insert(embedding_data).execute()
            embedding_id = result.data[0]["id"]
            self.logger.info(f"Created new embedding {embedding_id}")
            return embedding_id
        except Exception as e:
            self.logger.error(f"Failed to create embedding: {e}")
            raise
    
    async def get_embedding_by_chunk_id(self, chunk_id: str) -> Optional[Dict]:
        """Get embedding by chunk_id for deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                return None
            
            result = self.client.table("embeddings").select("id, chunk_id").eq("chunk_id", chunk_id).execute()
            if result.data:
                embedding_data = result.data[0]
                self.logger.info(f"Found existing embedding for chunk {chunk_id}")
                return embedding_data
            return None
        except Exception as e:
            self.logger.error(f"Failed to get embedding by chunk_id: {e}")
            return None
    
    async def create_error_code(self, error_code: ErrorCodeModel) -> str:
        """Create a new error code with deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                error_code_id = f"mock_error_code_{error_code.id}"
                self.logger.info(f"Created error code {error_code_id} (mock)")
                return error_code_id
            
            # Check for existing error code with same error_code
            existing_error_code = await self.get_error_code_by_code(error_code.error_code)
            if existing_error_code:
                self.logger.info(f"Error code '{error_code.error_code}' already exists: {existing_error_code['id']}")
                return existing_error_code['id']
            
            # Convert datetime objects to ISO strings for JSON serialization
            error_code_data = error_code.dict(exclude_unset=True)
            for key, value in error_code_data.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    error_code_data[key] = value.isoformat()
            
            result = self.client.table("error_codes").insert(error_code_data).execute()
            error_code_id = result.data[0]["id"]
            self.logger.info(f"Created new error code {error_code_id}")
            return error_code_id
        except Exception as e:
            self.logger.error(f"Failed to create error code: {e}")
            raise
    
    async def get_error_code_by_code(self, error_code: str) -> Optional[Dict]:
        """Get error code by error_code for deduplication"""
        try:
            if self.client is None:
                # Mock mode for testing
                return None
            
            result = self.client.table("error_codes").select("id, error_code").eq("error_code", error_code).execute()
            if result.data:
                error_code_data = result.data[0]
                self.logger.info(f"Found existing error code: {error_code}")
                return error_code_data
            return None
        except Exception as e:
            self.logger.error(f"Failed to get error code by code: {e}")
            return None
    
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
    
    async def create_search_analytics(self, analytics: SearchAnalyticsModel) -> str:
        """Create search analytics entry"""
        try:
            if self.client is None:
                # Mock mode for testing
                analytics_id = f"mock_analytics_{analytics.id}"
                self.logger.info(f"Created search analytics {analytics_id} (mock)")
                return analytics_id
            
            # Convert datetime objects to ISO strings for JSON serialization
            analytics_data = analytics.dict(exclude_unset=True)
            for key, value in analytics_data.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    analytics_data[key] = value.isoformat()
            
            result = self.client.table("search_analytics").insert(analytics_data).execute()
            analytics_id = result.data[0]["id"]
            self.logger.info(f"Created search analytics {analytics_id}")
            return analytics_id
        except Exception as e:
            self.logger.error(f"Failed to create search analytics: {e}")
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
    
    async def get_chunks_by_document_id(self, document_id: str) -> List[ChunkModel]:
        """Get all chunks for a document"""
        try:
            result = self.client.table('chunks').select('*').eq('document_id', document_id).order('chunk_index').execute()
            
            chunks = []
            for chunk_data in result.data:
                chunks.append(ChunkModel(**chunk_data))
            return chunks
            
        except Exception as e:
            self.logger.error(f"Failed to get chunks by document ID: {e}")
            return []
    
    # Cross-Schema Helper Methods (using direct PostgreSQL)
    async def count_chunks_by_document(self, document_id: str) -> int:
        """Count chunks for a document - Direct SQL for krai_content schema"""
        try:
            if self.pg_pool:
                async with self.pg_pool.acquire() as conn:
                    count = await conn.fetchval(
                        "SELECT COUNT(*) FROM krai_content.chunks WHERE document_id = $1",
                        document_id
                    )
                    return count or 0
            return 0
        except Exception as e:
            self.logger.error(f"Failed to count chunks: {e}")
            return 0
    
    async def count_images_by_document(self, document_id: str) -> int:
        """Count images for a document - Direct SQL for krai_content schema"""
        try:
            if self.pg_pool:
                async with self.pg_pool.acquire() as conn:
                    count = await conn.fetchval(
                        "SELECT COUNT(*) FROM krai_content.images WHERE document_id = $1",
                        document_id
                    )
                    return count or 0
            return 0
        except Exception as e:
            self.logger.error(f"Failed to count images: {e}")
            return 0
    
    async def check_embeddings_exist(self, document_id: str) -> bool:
        """Check if embeddings exist for a document - Direct SQL across schemas"""
        try:
            if self.pg_pool:
                async with self.pg_pool.acquire() as conn:
                    exists = await conn.fetchval(
                        """
                        SELECT EXISTS(
                            SELECT 1 
                            FROM krai_intelligence.embeddings e
                            JOIN krai_content.chunks c ON e.chunk_id = c.id
                            WHERE c.document_id = $1
                        )
                        """,
                        document_id
                    )
                    return exists or False
            return False
        except Exception as e:
            self.logger.error(f"Failed to check embeddings: {e}")
            return False
