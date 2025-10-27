"""
PDF Text Extraction Module

Uses PyMuPDF (fitz) as primary extractor.
Fallback to pdfplumber if needed.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from langdetect import detect_langs, DetectorFactory
    from langdetect.lang_detect_exception import LangDetectException

    DetectorFactory.seed = 0  # Ensure deterministic results
    LANGDETECT_AVAILABLE = True
except ImportError:
    detect_langs = None  # type: ignore
    LangDetectException = Exception  # type: ignore
    LANGDETECT_AVAILABLE = False

from .logger import get_logger
from .models import DocumentMetadata
from uuid import UUID
from datetime import datetime


logger = get_logger()


STRUCTURED_CODE_REGEX = re.compile(r"\d{2}\.[0-9A-Za-z]{2,3}\.[0-9A-Za-z]{2}", re.IGNORECASE)


class TextExtractor:
    """Extract text from PDF documents"""
    
    def __init__(self, prefer_engine: str = "pymupdf"):
        """
        Initialize text extractor
        
        Args:
            prefer_engine: Preferred extraction engine ('pymupdf' or 'pdfplumber')
        """
        self.prefer_engine = prefer_engine
        
        if not PYMUPDF_AVAILABLE and not PDFPLUMBER_AVAILABLE:
            raise RuntimeError(
                "No PDF extraction library available! "
                "Install PyMuPDF or pdfplumber"
            )
        
        if prefer_engine == "pymupdf" and not PYMUPDF_AVAILABLE:
            logger.warning("PyMuPDF not available, falling back to pdfplumber")
            self.prefer_engine = "pdfplumber"
        
        if prefer_engine == "pdfplumber" and not PDFPLUMBER_AVAILABLE:
            logger.warning("pdfplumber not available, falling back to PyMuPDF")
            self.prefer_engine = "pymupdf"
    
    def extract_text(
        self,
        pdf_path: Path,
        document_id: UUID
    ) -> Tuple[Dict[int, str], DocumentMetadata, Dict[int, Optional[str]]]:
        """
        Extract text from PDF
        
        Args:
            pdf_path: Path to PDF file
            document_id: Document UUID
            
        Returns:
            Tuple of (page_texts, metadata, structured_texts_by_page)
            - page_texts: {page_number: text_content}
            - metadata: DocumentMetadata object
            - structured_texts_by_page: {page_number: structured_text | None}
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        logger.info(f"Extracting text from: {pdf_path.name}")
        logger.info(f"Using engine: {self.prefer_engine}")
        
        if self.prefer_engine == "pymupdf" and PYMUPDF_AVAILABLE:
            return self._extract_with_pymupdf(pdf_path, document_id)
        elif self.prefer_engine == "pdfplumber" and PDFPLUMBER_AVAILABLE:
            return self._extract_with_pdfplumber(pdf_path, document_id)
        else:
            raise RuntimeError("No extraction engine available")
    
    def _extract_with_pymupdf(
        self,
        pdf_path: Path,
        document_id: UUID
    ) -> Tuple[Dict[int, str], DocumentMetadata, Dict[int, Optional[str]]]:
        """
        Extract using PyMuPDF (faster, better for service manuals)
        
        Returns:
            Tuple of (page_texts, metadata, structured_texts_by_page)
        """
        page_texts = {}
        structured_texts = {}
        
        try:
            doc = fitz.open(pdf_path)
            
            # Extract metadata
            metadata = self._extract_metadata_pymupdf(doc, pdf_path, document_id)
            
            # Extract text from each page
            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    text = page.get_text("text")
                    
                    structured = self._extract_structured_text(page)

                    # Clean up text
                    text = self._clean_text(text)

                    if text.strip():
                        page_texts[page_num + 1] = text  # 1-indexed
                    if structured:
                        structured_texts[page_num + 1] = structured
                
                except Exception as page_error:
                    logger.warning(f"Failed to extract page {page_num + 1}: {page_error}")
                    # Continue with next page
                    continue
            
            doc.close()
            
            logger.success(f"Extracted {len(page_texts)} pages with PyMuPDF")

            return page_texts, metadata, structured_texts
        
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}", exc=e)
            
            # Try fallback if available
            if PDFPLUMBER_AVAILABLE:
                logger.info("Falling back to pdfplumber...")
                return self._extract_with_pdfplumber(pdf_path, document_id)
            else:
                raise
    
    def _extract_with_pdfplumber(
        self,
        pdf_path: Path,
        document_id: UUID
    ) -> Tuple[Dict[int, str], DocumentMetadata, Dict[int, Optional[str]]]:
        """
        Extract using pdfplumber (slower, but good fallback)
        
        Returns:
            Tuple of (page_texts, metadata, structured_texts_by_page)
        """
        page_texts = {}
        structured_texts: Dict[int, Optional[str]] = {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract metadata
                metadata = self._extract_metadata_pdfplumber(pdf, pdf_path, document_id)
                
                # Extract text from each page
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    
                    if text:
                        text = self._clean_text(text)
                        page_texts[page_num] = text
            
            logger.success(f"Extracted {len(page_texts)} pages with pdfplumber")
            return page_texts, metadata, structured_texts
        
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}", exc=e)
            raise
    
    def _extract_metadata_pymupdf(
        self,
        doc: 'fitz.Document',
        pdf_path: Path,
        document_id: UUID
    ) -> DocumentMetadata:
        """Extract metadata using PyMuPDF"""
        pdf_metadata = doc.metadata
        
        # Try to parse creation date
        creation_date = None
        if pdf_metadata.get('creationDate'):
            try:
                # PyMuPDF format: D:20240101120000+00'00'
                date_str = pdf_metadata['creationDate']
                if date_str.startswith('D:'):
                    date_str = date_str[2:16]  # Take YYYYMMDDHHMMSS
                    creation_date = datetime.strptime(date_str, '%Y%m%d%H%M%S')
            except Exception:
                pass
        
        # Determine document type from title or filename
        doc_type = self._classify_document_type(
            title=pdf_metadata.get('title', ''),
            filename=pdf_path.name
        )
        
        language, language_confidence = self._detect_language_from_doc(doc)

        return DocumentMetadata(
            document_id=document_id,
            title=pdf_metadata.get('title') or pdf_path.stem,
            author=pdf_metadata.get('author'),
            creation_date=creation_date,
            page_count=len(doc),
            file_size_bytes=pdf_path.stat().st_size,
            mime_type="application/pdf",
            language=language,
            language_confidence=language_confidence,
            document_type=doc_type
        )
    
    def _extract_metadata_pdfplumber(
        self,
        pdf: 'pdfplumber.PDF',
        pdf_path: Path,
        document_id: UUID
    ) -> DocumentMetadata:
        """Extract metadata using pdfplumber"""
        pdf_metadata = pdf.metadata or {}
        
        # Parse creation date
        creation_date = None
        if pdf_metadata.get('CreationDate'):
            try:
                date_str = pdf_metadata['CreationDate']
                # pdfplumber format varies, try common formats
                for fmt in ['%Y%m%d%H%M%S', '%Y-%m-%d %H:%M:%S']:
                    try:
                        creation_date = datetime.strptime(date_str[:14], fmt)
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        
        doc_type = self._classify_document_type(
            title=pdf_metadata.get('Title', ''),
            filename=pdf_path.name
        )
        
        # Detect language from first few pages
        language, language_confidence = self._detect_language_from_samples(
            self._collect_pdfplumber_samples(pdf)
        )

        return DocumentMetadata(
            document_id=document_id,
            title=pdf_metadata.get('Title') or pdf_path.stem,
            author=pdf_metadata.get('Author'),
            creation_date=creation_date,
            page_count=len(pdf.pages),
            file_size_bytes=pdf_path.stat().st_size,
            mime_type="application/pdf",
            language=language,
            language_confidence=language_confidence,
            document_type=doc_type
        )

    def _collect_pdfplumber_samples(
        self,
        pdf: 'pdfplumber.PDF',
        max_pages: int = 5,
        max_chars: int = 5000
    ) -> List[str]:
        samples: List[str] = []
        total_chars = 0
        for page in pdf.pages[:max_pages]:
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            if not text:
                continue
            samples.append(text)
            total_chars += len(text)
            if total_chars >= max_chars:
                break
        return samples

    def _detect_language_from_doc(
        self,
        doc: 'fitz.Document',
        max_pages: int = 5,
        max_chars: int = 5000
    ) -> Tuple[str, Optional[float]]:
        if not doc:
            return "unknown", None

        samples: List[str] = []
        total_chars = 0
        page_count = min(len(doc), max_pages)

        for page_index in range(page_count):
            try:
                page_text = doc[page_index].get_text("text") or ""
            except Exception:
                page_text = ""

            if not page_text:
                continue

            samples.append(page_text)
            total_chars += len(page_text)

            if total_chars >= max_chars:
                break

        return self._detect_language_from_samples(samples)

    def _detect_language_from_samples(
        self,
        samples: List[str],
        min_chars: int = 20,
        max_chars: int = 5000,
        min_confidence: float = 0.6
    ) -> Tuple[str, Optional[float]]:
        if not LANGDETECT_AVAILABLE or not samples:
            return "unknown", None

        combined = "\n".join(s.strip() for s in samples if s and s.strip()).strip()
        if not combined:
            return "unknown", None

        if len(combined) > max_chars:
            combined = combined[:max_chars]

        if len(combined) < min_chars:
            return "unknown", None

        try:
            detections = detect_langs(combined)
        except LangDetectException:
            return "unknown", None

        if not detections:
            return "unknown", None

        best = max(detections, key=lambda result: result.prob)
        language_code = (best.lang or "unknown").lower()
        confidence = float(best.prob)

        if confidence < min_confidence:
            return "unknown", confidence

        return language_code, confidence

    def _extract_structured_text(self, page: 'fitz.Page') -> Optional[str]:
        """Extract error-code-friendly text using PyMuPDF raw dict layout."""
        try:
            raw = page.get_text("rawdict")
        except Exception:
            return None

        if not raw:
            return None

        structured_lines: List[str] = []
        seen = set()

        for block in raw.get("blocks", []):
            if block.get("type") != 0:  # text blocks only
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue

                joined = "".join(span.get("text", "") for span in spans)
                if not joined:
                    continue

                # Remove all whitespace characters and collapse leader dots for reliable matching
                compact = re.sub(r"\s+", "", joined)
                compact = re.sub(r"\.{2,}", ".", compact)
                compact = compact.replace("·", ".")  # Normalize mid-dots often used in tables

                if STRUCTURED_CODE_REGEX.search(compact):
                    normalized = re.sub(r"\.{2,}", " ", joined)
                    normalized = re.sub(r"\s+", " ", normalized).strip()
                    if normalized and normalized not in seen:
                        seen.add(normalized)
                        structured_lines.append(normalized)

        if not structured_lines:
            return None

        return "\n".join(structured_lines)
    
    def _classify_document_type(self, title: str, filename: str) -> str:
        """
        Classify document type from title/filename
        
        Returns one of: service_manual, parts_catalog, user_guide, troubleshooting
        """
        combined = f"{title} {filename}".lower()
        
        if any(kw in combined for kw in ['service', 'repair', 'maintenance']):
            return "service_manual"
        elif any(kw in combined for kw in ['parts', 'catalog', 'spare']):
            return "parts_catalog"
        elif any(kw in combined for kw in ['user', 'guide', 'manual', 'instruction']):
            return "user_guide"
        elif any(kw in combined for kw in ['troubleshoot', 'problem', 'error', 'diagnostic']):
            return "troubleshooting"
        else:
            # Default to service_manual for now
            return "service_manual"
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text
        
        - Remove excessive whitespace
        - Fix common OCR errors
        - Normalize line breaks
        """
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove excessive blank lines (more than 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove spaces at line start/end
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text
    
    def extract_first_page_text(self, pdf_path: Path) -> str:
        """
        Extract text from first page only (for quick metadata extraction)
        
        Args:
            pdf_path: Path to PDF
            
        Returns:
            Text from first page
        """
        if self.prefer_engine == "pymupdf" and PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(pdf_path)
                if len(doc) > 0:
                    text = doc[0].get_text("text")
                    doc.close()
                    return self._clean_text(text)
            except Exception as e:
                logger.error(f"Failed to extract first page: {e}")
        
        return ""


# Convenience function
def extract_text_from_pdf(
    pdf_path: Path,
    document_id: UUID,
    engine: str = "pymupdf"
) -> Tuple[Dict[int, str], DocumentMetadata, Dict[int, Optional[str]]]:
    """
    Convenience function to extract text from PDF
    
    Args:
        pdf_path: Path to PDF file
        document_id: Document UUID
        engine: Extraction engine ('pymupdf' or 'pdfplumber')
        
    Returns:
        Tuple of (page_texts, metadata, structured_texts_by_page)
        - page_texts: {page_number: text_content}
        - metadata: DocumentMetadata object
        - structured_texts_by_page: {page_number: structured_text | None}
    """
    extractor = TextExtractor(prefer_engine=engine)
    return extractor.extract_text(pdf_path, document_id)
