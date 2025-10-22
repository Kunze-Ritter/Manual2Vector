"""
Document Type Detector
Automatically detects document type based on content and metadata
"""

from typing import Optional, Dict, Any
import re
from datetime import datetime


class DocumentTypeDetector:
    """Detect document type from PDF metadata and content"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def detect(
        self,
        pdf_metadata: Dict[str, Any],
        content_stats: Dict[str, Any],
        manufacturer: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Detect document type and version
        
        Args:
            pdf_metadata: PDF metadata (title, author, creation_date, etc.)
            content_stats: Content statistics (error_codes_count, parts_count, etc.)
            manufacturer: Detected manufacturer name
            
        Returns:
            (document_type, version) tuple
        """
        title = pdf_metadata.get('title', '').lower()
        filename = pdf_metadata.get('filename', '').lower()
        creation_date = pdf_metadata.get('creation_date', '')
        
        error_codes_count = content_stats.get('total_error_codes', 0)
        parts_count = content_stats.get('parts_count', 0)
        
        document_type = self._detect_type(
            title=title,
            filename=filename,
            error_codes_count=error_codes_count,
            parts_count=parts_count
        )
        
        version = self._detect_version(
            title=title,
            filename=filename,
            creation_date=creation_date,
            document_type=document_type,
            manufacturer=manufacturer
        )
        
        return document_type, version
    
    def _detect_type(
        self,
        title: str,
        filename: str,
        error_codes_count: int,
        parts_count: int
    ) -> str:
        """
        Detect document type
        
        Priority:
        1. Parts Catalog (dedicated parts list, no error codes)
        2. Service Manual (error codes + procedures)
        3. User Manual (no error codes, no parts)
        4. Installation Guide
        """
        combined = f"{title} {filename}"
        
        # 1. Parts Catalog Detection
        has_parts_keyword = any(kw in combined for kw in [
            'parts guide',
            'parts catalog',
            'parts list',
            'parts manual',
            'ersatzteile',  # German
            'pièces',       # French
        ])
        
        if has_parts_keyword and error_codes_count == 0:
            return 'parts_catalog'
        
        # 2. Service Manual Detection
        has_service_keyword = any(kw in combined for kw in [
            'service manual',
            'service guide',
            'field service',
            'technician guide',
            'repair manual',
            'wartungsanleitung',  # German
        ])
        
        if has_service_keyword or error_codes_count > 0:
            return 'service_manual'
        
        # 3. User Manual Detection
        has_user_keyword = any(kw in combined for kw in [
            'user guide',
            'user manual',
            'operator guide',
            'bedienungsanleitung',  # German
            'manuel utilisateur',   # French
        ])
        
        if has_user_keyword:
            return 'user_manual'
        
        # 4. Installation Guide Detection
        has_install_keyword = any(kw in combined for kw in [
            'installation',
            'setup guide',
            'quick start',
        ])
        
        if has_install_keyword:
            return 'installation_guide'
        
        # Default: Service Manual (safest assumption)
        return 'service_manual'
    
    def _detect_version(
        self,
        title: str,
        filename: str,
        creation_date: str,
        document_type: str,
        manufacturer: Optional[str] = None
    ) -> Optional[str]:
        """
        Detect document version
        
        Strategies:
        1. For Konica Minolta Parts Catalogs: Use creation date (Month Year)
        2. Extract from title/filename (e.g., "v1.0", "Rev 2", "Edition 3")
        3. Extract document code (e.g., "A93E", "ACET011")
        """
        # Strategy 1: Konica Minolta Parts Catalog → Month Year
        if (document_type == 'parts_catalog' and 
            manufacturer and 'konica' in manufacturer.lower()):
            
            version = self._extract_date_version(creation_date)
            if version:
                return version
        
        # Strategy 2: Version patterns in title/filename
        combined = f"{title} {filename}"
        
        # Common version patterns
        patterns = [
            r'v(\d+\.?\d*)',           # v1.0, v2
            r'version\s*(\d+\.?\d*)',  # version 1.0
            r'rev\.?\s*([A-Z0-9]+)',   # Rev A, Rev.2
            r'edition\s*(\d+)',        # Edition 3
            r'ausgabe\s*(\d+)',        # German: Ausgabe 2
        ]
        
        for pattern in patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Strategy 3: Document code from filename
        # e.g., "A93E.pdf" → "A93E", "ACET011.pdf" → "ACET011"
        doc_code_match = re.match(r'^([A-Z]{1,2}\d{2,4}[A-Z]?)', filename.upper())
        if doc_code_match:
            return doc_code_match.group(1)
        
        return None
    
    def _extract_date_version(self, creation_date: str) -> Optional[str]:
        """
        Extract Month Year from PDF creation date
        
        Format: D:20250808064126Z → "August 2025"
        """
        if not creation_date:
            return None
        
        # Parse PDF date format: D:YYYYMMDDHHmmSS
        match = re.match(r'D:(\d{4})(\d{2})', creation_date)
        if not match:
            return None
        
        year = match.group(1)
        month_num = int(match.group(2))
        
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        if 1 <= month_num <= 12:
            month_name = months[month_num - 1]
            return f"{month_name} {year}"
        
        return None
