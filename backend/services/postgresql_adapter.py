"""
PostgreSQL Database Adapter

Pure asyncpg implementation for direct PostgreSQL connections.
No Supabase dependencies - uses only asyncpg for database access.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    raise ImportError("asyncpg not available. Please install: pip install asyncpg")

from backend.core.data_models import (
    DocumentModel, ManufacturerModel, ProductSeriesModel, ProductModel,
    ChunkModel, ImageModel, IntelligenceChunkModel, EmbeddingModel,
    ErrorCodeModel, SearchAnalyticsModel, ProcessingQueueModel,
    AuditLogModel, SystemMetricsModel, PrintDefectModel
)
from backend.services.database_adapter import DatabaseAdapter


class PostgreSQLAdapter(DatabaseAdapter):
    """
    PostgreSQL Database Adapter
    
    Pure asyncpg implementation for direct PostgreSQL connections.
    Uses schema prefix for multi-tenant support (e.g., krai_core, krai_content).
    """
    
    def __init__(self, postgres_url: str, schema_prefix: str = "krai"):
        super().__init__()
        self.postgres_url = postgres_url
        self.schema_prefix = schema_prefix
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.logger = logging.getLogger("krai.database.postgresql")
        self._core_schema = f"{self.schema_prefix}_core"
        self._content_schema = f"{self.schema_prefix}_content"
        self._intelligence_schema = f"{self.schema_prefix}_intelligence"
        self._system_schema = f"{self.schema_prefix}_system"
        self._parts_schema = f"{self.schema_prefix}_parts"

    def _ensure_pool(self) -> asyncpg.Pool:
        if self.pg_pool is None:
            raise RuntimeError("PostgreSQL connection pool is not initialized. Call connect() first.")
        return self.pg_pool

    def _prepare_insert(self, data: Dict[str, Any]) -> tuple[list[str], list[str], list[Any]]:
        columns = list(data.keys())
        placeholders = [f"${idx + 1}" for idx in range(len(columns))]
        values = [data[column] for column in columns]
        return columns, placeholders, values

    @staticmethod
    def _vector_literal(values: List[float]) -> str:
        return "[" + ",".join(f"{v:.8f}" for v in values) + "]"
    
    async def connect(self) -> None:
        """Establish PostgreSQL connection pool"""
        try:
            self.pg_pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            self.logger.info(f"Connected to PostgreSQL database (asyncpg pool)")
            await self.test_connection()
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise RuntimeError(f"Cannot connect to PostgreSQL database: {e}")
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            if self.pg_pool is None:
                raise RuntimeError("Database pool not connected")
            
            async with self.pg_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                self.logger.info("PostgreSQL connection test successful")
                return True
        except Exception as e:
            self.logger.warning(f"PostgreSQL connection test failed: {e}")
            return False
    
    # Document Operations
    async def create_document(self, document: DocumentModel) -> str:
        """Create a new document"""
        async with self.pg_pool.acquire() as conn:
            document_id = await conn.fetchval(
                f"""
                INSERT INTO {self.schema_prefix}_core.documents 
                (filename, original_filename, file_size, file_hash, document_type, language, processing_status)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                document.filename,
                document.original_filename,
                document.file_size,
                document.file_hash,
                document.document_type,
                document.language,
                document.processing_status
            )
            self.logger.info(f"Created document {document_id}")
            return str(document_id)
    
    async def get_document(self, document_id: str) -> Optional[DocumentModel]:
        """Get document by ID"""
        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT * FROM {self.schema_prefix}_core.documents WHERE id = $1",
                document_id
            )
            return DocumentModel(**dict(row)) if row else None
    
    async def get_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get document by file hash for deduplication"""
        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT * FROM {self.schema_prefix}_core.documents WHERE file_hash = $1",
                file_hash
            )
            return dict(row) if row else None
    
    async def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update document"""
        # Build dynamic UPDATE query
        set_clauses = [f"{key} = ${i+2}" for i, key in enumerate(updates.keys())]
        query = f"""
            UPDATE {self.schema_prefix}_core.documents 
            SET {', '.join(set_clauses)}, updated_at = NOW()
            WHERE id = $1
        """
        
        async with self.pg_pool.acquire() as conn:
            await conn.execute(query, document_id, *updates.values())
            self.logger.info(f"Updated document {document_id}")
            return True
    
    # Placeholder implementations for remaining methods
    # TODO: Implement all methods from DatabaseAdapter interface
    
    async def create_manufacturer(self, manufacturer: ManufacturerModel) -> str:
        pool = self._ensure_pool()
        manufacturer_data = manufacturer.model_dump(mode='python', exclude_none=True)
        async with pool.acquire() as conn:
            existing = await conn.fetchrow(
                f"SELECT id FROM {self._core_schema}.manufacturers WHERE LOWER(name) = LOWER($1) LIMIT 1",
                manufacturer.name
            )
            if existing:
                manufacturer_id = str(existing['id'])
                self.logger.info(f"Manufacturer '{manufacturer.name}' already exists: {manufacturer_id}")
                return manufacturer_id

            columns, placeholders, values = self._prepare_insert(manufacturer_data)
            sql = (
                f"INSERT INTO {self._core_schema}.manufacturers "
                f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
            )
            manufacturer_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Created manufacturer {manufacturer_id}")
            return str(manufacturer_id)

    async def get_manufacturer_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT * FROM {self._core_schema}.manufacturers WHERE LOWER(name) = LOWER($1) LIMIT 1",
                name
            )
            return dict(row) if row else None

    async def create_product_series(self, series: ProductSeriesModel) -> str:
        pool = self._ensure_pool()
        series_data = series.model_dump(mode='python', exclude_none=True)
        async with pool.acquire() as conn:
            existing = await conn.fetchrow(
                f"""
                SELECT id FROM {self._core_schema}.product_series
                WHERE manufacturer_id = $1 AND LOWER(series_name) = LOWER($2)
                LIMIT 1
                """,
                series.manufacturer_id,
                series.series_name
            )
            if existing:
                series_id = str(existing['id'])
                self.logger.info(
                    f"Product series '{series.series_name}' already exists (manufacturer {series.manufacturer_id})"
                )
                return series_id

            columns, placeholders, values = self._prepare_insert(series_data)
            sql = (
                f"INSERT INTO {self._core_schema}.product_series "
                f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
            )
            series_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Created product series {series_id}")
            return str(series_id)

    async def get_product_series_by_name(self, name: str, manufacturer_id: str) -> Optional[Dict[str, Any]]:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT * FROM {self._core_schema}.product_series
                WHERE manufacturer_id = $1 AND LOWER(series_name) = LOWER($2)
                LIMIT 1
                """,
                manufacturer_id,
                name
            )
            return dict(row) if row else None

    async def create_product(self, product: ProductModel) -> str:
        pool = self._ensure_pool()
        product_data = product.model_dump(mode='python', exclude_none=True)
        async with pool.acquire() as conn:
            existing = await conn.fetchrow(
                f"""
                SELECT id FROM {self._core_schema}.products
                WHERE manufacturer_id = $1 AND LOWER(model_number) = LOWER($2)
                LIMIT 1
                """,
                product.manufacturer_id,
                product.model_number
            )
            if existing:
                product_id = str(existing['id'])
                self.logger.info(
                    f"Product '{product.model_number}' (manufacturer {product.manufacturer_id}) already exists"
                )
                return product_id

            columns, placeholders, values = self._prepare_insert(product_data)
            sql = (
                f"INSERT INTO {self._core_schema}.products "
                f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
            )
            product_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Created product {product_id}")
            return str(product_id)

    async def get_product_by_model(self, model_number: str, manufacturer_id: str) -> Optional[Dict[str, Any]]:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT * FROM {self._core_schema}.products
                WHERE manufacturer_id = $1 AND LOWER(model_number) = LOWER($2)
                LIMIT 1
                """,
                manufacturer_id,
                model_number
            )
            return dict(row) if row else None

    async def create_chunk(self, chunk: ChunkModel) -> str:
        chunk_data = chunk.model_dump(mode='python', exclude_none=True)
        return await self.create_chunk_async(chunk_data)

    async def create_chunk_async(self, chunk_data: Dict[str, Any]) -> str:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            columns, placeholders, values = self._prepare_insert(chunk_data)
            sql = (
                f"INSERT INTO {self._content_schema}.chunks "
                f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
            )
            chunk_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Created chunk {chunk_id}")
            return str(chunk_id)

    async def get_chunk_by_document_and_index(self, document_id: str, chunk_index: int) -> Optional[Dict[str, Any]]:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT * FROM {self._content_schema}.chunks
                WHERE document_id = $1 AND chunk_index = $2
                LIMIT 1
                """,
                document_id,
                chunk_index
            )
            return dict(row) if row else None

    async def create_image(self, image: ImageModel) -> str:
        pool = self._ensure_pool()
        image_data = image.model_dump(mode='python', exclude_none=True)
        async with pool.acquire() as conn:
            existing = None
            if image.file_hash:
                existing = await conn.fetchrow(
                    f"SELECT id FROM {self._content_schema}.images WHERE file_hash = $1 LIMIT 1",
                    image.file_hash
                )
            if existing:
                image_id = str(existing['id'])
                self.logger.info(f"Image with hash {image.file_hash[:16]}... already exists: {image_id}")
                return image_id

            columns, placeholders, values = self._prepare_insert(image_data)
            sql = (
                f"INSERT INTO {self._content_schema}.images "
                f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
            )
            image_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Created image {image_id}")
            return str(image_id)

    async def get_image_by_hash(self, image_hash: str) -> Optional[Dict[str, Any]]:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT * FROM {self._content_schema}.images WHERE file_hash = $1 LIMIT 1",
                image_hash
            )
            return dict(row) if row else None

    async def get_images_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT * FROM {self._content_schema}.images
                WHERE document_id = $1
                ORDER BY page_number, image_index
                """,
                document_id
            )
            return [dict(row) for row in rows]

    async def create_intelligence_chunk(self, chunk: IntelligenceChunkModel) -> str:
        pool = self._ensure_pool()
        chunk_data = chunk.model_dump(mode='python', exclude_none=True)
        async with pool.acquire() as conn:
            columns, placeholders, values = self._prepare_insert(chunk_data)
            sql = (
                f"INSERT INTO {self._intelligence_schema}.chunks "
                f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
            )
            chunk_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Created intelligence chunk {chunk_id}")
            return str(chunk_id)

    async def create_embedding(self, embedding: EmbeddingModel) -> str:
        pool = self._ensure_pool()
        embedding_data = embedding.model_dump(mode='python', exclude_none=True)
        embedding_vector = embedding_data.pop('embedding')
        columns, placeholders, values = self._prepare_insert(embedding_data)
        vector_placeholder = f"${len(values) + 1}::vector"
        columns.insert(2, 'embedding')
        placeholders.insert(2, vector_placeholder)
        values.insert(2, self._vector_literal(embedding_vector))
        sql = (
            f"INSERT INTO {self._intelligence_schema}.embeddings "
            f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
        )
        async with pool.acquire() as conn:
            embedding_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Created embedding {embedding_id}")
            return str(embedding_id)

    async def get_embedding_by_chunk_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT * FROM {self._intelligence_schema}.embeddings WHERE chunk_id = $1 LIMIT 1",
                chunk_id
            )
            return dict(row) if row else None

    async def get_embeddings_by_chunk_ids(self, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        if not chunk_ids:
            return []
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT * FROM {self._intelligence_schema}.embeddings WHERE chunk_id = ANY($1::uuid[])",
                chunk_ids
            )
            return [dict(row) for row in rows]

    async def search_embeddings(
        self,
        query_embedding: List[float],
        limit: int = 10,
        match_threshold: float = 0.7,
        match_count: int = 10
    ) -> List[Dict[str, Any]]:
        pool = self._ensure_pool()
        vector_literal = self._vector_literal(query_embedding)
        effective_limit = max(limit, match_count)
        sql = f"""
            SELECT
                e.id,
                e.chunk_id,
                e.model_name,
                e.model_version,
                e.created_at,
                (1 - (e.embedding <=> {vector_literal}::vector)) AS similarity
            FROM {self._intelligence_schema}.embeddings e
            WHERE (1 - (e.embedding <=> {vector_literal}::vector)) >= $1
            ORDER BY similarity DESC
            LIMIT $2
        """
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, match_threshold, effective_limit)
            return [dict(row) for row in rows]

    async def create_error_code(self, error_code: ErrorCodeModel) -> str:
        pool = self._ensure_pool()
        error_code_data = error_code.model_dump(mode='python', exclude_none=True)
        columns, placeholders, values = self._prepare_insert(error_code_data)
        sql = (
            f"INSERT INTO {self._intelligence_schema}.error_codes "
            f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
        )
        async with pool.acquire() as conn:
            error_code_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Created error code {error_code_id}")
            return str(error_code_id)

    async def log_search_analytics(self, analytics: SearchAnalyticsModel) -> str:
        pool = self._ensure_pool()
        analytics_data = analytics.model_dump(mode='python', exclude_none=True)
        columns, placeholders, values = self._prepare_insert(analytics_data)
        sql = (
            f"INSERT INTO {self._intelligence_schema}.search_analytics "
            f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
        )
        async with pool.acquire() as conn:
            analytics_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Logged search analytics {analytics_id}")
            return str(analytics_id)

    async def create_processing_queue_item(self, item: ProcessingQueueModel) -> str:
        pool = self._ensure_pool()
        item_data = item.model_dump(mode='python', exclude_none=True)
        columns, placeholders, values = self._prepare_insert(item_data)
        sql = (
            f"INSERT INTO {self._system_schema}.processing_queue "
            f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
        )
        async with pool.acquire() as conn:
            item_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Created processing queue item {item_id}")
            return str(item_id)

    async def update_processing_queue_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        if not updates:
            return False
        pool = self._ensure_pool()
        set_clauses = [f"{key} = ${index + 2}" for index, key in enumerate(updates.keys())]
        sql = (
            f"UPDATE {self._system_schema}.processing_queue "
            f"SET {', '.join(set_clauses)}, updated_at = NOW() "
            f"WHERE id = $1"
        )
        async with pool.acquire() as conn:
            result = await conn.execute(sql, item_id, *updates.values())
            updated = result.upper().startswith("UPDATE")
            if updated:
                self.logger.info(f"Updated processing queue item {item_id}")
            return updated

    async def log_audit_event(self, event: AuditLogModel) -> str:
        pool = self._ensure_pool()
        event_data = event.model_dump(mode='python', exclude_none=True)
        columns, placeholders, values = self._prepare_insert(event_data)
        sql = (
            f"INSERT INTO {self._system_schema}.audit_log "
            f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
        )
        async with pool.acquire() as conn:
            event_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Logged audit event {event.action} ({event_id})")
            return str(event_id)

    async def get_system_status(self) -> Dict[str, Any]:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            document_counts = await conn.fetch(
                f"SELECT processing_status, COUNT(*) AS cnt FROM {self._core_schema}.documents GROUP BY processing_status"
            )
            total_documents = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self._core_schema}.documents"
            )
            status = {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "connected",
                "total_documents": total_documents or 0,
            }
            for row in document_counts:
                status[str(row['processing_status'])] = row['cnt']
            return status

    async def count_chunks_by_document(self, document_id: str) -> int:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self._content_schema}.chunks WHERE document_id = $1",
                document_id
            )
            return count or 0

    async def count_images_by_document(self, document_id: str) -> int:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self._content_schema}.images WHERE document_id = $1",
                document_id
            )
            return count or 0

    async def check_embedding_exists(self, chunk_id: str) -> bool:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            exists = await conn.fetchval(
                f"""
                SELECT EXISTS(
                    SELECT 1 FROM {self._intelligence_schema}.embeddings
                    WHERE chunk_id = $1
                )
                """,
                chunk_id
            )
            return bool(exists)

    async def count_links_by_document(self, document_id: str) -> int:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval(
                f"SELECT COUNT(*) FROM {self._content_schema}.links WHERE document_id = $1",
                document_id
            )
            return count or 0

    async def create_link(self, link_data: Dict[str, Any]) -> str:
        pool = self._ensure_pool()
        link_record = {k: v for k, v in link_data.items() if v is not None}
        columns, placeholders, values = self._prepare_insert(link_record)
        sql = (
            f"INSERT INTO {self._content_schema}.links "
            f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
        )
        async with pool.acquire() as conn:
            link_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Created link {link_id} ({link_data.get('link_type')})")
            return str(link_id)

    async def create_video(self, video_data: Dict[str, Any]) -> str:
        pool = self._ensure_pool()
        columns = list(video_data.keys())
        update_set = [f"{col} = EXCLUDED.{col}" for col in columns if col not in {"id"}]
        placeholders = [f"${idx + 1}" for idx in range(len(columns))]
        sql = (
            f"INSERT INTO {self._content_schema}.videos ({', '.join(columns)}) "
            f"VALUES ({', '.join(placeholders)}) "
            f"ON CONFLICT (link_id) DO UPDATE SET {', '.join(update_set)} "
            f"RETURNING id"
        )
        async with pool.acquire() as conn:
            video_id = await conn.fetchval(sql, *video_data.values())
            self.logger.info(f"Upserted video {video_id}")
            return str(video_id)

    async def create_print_defect(self, defect: PrintDefectModel) -> str:
        pool = self._ensure_pool()
        defect_data = defect.model_dump(mode='python', exclude_none=True)
        columns, placeholders, values = self._prepare_insert(defect_data)
        sql = (
            f"INSERT INTO {self._content_schema}.print_defects "
            f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
        )
        async with pool.acquire() as conn:
            defect_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Created print defect {defect_id}")
            return str(defect_id)

