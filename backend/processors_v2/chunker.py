"""
Smart Text Chunking Module

Splits text into chunks with overlap, preserving context.
Respects paragraph boundaries and error code sections.
"""

import re
import hashlib
from typing import List, Dict
from uuid import UUID

from .logger import get_logger
from .models import TextChunk


logger = get_logger()


class SmartChunker:
    """Intelligent text chunking with context preservation"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        overlap_size: int = 100,
        min_chunk_size: int = 50
    ):
        """
        Initialize chunker
        
        Args:
            chunk_size: Target chunk size in characters
            overlap_size: Overlap between chunks
            min_chunk_size: Minimum chunk size (reject smaller)
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
        self.logger = get_logger()
    
    def chunk_document(
        self,
        page_texts: Dict[int, str],
        document_id: UUID
    ) -> List[TextChunk]:
        """
        Chunk entire document with page-aware splitting
        
        Args:
            page_texts: Dictionary {page_number: text}
            document_id: Document UUID
            
        Returns:
            List of TextChunk objects
        """
        all_chunks = []
        chunk_index = 0
        
        # Process pages in order
        sorted_pages = sorted(page_texts.keys())
        
        for page_num in sorted_pages:
            text = page_texts[page_num]
            
            if not text or len(text.strip()) < self.min_chunk_size:
                continue
            
            # Chunk this page
            page_chunks = self._chunk_text(
                text=text,
                page_start=page_num,
                page_end=page_num,
                document_id=document_id,
                start_index=chunk_index
            )
            
            all_chunks.extend(page_chunks)
            chunk_index += len(page_chunks)
        
        self.logger.success(
            f"Created {len(all_chunks)} chunks from {len(sorted_pages)} pages"
        )
        
        return all_chunks
    
    def _chunk_text(
        self,
        text: str,
        page_start: int,
        page_end: int,
        document_id: UUID,
        start_index: int = 0
    ) -> List[TextChunk]:
        """
        Chunk single text with overlap
        
        Args:
            text: Text to chunk
            page_start: Starting page number
            page_end: Ending page number
            document_id: Document UUID
            start_index: Starting chunk index
            
        Returns:
            List of TextChunk objects
        """
        if not text or len(text.strip()) < self.min_chunk_size:
            return []
        
        chunks = []
        
        # Split into paragraphs first
        paragraphs = self._split_into_paragraphs(text)
        
        current_chunk = ""
        chunk_index = start_index
        
        for para in paragraphs:
            # Check if adding paragraph exceeds chunk size
            potential_size = len(current_chunk) + len(para)
            
            if potential_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_obj = self._create_chunk(
                    text=current_chunk,
                    chunk_index=chunk_index,
                    page_start=page_start,
                    page_end=page_end,
                    document_id=document_id
                )
                if chunk_obj:
                    chunks.append(chunk_obj)
                    chunk_index += 1
                
                # Start new chunk with overlap
                current_chunk = self._get_overlap(current_chunk) + "\n\n" + para
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Add final chunk
        if current_chunk and len(current_chunk.strip()) >= self.min_chunk_size:
            chunk_obj = self._create_chunk(
                text=current_chunk,
                chunk_index=chunk_index,
                page_start=page_start,
                page_end=page_end,
                document_id=document_id
            )
            if chunk_obj:
                chunks.append(chunk_obj)
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs
        
        Args:
            text: Text to split
            
        Returns:
            List of paragraphs
        """
        # Split on double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Clean and filter
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Force-split paragraphs that are too large (e.g. table of contents)
        max_paragraph_size = self.chunk_size * 2  # 2x chunk_size max
        split_paragraphs = []
        
        for para in paragraphs:
            if len(para) > max_paragraph_size:
                # Split by single newlines instead
                lines = para.split('\n')
                current = ""
                for line in lines:
                    if len(current) + len(line) > max_paragraph_size:
                        if current:
                            split_paragraphs.append(current)
                        current = line
                    else:
                        current = current + "\n" + line if current else line
                if current:
                    split_paragraphs.append(current)
            else:
                split_paragraphs.append(para)
        
        # Merge very short paragraphs with next one
        merged = []
        buffer = ""
        
        for para in split_paragraphs:
            if len(buffer) > 0 and len(buffer) < 100:
                # Merge with buffer
                buffer = buffer + "\n\n" + para
            else:
                if buffer:
                    merged.append(buffer)
                buffer = para
        
        if buffer:
            merged.append(buffer)
        
        return merged
    
    def _get_overlap(self, text: str) -> str:
        """
        Get overlap text from end of chunk
        
        Args:
            text: Full chunk text
            
        Returns:
            Overlap text
        """
        if len(text) <= self.overlap_size:
            return text
        
        # Take last N characters
        overlap = text[-self.overlap_size:]
        
        # Try to start at sentence boundary
        sentence_start = overlap.find('. ')
        if sentence_start > 0:
            overlap = overlap[sentence_start + 2:]
        
        return overlap.strip()
    
    def _create_chunk(
        self,
        text: str,
        chunk_index: int,
        page_start: int,
        page_end: int,
        document_id: UUID
    ) -> TextChunk:
        """
        Create TextChunk object with metadata
        
        Args:
            text: Chunk text
            chunk_index: Chunk index
            page_start: Starting page
            page_end: Ending page
            document_id: Document UUID
            
        Returns:
            TextChunk object or None if invalid
        """
        text = text.strip()
        
        # Validate minimum size
        if len(text) < self.min_chunk_size:
            return None
        
        # Generate fingerprint
        fingerprint = self._generate_fingerprint(text)
        
        # Detect chunk type
        chunk_type = self._detect_chunk_type(text)
        
        # Create metadata
        metadata = {
            'char_count': len(text),
            'word_count': len(text.split()),
            'has_error_codes': self._contains_error_codes(text),
            'chunk_type': chunk_type
        }
        
        try:
            return TextChunk(
                document_id=document_id,
                text=text,
                chunk_index=chunk_index,
                page_start=page_start,
                page_end=page_end,
                chunk_type=chunk_type,
                metadata=metadata,
                fingerprint=fingerprint
            )
        except Exception as e:
            self.logger.error(f"Failed to create chunk: {e}")
            return None
    
    def _generate_fingerprint(self, text: str) -> str:
        """
        Generate content fingerprint for deduplication
        
        Args:
            text: Text to fingerprint
            
        Returns:
            SHA256 hash (first 16 chars)
        """
        # Normalize text (remove whitespace variations)
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        
        # Hash
        hash_obj = hashlib.sha256(normalized.encode('utf-8'))
        return hash_obj.hexdigest()[:16]
    
    def _detect_chunk_type(self, text: str) -> str:
        """
        Detect what type of content this chunk contains
        
        Returns:
            One of: error_code_section, troubleshooting, procedure, specification, general
        """
        text_lower = text.lower()
        
        # Error code section
        if re.search(r'\d{2}\.\d{2}\.\d{2}', text):
            if any(kw in text_lower for kw in ['error', 'code', 'message']):
                return "error_code_section"
        
        # Troubleshooting
        if any(kw in text_lower for kw in ['troubleshoot', 'problem', 'symptom', 'cause', 'solution']):
            return "troubleshooting"
        
        # Procedure/steps
        if re.search(r'\b\d+\.\s+', text):  # Numbered list
            return "procedure"
        
        # Specifications
        if any(kw in text_lower for kw in ['specification', 'dimension', 'weight', 'capacity']):
            return "specification"
        
        return "general"
    
    def _contains_error_codes(self, text: str) -> bool:
        """
        Check if text contains error codes
        
        Args:
            text: Text to check
            
        Returns:
            True if error codes found
        """
        return bool(re.search(r'\d{2}\.\d{2}(\.\d{2})?', text))
    
    def deduplicate_chunks(
        self,
        chunks: List[TextChunk]
    ) -> List[TextChunk]:
        """
        Remove duplicate chunks based on fingerprint
        
        Args:
            chunks: List of chunks
            
        Returns:
            Deduplicated list
        """
        seen_fingerprints = set()
        unique_chunks = []
        duplicates = 0
        
        for chunk in chunks:
            if chunk.fingerprint not in seen_fingerprints:
                seen_fingerprints.add(chunk.fingerprint)
                unique_chunks.append(chunk)
            else:
                duplicates += 1
        
        if duplicates > 0:
            self.logger.info(f"Removed {duplicates} duplicate chunks")
        
        return unique_chunks


# Convenience function
def chunk_document_text(
    page_texts: Dict[int, str],
    document_id: UUID,
    chunk_size: int = 1000,
    overlap: int = 100
) -> List[TextChunk]:
    """
    Convenience function to chunk document
    
    Args:
        page_texts: Dictionary {page_number: text}
        document_id: Document UUID
        chunk_size: Target chunk size
        overlap: Overlap size
        
    Returns:
        List of TextChunk objects
    """
    chunker = SmartChunker(
        chunk_size=chunk_size,
        overlap_size=overlap
    )
    return chunker.chunk_document(page_texts, document_id)
