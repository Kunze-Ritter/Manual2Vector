"""
Embedding Processor - Generate vector embeddings for semantic search

Stage 7 of the processing pipeline.

Uses embeddinggemma via Ollama for local, fast embeddings.
Stores vectors in Supabase with pgvector for similarity search.

Features:
- Batch embedding generation
- Ollama integration (embeddinggemma 768-dim)
- pgvector storage in Supabase
- Similarity search
- Progress tracking
"""

import os
import json
import random
import platform
from pathlib import Path
from collections import deque
from typing import List, Dict, Any, Optional
import asyncio
from uuid import UUID
import time
import requests
from requests.adapters import HTTPAdapter
from requests import exceptions as requests_exceptions
from urllib3.util.retry import Retry
from datetime import datetime, timezone

from backend.core.base_processor import BaseProcessor, Stage
from .stage_tracker import StageTracker
from backend.pipeline.metrics import metrics
from backend.processors.logger import text_stats


class EmbeddingProcessor(BaseProcessor):
    """
    Stage 7: Embedding Processor
    
    Generates vector embeddings for chunks to enable semantic search.
    """

    @staticmethod
    def _make_json_safe(value: Any) -> Any:
        """Recursively convert values to JSON-serializable types."""
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {str(k): EmbeddingProcessor._make_json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [EmbeddingProcessor._make_json_safe(v) for v in value]
        if isinstance(value, tuple):
            return [EmbeddingProcessor._make_json_safe(v) for v in value]
        if isinstance(value, set):
            return [EmbeddingProcessor._make_json_safe(v) for v in value]
        return value

    def __init__(
        self,
        supabase_client=None,
        ollama_url: Optional[str] = None,
        model_name: str = None,
        batch_size: int = 100,
        embedding_dimension: int = 768,
        min_batch_size: int = 25,
        max_batch_size: int = 200,
        batch_adjust_step: int = 10
    ):
        """
        Initialize embedding processor
        
        Args:
            supabase_client: Supabase client for storage
            ollama_url: Ollama API URL (default: from env)
            model_name: Embedding model name (default: from OLLAMA_MODEL_EMBEDDING env)
            batch_size: Number of chunks to embed per batch
            embedding_dimension: Dimension of embedding vectors (768 for embeddinggemma, nomic-embed-text)
        """
        super().__init__(name="embedding_processor")
        self.stage = Stage.EMBEDDING
        self.supabase = supabase_client
        self.node_id = platform.node() or os.getenv("COMPUTERNAME", "unknown-host")
        self.min_batch_size = max(1, min_batch_size)
        self.max_batch_size = max(self.min_batch_size, max_batch_size)
        self.batch_adjust_step = max(1, batch_adjust_step)
        self.batch_size = max(self.min_batch_size, min(self.max_batch_size, batch_size))
        self.embedding_dimension = embedding_dimension
        
        # Ollama configuration
        self.ollama_url = ollama_url or os.getenv('OLLAMA_URL', 'http://localhost:11434')
        # Read model from env if not provided
        self.model_name = model_name or os.getenv('OLLAMA_MODEL_EMBEDDING', 'nomic-embed-text:latest')

        # HTTP session & retry configuration
        self.request_timeout = float(os.getenv('EMBEDDING_REQUEST_TIMEOUT', '30'))
        self.max_retries = int(os.getenv('EMBEDDING_REQUEST_MAX_RETRIES', '4'))
        self.retry_base_delay = float(os.getenv('EMBEDDING_RETRY_BASE_DELAY', '1.0'))
        self.retry_jitter = float(os.getenv('EMBEDDING_RETRY_JITTER', '0.5'))
        self.session = self._create_session()

        # Adaptive batching configuration
        self.target_latency_lower = float(os.getenv('EMBEDDING_TARGET_LATENCY_LOWER', '1.0'))
        self.target_latency_upper = float(os.getenv('EMBEDDING_TARGET_LATENCY_UPPER', '2.0'))
        state_path_env = os.getenv('EMBEDDING_BATCH_STATE_PATH')
        default_state_dir = Path(os.getenv('KRAI_STATE_DIR', Path.cwd() / 'state'))
        default_state_dir.mkdir(parents=True, exist_ok=True)
        self.batch_state_path = Path(state_path_env) if state_path_env else default_state_dir / 'embedding_batch_state.json'
        self._batch_latency_window: deque = deque(maxlen=50)
        self._load_persisted_batch_size()

        # Stage tracker
        if supabase_client:
            self.stage_tracker = StageTracker(supabase_client)
        else:
            self.stage_tracker = None
        
        # Check Ollama availability
        self.ollama_available = self._check_ollama()
    
    def _create_session(self) -> requests.Session:
        """Create a persistent HTTP session with retry-aware adapter."""
        session = requests.Session()
        adapter_retries = max(0, self.max_retries - 1)
        retry = Retry(
            total=adapter_retries,
            read=adapter_retries,
            connect=adapter_retries,
            backoff_factor=self.retry_base_delay,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=int(os.getenv('EMBEDDING_HTTP_POOL_CONNECTIONS', '10')),
            pool_maxsize=int(os.getenv('EMBEDDING_HTTP_POOL_MAXSIZE', '20'))
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _load_persisted_batch_size(self) -> None:
        """Load persisted batch configuration if available."""
        try:
            if self.batch_state_path.exists():
                with self.batch_state_path.open("r", encoding="utf-8") as f:
                    state = json.load(f)
                node_state = state.get(self.node_id)
                if node_state:
                    persisted_batch = node_state.get("batch_size")
                    if persisted_batch:
                        self.batch_size = max(
                            self.min_batch_size,
                            min(self.max_batch_size, int(persisted_batch))
                        )
                        self.logger.debug(
                            "Restored batch_size=%s for node=%s", self.batch_size, self.node_id
                        )
        except Exception as exc:
            self.logger.warning("Failed to load persisted batch size: %s", exc)

    def _persist_batch_size(self) -> None:
        """Persist current batch size to disk for warm starts."""
        try:
            state = {}
            if self.batch_state_path.exists():
                with self.batch_state_path.open("r", encoding="utf-8") as f:
                    state = json.load(f)
            state[self.node_id] = {
                "batch_size": self.batch_size,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            with self.batch_state_path.open("w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as exc:
            self.logger.warning("Failed to persist batch size: %s", exc)

    def _record_batch_latency(self, latency: float) -> None:
        """Track recent batch latencies for adaptive scaling."""
        self._batch_latency_window.append(latency)
        if len(self._batch_latency_window) == self._batch_latency_window.maxlen:
            try:
                import statistics

                p95 = statistics.quantiles(self._batch_latency_window, n=100)[94]
                p99 = statistics.quantiles(self._batch_latency_window, n=100)[98]
                self.logger.debug(
                    "Batch latency percentiles: p95=%.2fs p99=%.2fs",
                    p95,
                    p99,
                )
            except Exception:
                pass

    def _adjust_batch_size(self, latency: float) -> None:
        """Adjust batch size based on observed latency."""
        if latency < self.target_latency_lower and self.batch_size < self.max_batch_size:
            new_size = min(self.max_batch_size, self.batch_size + self.batch_adjust_step)
            if new_size != self.batch_size:
                self.logger.info(
                    "Increasing batch size from %s to %s (latency %.2fs < %.2fs)",
                    self.batch_size,
                    new_size,
                    latency,
                    self.target_latency_lower,
                )
                self.batch_size = new_size
                self._persist_batch_size()
        elif latency > self.target_latency_upper and self.batch_size > self.min_batch_size:
            new_size = max(self.min_batch_size, self.batch_size - self.batch_adjust_step)
            if new_size != self.batch_size:
                self.logger.info(
                    "Decreasing batch size from %s to %s (latency %.2fs > %.2fs)",
                    self.batch_size,
                    new_size,
                    latency,
                    self.target_latency_upper,
                )
                self.batch_size = new_size
                self._persist_batch_size()

    def _check_ollama(self) -> bool:
        """Check if Ollama is available and has the embedding model"""
        with self.logger_context(stage=self.stage):
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)

                if response.status_code == 200:
                    models = response.json().get('models', [])

                    model_names = [m.get('name', '').lower() for m in models]

                    if any(self.model_name in name for name in model_names):
                        self.logger.success(f"Ollama available with {self.model_name}")
                        return True
                    self.logger.warning(f"Model {self.model_name} not found in Ollama")
                    self.logger.info(f"Install with: ollama pull {self.model_name}")
                    return False

                self.logger.warning("Ollama not responding")
                return False

            except Exception as e:
                self.logger.warning(f"Ollama check failed: {e}")
                self.logger.info("Make sure Ollama is running: ollama serve")
                return False
    
    def is_configured(self) -> bool:
        """Check if embedding processor is properly configured"""
        return self.ollama_available and self.supabase is not None
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get detailed configuration status for debugging"""
        return {
            'is_configured': self.is_configured(),
            'ollama_available': self.ollama_available,
            'ollama_url': self.ollama_url,
            'model_name': self.model_name,
            'supabase_configured': self.supabase is not None,
            'embedding_dimension': self.embedding_dimension,
            'batch_size': self.batch_size
        }
    
    async def process(self, context) -> Dict[str, Any]:
        """Async pipeline entrypoint wrapping `process_document`."""
        if not hasattr(context, 'document_id'):
            raise ValueError("Processing context must include 'document_id'")

        chunks = getattr(context, 'chunks', None)
        if chunks is None:
            chunks = getattr(context, 'chunk_data', None)

        if chunks is None:
            return {
                'success': False,
                'error': 'No chunks provided for embedding generation',
                'embeddings_created': 0
            }

        track_stage = getattr(context, 'track_stage', True)

        loop = asyncio.get_running_loop()
        manufacturer = getattr(context, 'manufacturer', None) or getattr(context, 'processing_config', {}).get('manufacturer')
        document_type = getattr(context, 'document_type', None) or getattr(context, 'processing_config', {}).get('document_type')

        with metrics.stage_timer(
            stage=self.stage.value,
            manufacturer=manufacturer or 'unknown',
            document_type=document_type or 'unknown'
        ) as timer:
            try:
                result = await loop.run_in_executor(
                    None,
                    self.process_document,
                    context.document_id,
                    chunks,
                    track_stage
                )
            except Exception as exc:
                timer.stop(success=False, error_label=str(exc))
                raise
            else:
                timer.stop(
                    success=bool(result.get('success')),
                    error_label=str(result.get('error')) if result.get('error') else None
                )

        return result

    def process_document(
        self,
        document_id: UUID,
        chunks: List[Dict[str, Any]],
        track_stage: bool = True
    ) -> Dict[str, Any]:
        """
        Generate embeddings for all chunks in a document
        
        Args:
            document_id: Document UUID
            chunks: List of chunk dicts with 'text' field
            
        Returns:
            Dict with processing results
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Embedding processor not configured',
                'embeddings_created': 0
            }
        
        # Start stage tracking
        stage_tracker = self.stage_tracker if track_stage and self.stage_tracker else None

        if stage_tracker:
            self.stage_tracker.start_stage(str(document_id), self.stage.value)
        
        with self.logger_context(document_id=document_id, stage=self.stage) as adapter:
            try:
                adapter.info("Generating embeddings for %d chunks...", len(chunks))
                start_time = time.time()
                total_embedded = 0
                failed_chunks = []

                total_chunks = len(chunks)
                batch_index = 0
                processed_count = 0
                total_characters = 0
                total_non_empty_chunks = 0
                total_truncated_chunks = 0

                while processed_count < total_chunks:
                    batch_index += 1
                    current_batch_size = self.batch_size
                    batch = chunks[processed_count:processed_count + current_batch_size]
                    if not batch:
                        break

                    total_batches = max(1, (total_chunks + current_batch_size - 1) // current_batch_size)

                    adapter.info(
                        "Processing batch %d/%d (%d chunks, size=%d)...",
                        batch_index,
                        total_batches,
                        len(batch),
                        current_batch_size
                    )

                    batch_start = time.perf_counter()
                    batch_result = self._embed_batch(batch, document_id)
                    batch_latency = time.perf_counter() - batch_start

                    batch_stats = [text_stats(chunk.get('text', '')) for chunk in batch]
                    batch_total_chars = sum(stat['length'] for stat in batch_stats)
                    batch_non_empty = sum(1 for stat in batch_stats if not stat['empty'])
                    batch_truncated = sum(1 for stat in batch_stats if stat.get('truncated'))
                    total_characters += batch_total_chars
                    total_non_empty_chunks += batch_non_empty
                    total_truncated_chunks += batch_truncated
                    avg_chars = (batch_total_chars / len(batch)) if batch else 0.0

                    adapter.debug(
                        "Batch %d text stats: total_chars=%d avg_chars=%.1f non_empty=%d truncated=%d",
                        batch_index,
                        batch_total_chars,
                        avg_chars,
                        batch_non_empty,
                        batch_truncated,
                    )

                    if batch_latency > 0:
                        self._record_batch_latency(batch_latency)
                        self._adjust_batch_size(batch_latency)

                    total_embedded += batch_result['success_count']
                    failed_chunks.extend(batch_result['failed_chunks'])
                    processed_count += len(batch)

                    if self.stage_tracker:
                        progress = (processed_count / total_chunks) * 100
                        self.stage_tracker.update_stage_progress(
                            str(document_id),
                            self.stage.value,
                            progress,
                            metadata={
                                'chunks_embedded': total_embedded,
                                'batch': f"{batch_index}/{total_batches}",
                                'batch_latency': round(batch_latency, 3),
                                'batch_chars': batch_total_chars,
                                'batch_non_empty': batch_non_empty,
                                'batch_truncated': batch_truncated,
                            }
                        )

                processing_time = time.time() - start_time
                chunks_per_second = (total_embedded / processing_time) if processing_time else 0.0

                if stage_tracker:
                    metadata = {
                        'embeddings_created': total_embedded,
                        'processing_time': round(processing_time, 2),
                        'chunks_per_second': round(chunks_per_second, 2),
                        'failed_chunks': len(failed_chunks),
                        'total_characters': total_characters,
                        'non_empty_chunks': total_non_empty_chunks,
                        'truncated_chunks': total_truncated_chunks,
                    }

                    if total_embedded == 0 and failed_chunks:
                        stage_tracker.fail_stage(
                            str(document_id),
                            self.stage.value,
                            f"Failed to embed all {len(failed_chunks)} chunks"
                        )
                    else:
                        if failed_chunks:
                            metadata['status'] = 'partial'
                        stage_tracker.complete_stage(
                            str(document_id),
                            self.stage.value,
                            metadata=metadata
                        )

                self.logger.success(
                    "Created %d embeddings in %.1fs (%.1f chunks/s) | total_chars=%d truncated=%d",
                    total_embedded,
                    processing_time,
                    chunks_per_second,
                    total_characters,
                    total_truncated_chunks,
                )

                partial_success = total_embedded > 0 and len(failed_chunks) > 0

                if partial_success:
                    self.logger.warning(
                        f"Embedding generation partial: {total_embedded} succeeded, {len(failed_chunks)} failed"
                    )

                return {
                    'success': total_embedded > 0,
                    'partial_success': partial_success,
                    'embeddings_created': total_embedded,
                    'failed_count': len(failed_chunks),
                    'failed_chunks': failed_chunks,
                    'processing_time': processing_time
                }

            except Exception as e:
                error_msg = f"Embedding generation failed: {e}"
                self.logger.error(error_msg)
                adapter.error("Embedding generation failed: %s", e)

                if self.stage_tracker:
                    self.stage_tracker.fail_stage(
                        str(document_id),
                        self.stage.value,
                        error_msg
                    )

                return {
                    'success': False,
                    'error': error_msg,
                    'embeddings_created': 0
                }
    
    def _embed_batch(
        self,
        chunks: List[Dict[str, Any]],
        document_id: UUID
    ) -> Dict[str, Any]:
        """
        Generate embeddings for a batch of chunks
        
        Args:
            chunks: List of chunks
            document_id: Document UUID
            
        Returns:
            Dict with batch results
        """
        success_count = 0
        failed_chunks = []
        
        for chunk in chunks:
            try:
                # Generate embedding
                embedding = self._generate_embedding(chunk['text'])
                
                if embedding is None:
                    failed_chunks.append({
                        'chunk_id': chunk.get('chunk_id'),
                        'error': 'Failed to generate embedding'
                    })
                    continue
                
                # Store in database
                stored = self._store_embedding(
                    chunk_id=chunk['chunk_id'],
                    document_id=document_id,
                    embedding=embedding,
                    chunk_data=chunk
                )
                
                if stored:
                    success_count += 1
                else:
                    failed_chunks.append({
                        'chunk_id': chunk.get('chunk_id'),
                        'error': 'Failed to store embedding'
                    })
                    
            except Exception as e:
                self.logger.debug(f"Failed to embed chunk: {e}")
                failed_chunks.append({
                    'chunk_id': chunk.get('chunk_id'),
                    'error': str(e)
                })
        
        return {
            'success_count': success_count,
            'failed_chunks': failed_chunks
        }
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using Ollama
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None
        """
        max_attempts = max(1, self.max_retries)
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = self.session.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": self.model_name,
                        "prompt": text
                    },
                    timeout=self.request_timeout
                )

                if response.status_code == 200:
                    try:
                        result = response.json()
                    except ValueError as json_error:
                        self.logger.error(
                            "Embedding API returned invalid JSON (attempt %d/%d): %s | body=%s",
                            attempt,
                            max_attempts,
                            json_error,
                            response.text[:200],
                        )
                        last_error = f"invalid_json: {json_error}"
                        return None

                    embedding = result.get('embedding')

                    if embedding and len(embedding) == self.embedding_dimension:
                        if attempt > 1:
                            self.logger.info("Embedding request succeeded after %d retries", attempt - 1)
                        return embedding

                    self.logger.error(
                        "Embedding response missing or malformed 'embedding' field (len=%s) [attempt %d/%d]: %s",
                        len(embedding) if embedding else 0,
                        attempt,
                        max_attempts,
                        str(result)[:200]
                    )
                    last_error = "malformed_embedding"
                    return None

                # Determine if transient
                if response.status_code >= 500:
                    retry_delay = self.retry_base_delay * (2 ** (attempt - 1))
                    jitter = random.uniform(0, self.retry_jitter)
                    sleep_time = retry_delay + jitter
                    if attempt < max_attempts:
                        self.logger.warning(
                            "Embedding API transient error %s on attempt %d/%d - retrying in %.2fs",
                            response.status_code,
                            attempt,
                            max_attempts,
                            sleep_time
                        )
                        time.sleep(sleep_time)
                        last_error = f"status_{response.status_code}"
                        continue
                    last_error = f"status_{response.status_code}"

                else:
                    self.logger.error(
                        "Embedding API error %s: %s",
                        response.status_code,
                        response.text[:200]
                    )
                    last_error = f"status_{response.status_code}"
                    return None

            except (requests_exceptions.ConnectionError, requests_exceptions.Timeout) as exc:
                retry_delay = self.retry_base_delay * (2 ** (attempt - 1))
                jitter = random.uniform(0, self.retry_jitter)
                sleep_time = retry_delay + jitter
                if attempt < max_attempts:
                    self.logger.warning(
                        "Embedding request connection issue on attempt %d/%d: %s - retrying in %.2fs",
                        attempt,
                        max_attempts,
                        exc,
                        sleep_time
                    )
                    time.sleep(sleep_time)
                    last_error = f"connection_error: {exc}"
                    continue
                self.logger.error(
                    "Embedding request failed after %d attempts due to connection issues: %s",
                    max_attempts,
                    exc
                )
                last_error = f"connection_error: {exc}"
                return None
            except Exception as exc:
                self.logger.error(
                    "Embedding generation error on attempt %d/%d: %s",
                    attempt,
                    max_attempts,
                    exc
                )
                last_error = str(exc)
                return None

            # If we reached here due to non-retriable status or after retries exhausted
            break

        self.logger.error(
            "Embedding generation failed after %d attempts%s",
            max_attempts,
            f" (last_error={last_error})" if last_error else ""
        )
        return None
    
    def _store_embedding(
        self,
        chunk_id: str,
        document_id: UUID,
        embedding: List[float],
        chunk_data: Dict[str, Any]
    ) -> bool:
        """
        Store embedding in Supabase with pgvector
        
        Args:
            chunk_id: Chunk ID
            document_id: Document UUID
            embedding: Embedding vector
            chunk_data: Chunk metadata
            
        Returns:
            True if successful
        """
        if not self.supabase:
            return False
        
        try:
            # Prepare record for krai_intelligence.chunks table
            # Note: Supabase client uses public schema by default, 
            # but RLS policies route to correct schema
            
            # Preserve existing metadata from chunk (includes header metadata, etc.)
            existing_metadata = chunk_data.get('metadata', {})
            
            # Update with required fields (don't overwrite if already exists)
            metadata = {
                'char_count': existing_metadata.get('char_count', len(chunk_data.get('text', ''))),
                'word_count': existing_metadata.get('word_count', len(chunk_data.get('text', '').split())),
                'chunk_type': existing_metadata.get('chunk_type', chunk_data.get('chunk_type', 'text')),
                'embedded_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Merge with existing metadata (preserve header_metadata, etc.)
            for key, value in existing_metadata.items():
                if key not in metadata:  # Don't overwrite the standard fields
                    metadata[key] = value
            
            record = {
                'id': str(chunk_id),
                'document_id': str(document_id),
                'text_chunk': chunk_data.get('text', ''),  # Column name is text_chunk
                'chunk_index': chunk_data.get('chunk_index', 0),
                'page_start': chunk_data.get('page_start', chunk_data.get('page_numbers', [None])[0]),
                'page_end': chunk_data.get('page_end', chunk_data.get('page_numbers', [None])[-1] if chunk_data.get('page_numbers') else None),
                'fingerprint': str(chunk_data.get('fingerprint', chunk_id)),  # Use chunk_id as fallback
                'embedding': embedding,  # pgvector will handle this
                'metadata': metadata  # Now includes all metadata from chunker!
            }

            record = self._make_json_safe(record)
            
            table = self.supabase.table('vw_chunks')

            if hasattr(table, 'upsert'):
                try:
                    table.upsert(record).execute()
                    return True
                except Exception as e:
                    self.logger.error(f"Embedding upsert failed (chunk={chunk_id}): {e}")

            try:
                table.insert(record).execute()
                return True
            except Exception as insert_error:
                self.logger.error(f"Embedding insert failed (chunk={chunk_id}): {insert_error}")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to store embedding (chunk={chunk_id}): {e}")
            return False
    
    def search_similar(
        self,
        query_text: str,
        limit: int = 10,
        document_id: Optional[UUID] = None,
        similarity_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using vector similarity
        
        Args:
            query_text: Search query
            limit: Number of results to return
            document_id: Optional filter by document
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of similar chunks with scores
        """
        if not self.is_configured():
            self.logger.warning("Search not available - processor not configured")
            return []
        
        try:
            # Generate embedding for query
            query_embedding = self._generate_embedding(query_text)
            
            if query_embedding is None:
                self.logger.error("Failed to generate query embedding")
                return []
            
            # Search using pgvector similarity
            # This uses cosine similarity via pgvector extension
            # RPC function needs to be created in Supabase
            
            params = {
                'query_embedding': query_embedding,
                'match_threshold': similarity_threshold,
                'match_count': limit
            }
            
            if document_id:
                params['filter_document_id'] = str(document_id)
            
            result = self.supabase.rpc('match_chunks', params).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            self.logger.error(f"Similarity search failed: {e}")
            return []


# Example usage
if __name__ == "__main__":
    from uuid import uuid4
    
    processor = EmbeddingProcessor()
    
    if processor.is_configured():
        print("✅ Embedding Processor configured")
        print(f"   Model: {processor.model_name}")
        print(f"   Dimension: {processor.embedding_dimension}")
        print(f"   Batch size: {processor.batch_size}")
        
        # Test embedding
        test_text = "This is a test sentence for embedding generation."
        embedding = processor._generate_embedding(test_text)
        
        if embedding:
            print(f"\n✅ Test embedding generated!")
            print(f"   Dimension: {len(embedding)}")
            print(f"   Sample values: {embedding[:5]}...")
        else:
            print("\n❌ Test embedding failed")
    else:
        print("⚠️  Embedding Processor not configured")
        print("\nRequirements:")
        print("  1. Ollama running: ollama serve")
        print("  2. Model installed: ollama pull embeddinggemma")
        print("  3. Supabase client configured")
