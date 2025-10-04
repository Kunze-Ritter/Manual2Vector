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
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import UUID
import time
import requests
from datetime import datetime

from .logger import get_logger
from .stage_tracker import StageTracker


class EmbeddingProcessor:
    """
    Stage 7: Embedding Processor
    
    Generates vector embeddings for chunks to enable semantic search.
    """
    
    def __init__(
        self,
        supabase_client=None,
        ollama_url: Optional[str] = None,
        model_name: str = "embeddinggemma",
        batch_size: int = 100,
        embedding_dimension: int = 768
    ):
        """
        Initialize embedding processor
        
        Args:
            supabase_client: Supabase client for storage
            ollama_url: Ollama API URL (default: from env)
            model_name: Embedding model name (default: embeddinggemma)
            batch_size: Number of chunks to embed per batch
            embedding_dimension: Dimension of embedding vectors (768 for embeddinggemma)
        """
        self.logger = get_logger()
        self.supabase = supabase_client
        self.batch_size = batch_size
        self.embedding_dimension = embedding_dimension
        
        # Ollama configuration
        self.ollama_url = ollama_url or os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.model_name = model_name
        
        # Stage tracker
        if supabase_client:
            self.stage_tracker = StageTracker(supabase_client)
        else:
            self.stage_tracker = None
        
        # Check Ollama availability
        self.ollama_available = self._check_ollama()
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is available and has the embedding model"""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                
                # Check if our embedding model is available
                model_names = [m.get('name', '').lower() for m in models]
                
                if any(self.model_name in name for name in model_names):
                    self.logger.success(f"Ollama available with {self.model_name}")
                    return True
                else:
                    self.logger.warning(f"Model {self.model_name} not found in Ollama")
                    self.logger.info(f"Install with: ollama pull {self.model_name}")
                    return False
            else:
                self.logger.warning("Ollama not responding")
                return False
                
        except Exception as e:
            self.logger.warning(f"Ollama check failed: {e}")
            self.logger.info("Make sure Ollama is running: ollama serve")
            return False
    
    def is_configured(self) -> bool:
        """Check if embedding processor is properly configured"""
        return self.ollama_available and self.supabase is not None
    
    def process_document(
        self,
        document_id: UUID,
        chunks: List[Dict[str, Any]]
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
        if self.stage_tracker:
            self.stage_tracker.start_stage(str(document_id), 'embeddings')
        
        try:
            self.logger.info(f"Generating embeddings for {len(chunks)} chunks...")
            
            start_time = time.time()
            
            # Process in batches
            total_embedded = 0
            failed_chunks = []
            
            for i in range(0, len(chunks), self.batch_size):
                batch = chunks[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size
                
                self.logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
                
                # Generate embeddings for batch
                batch_result = self._embed_batch(batch, document_id)
                
                total_embedded += batch_result['success_count']
                failed_chunks.extend(batch_result['failed_chunks'])
                
                # Update progress
                if self.stage_tracker:
                    progress = (i + len(batch)) / len(chunks)
                    self.stage_tracker.update_stage_progress(
                        str(document_id),
                        'embeddings',
                        progress,
                        metadata={
                            'chunks_embedded': total_embedded,
                            'batch': f"{batch_num}/{total_batches}"
                        }
                    )
            
            processing_time = time.time() - start_time
            
            # Complete stage tracking
            if self.stage_tracker:
                if failed_chunks:
                    self.stage_tracker.fail_stage(
                        str(document_id),
                        'embeddings',
                        f"Failed to embed {len(failed_chunks)} chunks"
                    )
                else:
                    self.stage_tracker.complete_stage(
                        str(document_id),
                        'embeddings',
                        metadata={
                            'embeddings_created': total_embedded,
                            'processing_time': round(processing_time, 2),
                            'chunks_per_second': round(total_embedded / processing_time, 2)
                        }
                    )
            
            self.logger.success(
                f"Created {total_embedded} embeddings in {processing_time:.1f}s "
                f"({total_embedded/processing_time:.1f} chunks/s)"
            )
            
            return {
                'success': len(failed_chunks) == 0,
                'embeddings_created': total_embedded,
                'failed_count': len(failed_chunks),
                'failed_chunks': failed_chunks,
                'processing_time': processing_time
            }
            
        except Exception as e:
            error_msg = f"Embedding generation failed: {e}"
            self.logger.error(error_msg)
            
            if self.stage_tracker:
                self.stage_tracker.fail_stage(
                    str(document_id),
                    'embeddings',
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
        try:
            # Call Ollama embeddings API
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get('embedding')
                
                # Validate embedding
                if embedding and len(embedding) == self.embedding_dimension:
                    return embedding
                else:
                    self.logger.warning(f"Invalid embedding dimension: {len(embedding) if embedding else 0}")
                    return None
            else:
                self.logger.warning(f"Embedding API error: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.debug(f"Embedding generation error: {e}")
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
            record = {
                'id': chunk_id,
                'document_id': str(document_id),
                'text_chunk': chunk_data.get('text', ''),  # Column name is text_chunk
                'chunk_index': chunk_data.get('chunk_index', 0),
                'page_start': chunk_data.get('page_start', chunk_data.get('page_numbers', [None])[0]),
                'page_end': chunk_data.get('page_end', chunk_data.get('page_numbers', [None])[-1] if chunk_data.get('page_numbers') else None),
                'fingerprint': chunk_data.get('fingerprint', chunk_id),  # Use chunk_id as fallback
                'embedding': embedding,  # pgvector will handle this
                'metadata': {
                    'char_count': len(chunk_data.get('text', '')),
                    'word_count': len(chunk_data.get('text', '').split()),
                    'chunk_type': chunk_data.get('chunk_type', 'text'),
                    'embedded_at': datetime.utcnow().isoformat()
                }
            }
            
            # Upsert to chunks (view routes to krai_intelligence.chunks)
            result = self.supabase.table('chunks').upsert(record).execute()
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Failed to store embedding: {e}")
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
