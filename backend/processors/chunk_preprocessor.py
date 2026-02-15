"""
Chunk Preprocessor - Preprocess chunks before embedding

Stage 5 of the processing pipeline.

Cleans up chunks by removing headers/footers, normalizing whitespace,
and detecting chunk types for better embedding quality.
"""

import re
import json
from typing import Any, Dict, List

from backend.core.base_processor import BaseProcessor, Stage


class ChunkPreprocessor(BaseProcessor):
    """
    Stage 5: Chunk Preprocessor
    
    Preprocesses chunks before embedding generation.
    Removes noise, normalizes text, and enriches metadata.
    """
    
    def __init__(self, database_service=None, config_service=None):
        """
        Initialize chunk preprocessor
        
        Args:
            database_service: Database service instance
        """
        super().__init__(name="chunk_preprocessor")
        self.stage = Stage.CHUNK_PREPROCESSING
        self.database_service = database_service
        self.config_service = config_service
        
        # Header/footer patterns to remove
        self.header_patterns = [
            r'^\d+\s*$',  # Page numbers alone
            r'^Page \d+ of \d+$',
            r'^Chapter \d+$',
            r'^\d{1,3}\s*[A-Z][a-z]+\s+\d{4}$',  # Date headers
        ]
        
        # Footer patterns
        self.footer_patterns = [
            r'Copyright.*\d{4}',
            r'Confidential.*',
            r'Proprietary.*',
        ]
        
        self.logger.info("ChunkPreprocessor initialized")
    
    async def process(self, context) -> Any:
        """
        Process chunk preprocessing
        
        Args:
            context: Processing context with document_id
            
        Returns:
            Processing result with chunks_preprocessed count
        """
        document_id = getattr(context, "document_id", None)

        with self.logger_context(document_id=document_id, stage=self.stage) as adapter:
            try:
                chunks = await self._get_document_chunks(document_id, adapter)

                if not chunks:
                    adapter.warning("No chunks found to preprocess")
                    return self._create_result(
                        success=True,
                        message="No chunks found to preprocess (skipped)",
                        data={'chunks_preprocessed': 0}
                    )

                adapter.info("Preprocessing %s chunks", len(chunks))

                preprocessed_count = 0
                for chunk in chunks:
                    try:
                        original_content = (
                            chunk.get('content')
                            or chunk.get('text_chunk')
                            or chunk.get('chunk_text')
                            or ''
                        )
                        cleaned_content = self._clean_chunk(original_content)

                        chunk_type = self._detect_chunk_type(cleaned_content)

                        metadata = self._normalize_metadata(chunk.get('metadata'))
                        metadata['preprocessed'] = True
                        metadata['chunk_type'] = chunk_type
                        metadata['original_length'] = len(original_content)
                        metadata['cleaned_length'] = len(cleaned_content)

                        chunk_id = chunk.get('id')
                        if chunk_id and self.database_service:
                            updated = await self._update_chunk(
                                chunk_id,
                                cleaned_content,
                                metadata,
                                adapter
                            )
                            if updated:
                                preprocessed_count += 1

                    except Exception as e:
                        adapter.warning("Failed to preprocess chunk %s: %s", chunk.get('id'), e)

                adapter.info("Preprocessed %s chunks", preprocessed_count)
                self.logger.success(f"✅ Preprocessed {preprocessed_count} chunks")

                return self._create_result(
                    success=True,
                    message=f"Chunk preprocessing completed: {preprocessed_count} chunks",
                    data={
                        'chunks_preprocessed': preprocessed_count,
                        'total_chunks': len(chunks)
                    }
                )

            except Exception as e:
                adapter.error("Chunk preprocessing failed: %s", e)
                self.logger.error(f"Chunk preprocessing failed: {e}")
                return self._create_result(
                    success=False,
                    message=f"Chunk preprocessing error: {str(e)}",
                    data={}
                )
    
    def _clean_chunk(self, content: str) -> str:
        """
        Clean chunk content
        
        Removes:
        - Headers and footers
        - Excessive whitespace
        - Page numbers
        - Repeated characters
        """
        if not content:
            return content
        
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
            
            # Check header patterns
            is_header = False
            for pattern in self.header_patterns:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    is_header = True
                    break
            
            if is_header:
                continue
            
            # Check footer patterns
            is_footer = False
            for pattern in self.footer_patterns:
                if re.search(pattern, line.strip(), re.IGNORECASE):
                    is_footer = True
                    break
            
            if is_footer:
                continue
            
            # Normalize whitespace
            cleaned_line = re.sub(r'\s+', ' ', line.strip())
            
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        # Join lines
        cleaned_content = '\n'.join(cleaned_lines)
        
        # Remove repeated newlines
        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
        
        return cleaned_content.strip()
    
    def _detect_chunk_type(self, content: str) -> str:
        """
        Detect chunk type based on content
        
        Types:
        - error_code: Contains error codes
        - parts_list: Contains part numbers
        - procedure: Contains step-by-step instructions
        - specification: Contains technical specs
        - table: Contains tabular data
        - text: General text
        """
        if not content:
            return 'empty'
        
        content_lower = content.lower()
        
        # Error code detection
        if re.search(r'\b[A-Z]\d{2,3}[-\s]?\d{2,3}\b', content):
            return 'error_code'
        
        # Parts list detection
        if re.search(r'\b[A-Z]{2,3}[-\s]?\d{4,6}\b', content) and any(kw in content_lower for kw in ['part', 'item', 'component']):
            return 'parts_list'
        
        # Procedure detection
        if re.search(r'^\d+\.\s+', content, re.MULTILINE) or any(kw in content_lower for kw in ['step', 'procedure', 'install', 'remove', 'replace']):
            return 'procedure'
        
        # Specification detection
        if any(kw in content_lower for kw in ['specification', 'dimensions', 'weight', 'capacity', 'speed', 'resolution']):
            return 'specification'
        
        # Table detection (simple heuristic)
        lines = content.split('\n')
        if len(lines) > 3:
            # Check if multiple lines have similar structure (tabs or multiple spaces)
            structured_lines = sum(1 for line in lines if '\t' in line or re.search(r'\s{3,}', line))
            if structured_lines / len(lines) > 0.5:
                return 'table'
        
        return 'text'

    @staticmethod
    def _normalize_metadata(raw_metadata: Any) -> Dict[str, Any]:
        """Normalize chunk metadata to a mutable dict."""
        if isinstance(raw_metadata, dict):
            return dict(raw_metadata)
        if isinstance(raw_metadata, str):
            try:
                parsed = json.loads(raw_metadata)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
        return {}
    
    async def _get_document_chunks(self, document_id: str, adapter) -> List[Dict]:
        """Get all chunks for document via DatabaseAdapter or Supabase client. Fails or warns when neither is available."""
        if not self.database_service:
            adapter.warning("Cannot get chunks: no database_service available")
            return []

        has_adapter = hasattr(self.database_service, 'get_chunks_by_document')
        has_client = hasattr(self.database_service, 'client') and self.database_service.client is not None

        if not has_adapter and not has_client:
            adapter.warning(
                "Cannot get chunks: neither DatabaseAdapter (get_chunks_by_document) nor Supabase client available"
            )
            return []

        try:
            if has_adapter:
                chunks = await self.database_service.get_chunks_by_document(document_id)
            else:
                result = self.database_service.client.table('chunks').select('*').eq('document_id', document_id).order('chunk_index').execute()
                chunks = result.data if result.data else []
            return chunks or []
        except Exception as e:
            adapter.warning("Could not get chunks: %s", e)
            return []
    
    async def _update_chunk(self, chunk_id: str, content: str, metadata: Dict, adapter) -> bool:
        """Update chunk with cleaned content and metadata via DatabaseAdapter or Supabase client. Returns True if updated."""
        if not self.database_service:
            adapter.warning("Cannot update chunk: no database_service available")
            return False

        has_adapter = hasattr(self.database_service, 'update_chunk')
        has_client = hasattr(self.database_service, 'client') and self.database_service.client is not None

        if not has_adapter and not has_client:
            adapter.warning(
                "Cannot update chunk: neither DatabaseAdapter (update_chunk) nor Supabase client available"
            )
            return False

        try:
            if has_adapter:
                return await self.database_service.update_chunk(
                    chunk_id, content=content, metadata=metadata, char_count=len(content)
                )
            else:
                self.database_service.client.table('chunks').update({
                    'content': content,
                    'metadata': metadata,
                    'char_count': len(content)
                }).eq('id', chunk_id).execute()
                return True
        except Exception as e:
            adapter.warning("Failed to update chunk %s: %s", chunk_id, e)
            return False
    
    def _create_result(self, success: bool, message: str, data: Dict) -> Dict[str, Any]:
        """Create a BaseProcessor-compatible result payload."""
        return {
            "success": success,
            "data": data or {},
            "metadata": {"message": message},
            "error": None if success else message,
        }
