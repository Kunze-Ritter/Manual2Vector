"""
Production Database Service for KR-AI-Engine
Supabase Cloud integration - NO MOCK MODE
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
    raise ImportError("Supabase client not available. Please install: pip install supabase")

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
    Production Database service for Supabase Cloud integration
    
    Handles all database operations for the KR-AI-Engine:
    - krai_core: manufacturers, products, product_series, documents
    - krai_content: chunks, images, print_defects
    - krai_intelligence: chunks, embeddings, error_codes, search_analytics
    - krai_system: processing_queue, audit_log, system_metrics
    """
    
    def __init__(self, supabase_url: str, supabase_key: str, postgres_url: Optional[str] = None, service_role_key: Optional[str] = None):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.postgres_url = postgres_url  # Direct PostgreSQL connection for cross-schema queries
        self.service_role_key = service_role_key  # Service role for elevated permissions
        self.client: Optional[SupabaseClient] = None
        self.service_client: Optional[SupabaseClient] = None  # Service role client for cross-schema
        self.pg_pool: Optional[asyncpg.Pool] = None  # PostgreSQL connection pool
        self.logger = logging.getLogger("krai.database")
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for database service"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
            
            # Connect with Service Role Key for cross-schema queries (alternative to asyncpg)
            if self.service_role_key:
                try:
                    self.service_client = create_client(self.supabase_url, self.service_role_key)
                    self.logger.info("Connected with Service Role Key - Cross-schema via PostgREST enabled ✅")
                except Exception as srv_error:
                    self.logger.warning(f"Service role client init failed: {srv_error}")
                    self.service_client = None
            
            # Connect direct PostgreSQL for cross-schema queries (if URL provided)
            if self.postgres_url and ASYNCPG_AVAILABLE:
                try:
                    self.pg_pool = await asyncpg.create_pool(
                        self.postgres_url,
                        min_size=2,
                        max_size=10,
                        command_timeout=60
                    )
                    self.logger.info("Connected to PostgreSQL database (direct) - asyncpg pool enabled ✅")
                except Exception as pg_error:
                    self.logger.warning(f"PostgreSQL direct connection failed: {pg_error}. Using PostgREST fallback.")
                    self.pg_pool = None
            
            # Log cross-schema capability status
            if not self.pg_pool and not self.service_client:
                self.logger.warning("⚠️  No cross-schema access available - Image deduplication will be limited")
                self.logger.info("💡 Add POSTGRES_URL or SUPABASE_SERVICE_ROLE_KEY to enable cross-schema queries")
            
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
    
    async def create_document(self, document: DocumentModel) -> str:
        """Create a new document"""
        document_data = document.model_dump(mode='json')
        
        try:
            # Insert document into krai_core.documents
            result = self.client.table('documents').insert(document_data).execute()
            
            if result.data:
                document_id = result.data[0]['id']
                self.logger.info(f"Created document {document_id}")
                return document_id
            else:
                raise Exception("Failed to create document")
                
        except Exception as e:
            self.logger.error(f"Failed to create document: {e}")
            raise RuntimeError(f"Cannot create document in database: {e}")
    
    async def get_document(self, document_id: str) -> Optional[DocumentModel]:
        """Get document by ID"""
        try:
            result = self.client.table('documents').select('*').eq('id', document_id).execute()
            
            if result.data:
                return DocumentModel(**result.data[0])
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get document: {e}")
            return None
    
    async def get_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get document by file hash for deduplication"""
        try:
            result = self.client.table('documents').select('*').eq('file_hash', file_hash).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Failed to get document by hash {file_hash[:16]}...: {e}")
            return None
    
    async def get_image_by_hash(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """Get image by hash for deduplication"""
        try:
            result = self.client.table('images').select('*').eq('image_hash', image_hash).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Failed to get image by hash {image_hash[:16]}...: {e}")
            return None
    
    async def get_embedding_by_chunk_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get embedding by chunk_id for deduplication"""
        try:
            result = self.client.table('embeddings').select('*').eq('chunk_id', chunk_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Failed to get embedding by chunk_id {chunk_id[:16]}...: {e}")
            return None
    
    async def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update document"""
        try:
            result = self.client.table('documents').update(updates).eq('id', document_id).execute()
            
            if result.data:
                self.logger.info(f"Updated document {document_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to update document: {e}")
            return False
    
    async def create_manufacturer(self, manufacturer: ManufacturerModel) -> str:
        """Create a new manufacturer with deduplication"""
        # Check if manufacturer already exists (DEDUPLICATION!)
        existing_manufacturer = await self.get_manufacturer_by_name(manufacturer.name)
        if existing_manufacturer:
            self.logger.info(f"Manufacturer '{manufacturer.name}' already exists: {existing_manufacturer.id}")
            return existing_manufacturer.id
        
        manufacturer_data = manufacturer.model_dump(mode='json')
        
        try:
            result = self.client.table('manufacturers').insert(manufacturer_data).execute()
            
            if result.data:
                manufacturer_id = result.data[0]['id']
                self.logger.info(f"Created manufacturer {manufacturer_id}")
                return manufacturer_id
            else:
                raise Exception("Failed to create manufacturer")
                
        except Exception as e:
            self.logger.error(f"Failed to create manufacturer: {e}")
            raise RuntimeError(f"Cannot create manufacturer in database: {e}")
    
    async def get_manufacturer_by_name(self, name: str) -> Optional[ManufacturerModel]:
        """Get manufacturer by name"""
        try:
            result = self.client.table('manufacturers').select('*').eq('name', name).execute()
            
            if result.data:
                return ManufacturerModel(**result.data[0])
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get manufacturer: {e}")
            return None
    
    async def create_product_series(self, series: ProductSeriesModel) -> str:
        """Create a new product series"""
        series_data = series.model_dump(mode='json')
        
        try:
            result = self.client.table('product_series').insert(series_data).execute()
            
            if result.data:
                series_id = result.data[0]['id']
                self.logger.info(f"Created product series {series_id}")
                return series_id
            else:
                raise Exception("Failed to create product series")
                
        except Exception as e:
            self.logger.error(f"Failed to create product series: {e}")
            raise RuntimeError(f"Cannot create product series in database: {e}")
    
    async def get_product_series_by_name(self, name: str, manufacturer_id: str) -> Optional[ProductSeriesModel]:
        """Get product series by name and manufacturer"""
        try:
            result = self.client.table('product_series').select('*').eq('name', name).eq('manufacturer_id', manufacturer_id).execute()
            
            if result.data:
                return ProductSeriesModel(**result.data[0])
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get product series: {e}")
            return None
    
    async def create_product(self, product: ProductModel) -> str:
        """Create a new product"""
        product_data = product.model_dump(mode='json')
        
        try:
            result = self.client.table('products').insert(product_data).execute()
            
            if result.data:
                product_id = result.data[0]['id']
                self.logger.info(f"Created product {product_id}")
                return product_id
            else:
                raise Exception("Failed to create product")
                
        except Exception as e:
            self.logger.error(f"Failed to create product: {e}")
            raise RuntimeError(f"Cannot create product in database: {e}")
    
    async def create_chunk(self, chunk: ChunkModel) -> str:
        """Create a new chunk"""
        chunk_data = chunk.model_dump(mode='json')
        
        try:
            result = self.client.table('chunks').insert(chunk_data).execute()
            
            if result.data:
                chunk_id = result.data[0]['id']
                self.logger.info(f"Created chunk {chunk_id}")
                return chunk_id
            else:
                raise Exception("Failed to create chunk")
                
        except Exception as e:
            self.logger.error(f"Failed to create chunk: {e}")
            raise RuntimeError(f"Cannot create chunk in database: {e}")
    
    async def create_chunk_async(self, chunk: ChunkModel) -> str:
        """Create a new chunk asynchronously"""
        chunk_data = chunk.model_dump(mode='json')
        
        try:
            result = self.client.table('chunks').insert(chunk_data).execute()
            
            if result.data:
                chunk_id = result.data[0]['id']
                return chunk_id
            else:
                raise Exception("Failed to create chunk")
                
        except Exception as e:
            self.logger.error(f"Failed to create chunk: {e}")
            raise RuntimeError(f"Cannot create chunk in database: {e}")
    
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
    
    async def create_image(self, image: ImageModel) -> str:
        """Create a new image"""
        image_data = image.model_dump(mode='json')
        
        try:
            result = self.client.table('images').insert(image_data).execute()
            
            if result.data:
                image_id = result.data[0]['id']
                self.logger.info(f"Created image {image_id}")
                return image_id
            else:
                raise Exception("Failed to create image")
                
        except Exception as e:
            self.logger.error(f"Failed to create image: {e}")
            raise RuntimeError(f"Cannot create image in database: {e}")
    
    async def create_intelligence_chunk(self, chunk: IntelligenceChunkModel) -> str:
        """Create a new intelligence chunk"""
        chunk_data = chunk.model_dump(mode='json')
        
        try:
            result = self.client.table('intelligence_chunks').insert(chunk_data).execute()
            
            if result.data:
                chunk_id = result.data[0]['id']
                self.logger.info(f"Created intelligence chunk {chunk_id}")
                return chunk_id
            else:
                raise Exception("Failed to create intelligence chunk")
                
        except Exception as e:
            self.logger.error(f"Failed to create intelligence chunk: {e}")
            raise RuntimeError(f"Cannot create intelligence chunk in database: {e}")
    
    async def create_embedding(self, embedding: EmbeddingModel) -> str:
        """Create a new embedding"""
        embedding_data = embedding.model_dump(mode='json')
        
        try:
            result = self.client.table('embeddings').insert(embedding_data).execute()
            
            if result.data:
                embedding_id = result.data[0]['id']
                self.logger.info(f"Created embedding {embedding_id}")
                return embedding_id
            else:
                raise Exception("Failed to create embedding")
                
        except Exception as e:
            self.logger.error(f"Failed to create embedding: {e}")
            raise RuntimeError(f"Cannot create embedding in database: {e}")
    
    async def search_embeddings(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Search embeddings using vector similarity"""
        try:
            # Use Supabase's vector search
            result = self.client.rpc('search_embeddings', {
                'query_vector': query_vector,
                'match_threshold': 0.7,
                'match_count': limit
            }).execute()
            
            return result.data or []
            
        except Exception as e:
            self.logger.error(f"Failed to search embeddings: {e}")
            return []
    
    async def create_error_code(self, error_code: ErrorCodeModel) -> str:
        """Create a new error code in krai_intelligence.error_codes"""
        error_code_data = error_code.model_dump(mode='json')
        
        try:
            # Use service_client for cross-schema access
            client = self.service_client if self.service_client else self.client
            
            result = client.schema('krai_intelligence').table('error_codes').insert(error_code_data).execute()
            
            if result.data:
                error_code_id = result.data[0]['id']
                self.logger.info(f"Created error code {error_code_id}: {error_code_data.get('error_code')}")
                return error_code_id
            else:
                raise Exception("Failed to create error code")
                
        except Exception as e:
            self.logger.error(f"Failed to create error code: {e}")
            raise RuntimeError(f"Cannot create error code in database: {e}")
    
    async def create_search_analytics(self, analytics: SearchAnalyticsModel) -> str:
        """Create a new search analytics record"""
        analytics_data = analytics.model_dump(mode='json')
        
        try:
            result = self.client.table('search_analytics').insert(analytics_data).execute()
            
            if result.data:
                analytics_id = result.data[0]['id']
                self.logger.info(f"Created search analytics {analytics_id}")
                return analytics_id
            else:
                raise Exception("Failed to create search analytics")
                
        except Exception as e:
            self.logger.error(f"Failed to create search analytics: {e}")
            raise RuntimeError(f"Cannot create search analytics in database: {e}")
    
    async def create_processing_queue_item(self, item: ProcessingQueueModel) -> str:
        """Create a new processing queue item"""
        item_data = item.model_dump(mode='json')
        
        try:
            result = self.client.table('processing_queue').insert(item_data).execute()
            
            if result.data:
                item_id = result.data[0]['id']
                self.logger.info(f"Created processing queue item {item_id}")
                return item_id
            else:
                raise Exception("Failed to create processing queue item")
                
        except Exception as e:
            self.logger.error(f"Failed to create processing queue item: {e}")
            raise RuntimeError(f"Cannot create processing queue item in database: {e}")
    
    async def update_processing_queue_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update processing queue item"""
        try:
            result = self.client.table('processing_queue').update(updates).eq('id', item_id).execute()
            
            if result.data:
                self.logger.info(f"Updated processing queue item {item_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to update processing queue item: {e}")
            return False
    
    async def get_pending_queue_items(self, processor_name: str, limit: int = 10) -> List[ProcessingQueueModel]:
        """Get pending queue items for a processor"""
        try:
            result = self.client.table('processing_queue').select('*').eq('processor_name', processor_name).eq('status', 'pending').limit(limit).execute()
            
            items = []
            for item_data in result.data:
                items.append(ProcessingQueueModel(**item_data))
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to get pending queue items: {e}")
            return []
    
    async def log_audit(self, action: str, entity_type: str, entity_id: str, details: Dict[str, Any] = None):
        """Log audit event (disabled - audit_log table not configured)"""
        try:
            # Audit logging is disabled until audit_log table is properly configured
            # This prevents errors when audit_log table schema doesn't match expectations
            pass
            
        except Exception as e:
            # Silently ignore audit logging errors
            pass
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status and statistics"""
        try:
            # Get counts from all tables
            status = {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "connected",
                "database_url": self.supabase_url
            }
            
            # Get document counts
            docs_result = self.client.table('documents').select('processing_status').execute()
            status['total_documents'] = len(docs_result.data)
            
            # Count by status
            status_counts = {}
            for doc in docs_result.data:
                status_val = doc['processing_status']
                status_counts[status_val] = status_counts.get(status_val, 0) + 1
            
            status.update(status_counts)
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    # Cross-Schema Helper Methods (using direct PostgreSQL)
    async def get_image_by_hash(self, file_hash: str) -> Optional[Dict]:
        """Get image by file_hash for deduplication - SQL or PostgREST"""
        try:
            if self.client is None:
                return None
            
            # Method 1: Direct PostgreSQL (fastest)
            if self.pg_pool:
                try:
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
                            self.logger.info(f"Found existing image with hash {file_hash[:16]}... (asyncpg)")
                            return image_data
                except Exception as pg_err:
                    self.logger.warning(f"asyncpg query failed: {pg_err}, trying PostgREST...")
            
            # Method 2: PostgREST with Service Role via public.vw_images view
            if self.service_client:
                try:
                    result = self.service_client.from_('vw_images').select('id, filename, file_hash, created_at, document_id, storage_url').eq('file_hash', file_hash).limit(1).execute()
                    
                    if result.data and len(result.data) > 0:
                        image_data = result.data[0]
                        self.logger.info(f"Found existing image with hash {file_hash[:16]}... (PostgREST)")
                        return image_data
                except Exception as rest_err:
                    self.logger.warning(f"PostgREST query failed: {rest_err}")
            
            return None
        except Exception as e:
            self.logger.error(f"Failed to get image by hash {file_hash[:16]}...: {e}")
            return None
    
    async def count_chunks_by_document(self, document_id: str) -> int:
        """Count chunks for a document - SQL or PostgREST"""
        try:
            # Method 1: Direct PostgreSQL
            if self.pg_pool:
                try:
                    async with self.pg_pool.acquire() as conn:
                        count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_content.chunks WHERE document_id = $1",
                            document_id
                        )
                        return count or 0
                except Exception as pg_err:
                    self.logger.warning(f"asyncpg count failed: {pg_err}, trying PostgREST...")
            
            # Method 2: PostgREST via public.vw_chunks view
            if self.service_client:
                try:
                    result = self.service_client.from_('vw_chunks').select('id', count='exact').eq('document_id', document_id).execute()
                    return result.count or 0
                except Exception as rest_err:
                    self.logger.warning(f"PostgREST count failed: {rest_err}")
            
            return 0
        except Exception as e:
            self.logger.error(f"Failed to count chunks: {e}")
            return 0
    
    async def count_images_by_document(self, document_id: str) -> int:
        """Count images for a document - SQL or PostgREST"""
        try:
            # Method 1: Direct PostgreSQL
            if self.pg_pool:
                try:
                    async with self.pg_pool.acquire() as conn:
                        count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_content.images WHERE document_id = $1",
                            document_id
                        )
                        return count or 0
                except Exception as pg_err:
                    self.logger.warning(f"asyncpg count failed: {pg_err}, trying PostgREST...")
            
            # Method 2: PostgREST via public.vw_images view
            if self.service_client:
                try:
                    result = self.service_client.from_('vw_images').select('id', count='exact').eq('document_id', document_id).execute()
                    return result.count or 0
                except Exception as rest_err:
                    self.logger.warning(f"PostgREST count failed: {rest_err}")
            
            return 0
        except Exception as e:
            self.logger.error(f"Failed to count images: {e}")
            return 0
    
    async def check_embeddings_exist(self, document_id: str) -> bool:
        """Check if embeddings exist for a document - SQL or PostgREST"""
        try:
            # Method 1: Direct PostgreSQL (supports JOINs)
            if self.pg_pool:
                try:
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
                except Exception as pg_err:
                    self.logger.warning(f"asyncpg embeddings check failed: {pg_err}, trying PostgREST...")
            
            # Method 2: PostgREST via public views (multi-step: get chunks first, then check embeddings)
            if self.service_client:
                try:
                    # Get chunk IDs for document via vw_chunks
                    chunks = self.service_client.from_('vw_chunks').select('id').eq('document_id', document_id).limit(1).execute()
                    
                    if chunks.data and len(chunks.data) > 0:
                        chunk_id = chunks.data[0]['id']
                        # Check if any embedding exists for this chunk via vw_embeddings
                        embeddings = self.service_client.from_('vw_embeddings').select('id').eq('chunk_id', chunk_id).limit(1).execute()
                        return embeddings.data and len(embeddings.data) > 0
                except Exception as rest_err:
                    self.logger.warning(f"PostgREST embeddings check failed: {rest_err}")
            
            return False
        except Exception as e:
            self.logger.error(f"Failed to check embeddings: {e}")
            return False
    
    # Link & Video Methods
    async def count_links_by_document(self, document_id: str) -> int:
        """Count links for a document"""
        try:
            # Method 1: Direct PostgreSQL
            if self.pg_pool:
                try:
                    async with self.pg_pool.acquire() as conn:
                        count = await conn.fetchval(
                            "SELECT COUNT(*) FROM krai_content.links WHERE document_id = $1",
                            document_id
                        )
                        return count or 0
                except Exception as pg_err:
                    self.logger.warning(f"asyncpg count failed: {pg_err}, trying PostgREST...")
            
            # Method 2: PostgREST via vw_links view
            client = self.service_client if self.service_client else self.client
            result = client.from_('vw_links').select('id', count='exact').eq('document_id', document_id).execute()
            return result.count or 0
            
        except Exception as e:
            self.logger.error(f"Failed to count links: {e}")
            return 0
    
    async def create_link(self, link_data: Dict[str, Any]) -> Optional[str]:
        """Create a link in krai_content.links"""
        try:
            # Use PostgREST (works with both service_client and regular client)
            client = self.service_client if self.service_client else self.client
            
            result = client.schema('krai_content').table('links').insert(link_data).execute()
            
            if result.data and len(result.data) > 0:
                link_id = result.data[0]['id']
                self.logger.info(f"Created link: {link_id} ({link_data.get('link_type')})")
                return link_id
            
            return None
        except Exception as e:
            self.logger.error(f"Failed to create link: {e}")
            return None
    
    async def find_or_create_video_from_link(self, url: str, manufacturer_id: Optional[str], 
                                            title: Optional[str] = None, 
                                            description: Optional[str] = None,
                                            metadata: Optional[Dict] = None) -> Optional[str]:
        """Find existing video by URL or create new one"""
        try:
            # Use SQL function we created in migration
            if self.pg_pool:
                async with self.pg_pool.acquire() as conn:
                    video_id = await conn.fetchval(
                        "SELECT krai_content.find_or_create_video_from_link($1, $2, $3, $4, $5)",
                        url,
                        manufacturer_id,
                        title,
                        description,
                        metadata or {}
                    )
                    return str(video_id) if video_id else None
            
            # Fallback: Use PostgREST (two-step: find, then create if not found)
            client = self.service_client if self.service_client else self.client
            
            # Try to find existing
            result = client.schema('krai_content').table('instructional_videos').select('id').eq('video_url', url).limit(1).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]['id']
            
            # Create new
            video_data = {
                'manufacturer_id': manufacturer_id,
                'video_url': url,
                'title': title or f"Auto-extracted: {url}",
                'description': description or "Automatically extracted from document",
                'auto_created': True,
                'metadata': metadata or {}
            }
            
            result = client.schema('krai_content').table('instructional_videos').insert(video_data).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]['id']
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find/create video from link: {e}")
            return None
