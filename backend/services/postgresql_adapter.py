"""
PostgreSQL Database Adapter

Pure asyncpg implementation for direct PostgreSQL connections.
No Supabase dependencies - uses only asyncpg for database access.
"""

import logging
import json
import re
from types import SimpleNamespace
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    raise ImportError("asyncpg not available. Please install: pip install asyncpg")

from core.data_models import (
    DocumentModel, ManufacturerModel, ProductSeriesModel, ProductModel,
    ChunkModel, ImageModel, IntelligenceChunkModel, EmbeddingModel,
    ErrorCodeModel, SearchAnalyticsModel, ProcessingQueueModel,
    AuditLogModel, SystemMetricsModel, PrintDefectModel
)
from services.database_adapter import DatabaseAdapter


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

    def _prepare_query(self, query: str, params: Optional[Any]) -> Tuple[str, List[Any]]:
        """Convert named (":param") or psycopg-style ("%s") placeholders to asyncpg positional ones."""

        if params is None:
            return query, []

        # Handle sequence parameters (assume positional order)
        if isinstance(params, (list, tuple)):
            values = list(params)
            # Convert psycopg %s placeholders to $1, $2, ...
            if "%s" in query:
                placeholder_pattern = re.compile(r"%s")
                index = 0

                def repl(_):
                    nonlocal index
                    index += 1
                    return f"${index}"

                query = placeholder_pattern.sub(repl, query)
            return query, values

        # Handle single scalar parameter
        if not isinstance(params, dict):
            return query, [params]

        # Named parameters
        pattern = re.compile(r":([a-zA-Z0-9_]+)")
        values: List[Any] = []
        index_map: Dict[str, int] = {}

        def replace(match: re.Match) -> str:
            name = match.group(1)
            if name not in params:
                raise KeyError(f"Parameter '{name}' not provided for query")
            if name not in index_map:
                index_map[name] = len(values) + 1
                values.append(params[name])
            return f"${index_map[name]}"

        query = pattern.sub(replace, query)
        return query, values

    async def fetch_one(self, query: str, params: Optional[Any] = None):
        """Execute query and return a single row."""
        pool = self._ensure_pool()
        formatted_query, values = self._prepare_query(query, params)
        async with pool.acquire() as conn:
            return await conn.fetchrow(formatted_query, *values)

    async def fetch_all(self, query: str, params: Optional[Any] = None) -> List[Any]:
        """Execute query and return all rows."""
        pool = self._ensure_pool()
        formatted_query, values = self._prepare_query(query, params)
        async with pool.acquire() as conn:
            return await conn.fetch(formatted_query, *values)

    async def execute_query(self, query: str, params: Optional[Any] = None):
        """Execute arbitrary SQL query supporting SELECT and mutation statements."""
        pool = self._ensure_pool()
        formatted_query, values = self._prepare_query(query, params)
        lower_query = formatted_query.lstrip().lower()

        async with pool.acquire() as conn:
            # Return rows for SELECT/RETURNING/CTE statements
            if lower_query.startswith(("select", "with")) or " returning " in lower_query:
                return await conn.fetch(formatted_query, *values)

            status = await conn.execute(formatted_query, *values)

            # Extract rowcount from command tag (e.g., "UPDATE 1")
            rowcount = 0
            try:
                parts = status.split()
                if parts and parts[-1].isdigit():
                    rowcount = int(parts[-1])
            except Exception:  # pragma: no cover - fallback safety
                rowcount = 0

            return SimpleNamespace(status=status, rowcount=rowcount)

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

    # Phase 5: Context extraction update methods
    async def update_image_context(self, image_id: str, context_data: Dict[str, Any]) -> bool:
        """Update context fields for an image."""
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            try:
                # Handle vector field separately
                vector_value = None
                if 'context_embedding' in context_data:
                    vector_value = context_data.pop('context_embedding')
                
                # Build SET clause for non-vector fields
                set_clauses = []
                values = []
                param_idx = 1
                
                for key, value in context_data.items():
                    set_clauses.append(f"{key} = ${param_idx}")
                    values.append(value)
                    param_idx += 1
                
                # Add vector field if present
                if vector_value is not None:
                    set_clauses.append(f"context_embedding = ${param_idx}::vector")
                    values.append(self._vector_literal(vector_value))
                    param_idx += 1
                
                values.append(image_id)  # WHERE clause parameter
                
                sql = f"""
                UPDATE {self._content_schema}.images 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_idx}
                """
                
                result = await conn.execute(sql, *values)
                success = result == "UPDATE 1"
                
                if success:
                    self.logger.info(f"Updated context for image {image_id}")
                else:
                    self.logger.warning(f"Failed to update context for image {image_id}")
                
                return success
                
            except Exception as e:
                self.logger.error(f"Error updating image context {image_id}: {e}")
                return False

    async def update_video_context(self, video_id: str, context_data: Dict[str, Any]) -> bool:
        """Update context fields for a video."""
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            try:
                # Handle vector field separately
                vector_value = None
                if 'context_embedding' in context_data:
                    vector_value = context_data.pop('context_embedding')
                
                # Build SET clause for non-vector fields
                set_clauses = []
                values = []
                param_idx = 1
                
                for key, value in context_data.items():
                    set_clauses.append(f"{key} = ${param_idx}")
                    values.append(value)
                    param_idx += 1
                
                # Add vector field if present
                if vector_value is not None:
                    set_clauses.append(f"context_embedding = ${param_idx}::vector")
                    values.append(self._vector_literal(vector_value))
                    param_idx += 1
                
                values.append(video_id)  # WHERE clause parameter
                
                sql = f"""
                UPDATE {self._content_schema}.instructional_videos 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_idx}
                """
                
                result = await conn.execute(sql, *values)
                success = result == "UPDATE 1"
                
                if success:
                    self.logger.info(f"Updated context for video {video_id}")
                else:
                    self.logger.warning(f"Failed to update context for video {video_id}")
                
                return success
                
            except Exception as e:
                self.logger.error(f"Error updating video context {video_id}: {e}")
                return False

    async def update_link_context(self, link_id: str, context_data: Dict[str, Any]) -> bool:
        """Update context fields for a link."""
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            try:
                # Handle vector field separately
                vector_value = None
                if 'context_embedding' in context_data:
                    vector_value = context_data.pop('context_embedding')
                
                # Build SET clause for non-vector fields
                set_clauses = []
                values = []
                param_idx = 1
                
                for key, value in context_data.items():
                    set_clauses.append(f"{key} = ${param_idx}")
                    values.append(value)
                    param_idx += 1
                
                # Add vector field if present
                if vector_value is not None:
                    set_clauses.append(f"context_embedding = ${param_idx}::vector")
                    values.append(self._vector_literal(vector_value))
                    param_idx += 1
                
                values.append(link_id)  # WHERE clause parameter
                
                sql = f"""
                UPDATE {self._content_schema}.links 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_idx}
                """
                
                result = await conn.execute(sql, *values)
                success = result == "UPDATE 1"
                
                if success:
                    self.logger.info(f"Updated context for link {link_id}")
                else:
                    self.logger.warning(f"Failed to update context for link {link_id}")
                
                return success
                
            except Exception as e:
                self.logger.error(f"Error updating link context {link_id}: {e}")
                return False

    async def update_media_contexts_batch(self, updates: List[Dict[str, Any]]) -> Dict[str, int]:
        """Update context fields for multiple media items in a batch."""
        success_count = 0
        failed_count = 0
        
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            try:
                async with conn.transaction():
                    for update in updates:
                        media_type = update.get('media_type')
                        media_id = update.get('media_id')
                        context_data = update.get('context_data', {})
                        
                        if not media_type or not media_id:
                            failed_count += 1
                            continue
                        
                        try:
                            if media_type == 'image':
                                success = await self.update_image_context(media_id, context_data)
                            elif media_type == 'video':
                                success = await self.update_video_context(media_id, context_data)
                            elif media_type == 'link':
                                success = await self.update_link_context(media_id, context_data)
                            else:
                                success = False
                            
                            if success:
                                success_count += 1
                            else:
                                failed_count += 1
                                
                        except Exception as e:
                            self.logger.error(f"Error in batch update for {media_type} {media_id}: {e}")
                            failed_count += 1
                
            except Exception as e:
                self.logger.error(f"Transaction failed in batch context update: {e}")
                failed_count += len(updates)
        
        self.logger.info(f"Batch context update completed: {success_count} success, {failed_count} failed")
        return {'success_count': success_count, 'failed_count': failed_count}

    async def get_media_without_context(self, media_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get media items without context extraction for backfill."""
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            try:
                if media_type == 'image':
                    sql = f"""
                    SELECT id, document_id, page_number 
                    FROM {self._content_schema}.images 
                    WHERE context_caption IS NULL 
                    ORDER BY created_at DESC 
                    LIMIT ${limit}
                    """
                elif media_type == 'video':
                    sql = f"""
                    SELECT id, document_id, page_number 
                    FROM {self._content_schema}.instructional_videos 
                    WHERE context_description IS NULL 
                    ORDER BY created_at DESC 
                    LIMIT ${limit}
                    """
                elif media_type == 'link':
                    sql = f"""
                    SELECT id, document_id, page_number 
                    FROM {self._content_schema}.links 
                    WHERE context_description IS NULL 
                    ORDER BY created_at DESC 
                    LIMIT ${limit}
                    """
                else:
                    return []
                
                rows = await conn.fetch(sql, limit)
                return [dict(row) for row in rows]
                
            except Exception as e:
                self.logger.error(f"Error getting media without context for {media_type}: {e}")
                return []

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

    async def create_embedding_v2(
        self,
        source_id: str,
        source_type: str,
        embedding: List[float],
        model_name: str,
        embedding_context: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Create embedding in embeddings_v2 table"""
        pool = self._ensure_pool()
        
        # Prepare data
        embedding_data = {
            'source_id': source_id,
            'source_type': source_type,
            'model_name': model_name,
            'embedding_context': embedding_context,
            'metadata': json.dumps(metadata or {})
        }
        
        # Prepare vector literal
        vector_literal = self._vector_literal(embedding)
        
        # Build SQL
        columns, placeholders, values = self._prepare_insert(embedding_data)
        columns.append('embedding')
        placeholders.append(f'${len(values) + 1}::vector')
        values.append(vector_literal)
        
        sql = (
            f"INSERT INTO {self._intelligence_schema}.embeddings_v2 "
            f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
        )
        
        async with pool.acquire() as conn:
            embedding_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Created embedding_v2 {embedding_id} (type={source_type})")
            return str(embedding_id)

    async def create_embeddings_v2_batch(
        self,
        embeddings: List[Dict[str, Any]]
    ) -> List[str]:
        """Create multiple embeddings in embeddings_v2 table (batch)"""
        pool = self._ensure_pool()
        embedding_ids = []
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                for emb_data in embeddings:
                    embedding_id = await self.create_embedding_v2(
                        source_id=emb_data['source_id'],
                        source_type=emb_data['source_type'],
                        embedding=emb_data['embedding'],
                        model_name=emb_data['model_name'],
                        embedding_context=emb_data.get('embedding_context'),
                        metadata=emb_data.get('metadata')
                    )
                    embedding_ids.append(embedding_id)
        
        self.logger.info(f"Created {len(embedding_ids)} embeddings_v2 in batch")
        return embedding_ids

    async def create_structured_table(
        self,
        table_data: Dict[str, Any]
    ) -> str:
        """Create structured table in krai_intelligence.structured_tables"""
        pool = self._ensure_pool()
        
        # Handle JSONB fields
        if 'table_data' in table_data and isinstance(table_data['table_data'], (list, dict)):
            table_data['table_data'] = json.dumps(table_data['table_data'])
        if 'metadata' in table_data and isinstance(table_data['metadata'], dict):
            table_data['metadata'] = json.dumps(table_data['metadata'])
        
        # Handle vector field (table_embedding)
        table_embedding = table_data.pop('table_embedding', None)
        context_embedding = table_data.pop('context_embedding', None)
        
        columns, placeholders, values = self._prepare_insert(table_data)
        
        # Add vector fields if present
        if table_embedding:
            columns.append('table_embedding')
            placeholders.append(f'${len(values) + 1}::vector')
            values.append(self._vector_literal(table_embedding))
        if context_embedding:
            columns.append('context_embedding')
            placeholders.append(f'${len(values) + 1}::vector')
            values.append(self._vector_literal(context_embedding))
        
        sql = (
            f"INSERT INTO {self._intelligence_schema}.structured_tables "
            f"({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
        )
        
        async with pool.acquire() as conn:
            table_id = await conn.fetchval(sql, *values)
            self.logger.info(f"Created structured table {table_id}")
            return str(table_id)

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

    async def get_embeddings_by_source(
        self,
        source_id: str,
        source_type: str = None
    ) -> List[Dict[str, Any]]:
        """Get embeddings from embeddings_v2 by source_id and optional source_type"""
        pool = self._ensure_pool()
        
        if source_type:
            sql = f"""
                SELECT * FROM {self._intelligence_schema}.embeddings_v2
                WHERE source_id = $1 AND source_type = $2
                ORDER BY created_at DESC
            """
            async with pool.acquire() as conn:
                rows = await conn.fetch(sql, source_id, source_type)
        else:
            sql = f"""
                SELECT * FROM {self._intelligence_schema}.embeddings_v2
                WHERE source_id = $1
                ORDER BY created_at DESC
            """
            async with pool.acquire() as conn:
                rows = await conn.fetch(sql, source_id)
        
        return [dict(row) for row in rows]

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
    
    async def execute_rpc_function(
        self,
        function_name: str,
        params: Dict[str, Any] = None,
        schema: str = None
    ) -> List[Dict[str, Any]]:
        """
        Execute PostgreSQL function (RPC equivalent)
        
        Args:
            function_name: Name of the function to execute
            params: Parameters to pass to the function
            schema: Schema name (default: intelligence schema)
            
        Returns:
            List of results as dictionaries
        """
        try:
            pool = self._ensure_pool()
            schema = schema or self._intelligence_schema
            params = params or {}
            
            # Build parameter list and placeholders
            param_values = list(params.values())
            param_placeholders = [f"${i+1}" for i in range(len(param_values))]
            
            # Build function call
            if param_values:
                sql = f"SELECT * FROM {schema}.{function_name}({', '.join(param_placeholders)})"
            else:
                sql = f"SELECT * FROM {schema}.{function_name}()"
            
            async with pool.acquire() as conn:
                results = await conn.fetch(sql, *param_values)
                
                # Convert to list of dicts
                return [dict(result) for result in results]
                
        except Exception as e:
            self.logger.error(f"Failed to execute RPC function {function_name}: {e}")
            return []
    
    async def match_multimodal(
        self,
        query_embedding: List[float],
        match_threshold: float = 0.5,
        match_count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Wrapper for match_multimodal RPC function
        
        Args:
            query_embedding: Query embedding vector
            match_threshold: Similarity threshold
            match_count: Maximum number of results
            
        Returns:
            List of multimodal search results
        """
        try:
            pool = self._ensure_pool()
            vector_literal = self._vector_literal(query_embedding)
            
            async with pool.acquire() as conn:
                results = await conn.fetch(
                    f"SELECT * FROM {self._intelligence_schema}.match_multimodal($1::vector, $2, $3)",
                    vector_literal,
                    match_threshold,
                    match_count
                )
                
                return [dict(result) for result in results]
                
        except Exception as e:
            self.logger.error(f"Failed to execute match_multimodal: {e}")
            return []
    
    async def match_images_by_context(
        self,
        query_embedding: List[float],
        match_threshold: float = 0.5,
        match_count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Wrapper for match_images_by_context RPC function
        
        Args:
            query_embedding: Query embedding vector
            match_threshold: Similarity threshold
            match_count: Maximum number of results
            
        Returns:
            List of image search results
        """
        try:
            pool = self._ensure_pool()
            vector_literal = self._vector_literal(query_embedding)
            
            async with pool.acquire() as conn:
                results = await conn.fetch(
                    f"SELECT * FROM {self._intelligence_schema}.match_images_by_context($1::vector, $2, $3)",
                    vector_literal,
                    match_threshold,
                    match_count
                )
                
                return [dict(result) for result in results]
                
        except Exception as e:
            self.logger.error(f"Failed to execute match_images_by_context: {e}")
            return []
    
    async def store_image_context(self, document_id: str, context_data: Dict[str, Any]) -> bool:
        """Store image context for a document"""
        try:
            pool = self._ensure_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self._intelligence_schema}.image_contexts 
                    (document_id, context_data, created_at) 
                    VALUES ($1, $2, $3)
                    ON CONFLICT (document_id) DO UPDATE SET 
                    context_data = $2, updated_at = $3
                    """,
                    document_id,
                    json.dumps(context_data),
                    datetime.now()
                )
                return True
        except Exception as e:
            self.logger.error(f"Failed to store image context: {e}")
            return False
    
    async def store_video_context(self, document_id: str, context_data: Dict[str, Any]) -> bool:
        """Store video context for a document"""
        try:
            pool = self._ensure_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self._intelligence_schema}.video_contexts 
                    (document_id, context_data, created_at) 
                    VALUES ($1, $2, $3)
                    ON CONFLICT (document_id) DO UPDATE SET 
                    context_data = $2, updated_at = $3
                    """,
                    document_id,
                    json.dumps(context_data),
                    datetime.now()
                )
                return True
        except Exception as e:
            self.logger.error(f"Failed to store video context: {e}")
            return False
    
    async def store_link_context(self, document_id: str, context_data: Dict[str, Any]) -> bool:
        """Store link context for a document"""
        try:
            pool = self._ensure_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self._intelligence_schema}.link_contexts 
                    (document_id, context_data, created_at) 
                    VALUES ($1, $2, $3)
                    ON CONFLICT (document_id) DO UPDATE SET 
                    context_data = $2, updated_at = $3
                    """,
                    document_id,
                    json.dumps(context_data),
                    datetime.now()
                )
                return True
        except Exception as e:
            self.logger.error(f"Failed to store link context: {e}")
            return False
    
    async def store_table_context(self, document_id: str, context_data: Dict[str, Any]) -> bool:
        """Store table context for a document"""
        try:
            pool = self._ensure_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self._intelligence_schema}.table_contexts 
                    (document_id, context_data, created_at) 
                    VALUES ($1, $2, $3)
                    ON CONFLICT (document_id) DO UPDATE SET 
                    context_data = $2, updated_at = $3
                    """,
                    document_id,
                    json.dumps(context_data),
                    datetime.now()
                )
                return True
        except Exception as e:
            self.logger.error(f"Failed to store table context: {e}")
            return False
    
    async def get_image_contexts_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all image contexts for a document"""
        try:
            pool = self._ensure_pool()
            async with pool.acquire() as conn:
                results = await conn.fetch(
                    f"""
                    SELECT document_id, context_data, created_at, updated_at 
                    FROM {self._intelligence_schema}.image_contexts 
                    WHERE document_id = $1
                    ORDER BY created_at DESC
                    """,
                    document_id
                )
                return [dict(result) for result in results]
        except Exception as e:
            self.logger.error(f"Failed to get image contexts: {e}")
            return []
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and all related data"""
        try:
            pool = self._ensure_pool()
            async with pool.acquire() as conn:
                # Delete from all tables in reverse order of dependencies
                await conn.execute(f"DELETE FROM {self._intelligence_schema}.chunks WHERE document_id = $1", document_id)
                await conn.execute(f"DELETE FROM {self._intelligence_schema}.image_contexts WHERE document_id = $1", document_id)
                await conn.execute(f"DELETE FROM {self._intelligence_schema}.video_contexts WHERE document_id = $1", document_id)
                await conn.execute(f"DELETE FROM {self._intelligence_schema}.link_contexts WHERE document_id = $1", document_id)
                await conn.execute(f"DELETE FROM {self._intelligence_schema}.table_contexts WHERE document_id = $1", document_id)
                await conn.execute(f"DELETE FROM {self._content_schema}.documents WHERE id = $1", document_id)
                await conn.execute(f"DELETE FROM {self._parts_schema}.products WHERE document_id = $1", document_id)
                return True
        except Exception as e:
            self.logger.error(f"Failed to delete document: {e}")
            return False

