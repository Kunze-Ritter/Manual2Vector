"""
Smart Text Chunking Module

Splits text into chunks with overlap, preserving context.
Respects paragraph boundaries and error code sections.
"""

import re
import hashlib
from typing import List, Dict, Tuple
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
        min_chunk_size: int = 30  # Reduced to preserve small but valuable chunks
    ):
        """
        Initialize chunker
        
        Args:
            chunk_size: Target chunk size in characters (default: 1000)
            overlap_size: Overlap between chunks (default: 100)
            min_chunk_size: Minimum chunk size after header cleaning (default: 30)
                           Reduced from 50 to preserve short but valuable content
                           like error codes, part numbers, or brief instructions
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
        
        # Summary statistics
        chunk_types = {}
        chunks_with_headers = 0
        for chunk in all_chunks:
            chunk_type = chunk.metadata.get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            if chunk.metadata.get('page_header'):
                chunks_with_headers += 1
        
        self.logger.success(
            f"✅ Created {len(all_chunks)} chunks from {len(sorted_pages)} pages"
        )
        if chunk_types:
            types_str = ', '.join([f"{k}: {v}" for k, v in sorted(chunk_types.items())])
            self.logger.info(f"   Types: {types_str}")
        if chunks_with_headers > 0:
            self.logger.info(f"   Headers preserved: {chunks_with_headers}/{len(all_chunks)} chunks")
        
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
        
        # Clean headers and extract metadata
        cleaned_text, header_metadata = self._clean_headers(text)
        
        # Validate minimum size AFTER cleaning (headers might have been removed)
        if len(cleaned_text.strip()) < self.min_chunk_size:
            self.logger.debug(f"⏭️  Skipped chunk (too short after header cleaning): {len(cleaned_text)} chars (min: {self.min_chunk_size})")
            return None
        
        # Generate fingerprint
        fingerprint = self._generate_fingerprint(cleaned_text)
        
        # Detect chunk type
        chunk_type = self._detect_chunk_type(cleaned_text)
        
        # Create metadata
        metadata = {
            'char_count': len(cleaned_text),
            'word_count': len(cleaned_text.split()),
            'has_error_codes': self._contains_error_codes(cleaned_text),
            'chunk_type': chunk_type
        }
        
        # Add header metadata if found
        if header_metadata:
            metadata.update(header_metadata)
            self.logger.debug(f"📋 Added header metadata to chunk: {list(header_metadata.keys())}")
        
        try:
            return TextChunk(
                document_id=document_id,
                text=cleaned_text,
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
    
    def _clean_headers(self, text: str) -> Tuple[str, dict]:
        """
        Remove repetitive PDF headers and extract as metadata
        
        Args:
            text: Original chunk text
            
        Returns:
            Tuple of (cleaned_text, header_metadata)
        """
        header_metadata = {}
        cleaned_text = text
        
        # Common header patterns (first 1-3 lines)
        lines = text.split('\n')
        if len(lines) < 2:
            return text, {}
        
        header_lines = []
        content_start_idx = 0
        
        # Check first few lines for header patterns
        for i, line in enumerate(lines[:5]):  # Check first 5 lines max
            line_clean = line.strip()
            
            # Stop if we hit actual content (longer lines, paragraphs)
            if i > 0 and len(line_clean) > 80:
                break
            
            # Detect product model patterns from all major manufacturers
            # Konica Minolta: AccurioPress C4080, bizhub C450i, bizhub PRESS
            # HP: LaserJet M607, OfficeJet Pro 9025, DesignJet T730 (Plotter)
            # Lexmark: CX920, MX910, CS820, MS812, XC9235
            # UTAX: 5006ci, 4006ci, TA5006ci
            # Kyocera: TASKalfa 5053ci, ECOSYS M8130cidn, FS-C5150DN, CS-2552ci
            # Canon: imageRUNNER C5550i, imagePROGRAF PRO-4100 (Plotter)
            # Xerox: VersaLink C7020, AltaLink C8035, WorkCentre 7835
            # Brother: MFC-L8900CDW, HL-L8360CDW, DCP-L8410CDN
            # Fujifilm: ApeosPort-VII C4473, DocuPrint CP505, Apeos C6580, Revoria Press
            # Riso: ComColor GD7330, ORPHIS X9050
            manufacturer_patterns = (
                # Konica Minolta
                r'AccurioPress|AccurioPrint|bizhub PRESS|bizhub|Magicolor'
                # HP - Office & Plotter
                r'|LaserJet|OfficeJet|Color LaserJet|PageWide|DeskJet|ScanJet'
                r'|DesignJet|PageWide XL'  # HP Plotter
                r'|colorlj[A-Z][0-9]+|Color LaserJet [A-Z][0-9]+'  # HP model codes (colorljM455, etc.)
                # Lexmark
                r'|Lexmark\s+[A-Z]{1,2}\d{3,4}|CX\d{3,4}|MX\d{3,4}|CS\d{3,4}|MS\d{3,4}|XC\d{3,4}|MC\d{3,4}'
                # UTAX / Triumph-Adler
                r'|UTAX|Triumph-Adler|TA\s*\d{4}ci'
                # Kyocera - Extended
                r'|TASKalfa|ECOSYS|Kyocera|FS-C\d{4}|FS-\d{4}|CS-\d{4}ci|MA\d{4}|PA\d{4}'
                # Canon - Office & Plotter
                r'|imageRUNNER|imageCLASS|imagePRESS|imageWARE'
                r'|imagePROGRAF|iPF\d{3,4}'  # Canon Plotter
                # Xerox
                r'|VersaLink|AltaLink|WorkCentre|ColorQube|Phaser|PrimeLink'
                # Brother
                r'|MFC-[A-Z]\d{4,5}|HL-[A-Z]\d{4,5}|DCP-[A-Z]\d{4,5}'
                # Fujifilm (Xerox successor in Asia/Japan)
                r'|ApeosPort|Apeos|DocuPrint|DocuCentre|ApeosPort-VII|Apeos C\d{4}|Revoria'
                # Riso (Digital Duplicators & Production Printers)
                r'|ComColor|ORPHIS|Riso|RZ\d{3,4}|SF\d{3,4}'
            )
            if re.search(manufacturer_patterns, line_clean, re.IGNORECASE):
                header_lines.append(line_clean)
                content_start_idx = i + 1
            # Roman numerals (page numbers in header)
            elif re.match(r'^[ivxlcdm]+$', line_clean, re.IGNORECASE):
                header_lines.append(line_clean)
                content_start_idx = i + 1
            # Document type headers (e.g., "Control Panel Messages Document")
            elif i < 3 and re.search(r'\b(Document|Manual|Guide|Instruction|Service|Technical|CPMD)\b', line_clean, re.IGNORECASE):
                header_lines.append(line_clean)
                content_start_idx = i + 1
            # URLs (support pages, product pages)
            elif i < 5 and re.match(r'^(https?://|www\.)', line_clean):
                header_lines.append(line_clean)
                content_start_idx = i + 1
            # Very short lines that look like headers
            elif i < 2 and len(line_clean) < 60 and line_clean and not line_clean[0].islower():
                header_lines.append(line_clean)
                content_start_idx = i + 1
            else:
                # Stop looking
                break
        
        # Extract header info
        if header_lines:
            full_header = '\n'.join(header_lines)
            header_metadata['page_header'] = full_header
            header_metadata['header_removed'] = True
            
            # Extract product models
            products = []
            for line in header_lines:
                # Find model patterns like C4080, C4070, C84hc, etc.
                models = re.findall(r'[A-Z]\d{4}[a-z]*(?:/[A-Z]\d{4}[a-z]*)*', line)
                products.extend(models)
                
                # Extract HP model codes from URLs (colorljM455, colorljE47528MFP)
                url_models = re.findall(r'colorlj([A-Z]\d+[A-Z]*)', line, re.IGNORECASE)
                products.extend(url_models)
            
            if products:
                header_metadata['header_products'] = list(set(products))  # Unique
            
            # Remove header from text
            cleaned_text = '\n'.join(lines[content_start_idx:]).strip()
            
            self.logger.debug(f"🎯 Found header: '{full_header[:50]}...' | Products: {products}")
        
        return cleaned_text, header_metadata
    
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
