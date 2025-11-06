"""
Classification Processor - Classify documents by manufacturer and type

Stage 4 of the processing pipeline.

Detects manufacturer and document type using AI and pattern matching.
"""

import re
from typing import Any, Dict, Optional
from pathlib import Path

from core.base_processor import BaseProcessor, Stage
from .document_type_detector import DocumentTypeDetector
from utils.manufacturer_normalizer import normalize_manufacturer


class ClassificationProcessor(BaseProcessor):
    """
    Stage 4: Classification Processor
    
    Classifies documents by manufacturer and document type.
    Uses AI for intelligent classification and pattern matching for validation.
    """
    
    def __init__(self, database_service=None, ai_service=None, features_service=None):
        """
        Initialize classification processor
        
        Args:
            database_service: Database service instance
            ai_service: AI service instance
            features_service: Features service instance
        """
        super().__init__(name="classification_processor")
        self.stage = Stage.CLASSIFICATION
        self.database_service = database_service
        self.ai_service = ai_service
        self.features_service = features_service
        
        # Initialize document type detector
        self.type_detector = DocumentTypeDetector(debug=False)
        
        # Known manufacturers for pattern matching
        self.known_manufacturers = [
            'HP', 'Canon', 'Epson', 'Brother', 'Lexmark', 'Ricoh',
            'Konica Minolta', 'Xerox', 'Samsung', 'Kyocera', 'Sharp',
            'Oki', 'Dell', 'Toshiba', 'Panasonic', 'Develop'
        ]
        
        self.logger.info("ClassificationProcessor initialized")
    
    async def process(self, context) -> Any:
        """
        Process classification
        
        Args:
            context: Processing context with file_path and document_id
            
        Returns:
            Processing result with manufacturer and document_type
        """
        with self.logger_context(
            document_id=getattr(context, "document_id", None),
            stage=self.stage
        ) as adapter:
            try:
                file_path = Path(context.file_path)

                doc_metadata = await self._get_document_metadata(context.document_id)

                manufacturer = await self._detect_manufacturer(file_path, doc_metadata, context, adapter)

                if not manufacturer:
                    adapter.warning("Could not detect manufacturer")
                    manufacturer = "Unknown"

                document_type, version = await self._detect_document_type(
                    file_path, doc_metadata, manufacturer, context, adapter
                )

                if self.database_service:
                    await self._update_document_classification(
                        context.document_id,
                        manufacturer,
                        document_type,
                        version
                    )

                self.logger.success(f"✅ Classification: {manufacturer} - {document_type}")

                return self._create_result(
                    success=True,
                    message=f"Classification completed: {manufacturer} - {document_type}",
                    data={
                        'manufacturer': manufacturer,
                        'document_type': document_type,
                        'version': version
                    }
                )

            except Exception as e:
                adapter.error("Classification failed: %s", e)
                self.logger.error(f"Classification failed: {e}")
                return self._create_result(
                    success=False,
                    message=f"Classification error: {str(e)}",
                    data={}
                )
    
    async def _get_document_metadata(self, document_id: str) -> Dict:
        """Get document metadata from database"""
        if not self.database_service:
            return {}
        
        try:
            if hasattr(self.database_service, 'get_document'):
                doc = await self.database_service.get_document(document_id)
                if doc:
                    return {
                        'filename': getattr(doc, 'filename', ''),
                        'title': getattr(doc, 'title', ''),
                        'file_hash': getattr(doc, 'file_hash', '')
                    }
            elif hasattr(self.database_service, 'client'):
                result = self.database_service.client.table('documents').select('*').eq('id', document_id).execute()
                if result.data:
                    return result.data[0]
        except Exception as e:
            self.logger.warning(f"Could not get document metadata: {e}")
        
        return {}
    
    async def _detect_manufacturer(
        self,
        file_path: Path,
        doc_metadata: Dict,
        context,
        adapter
    ) -> Optional[str]:
        """
        Detect manufacturer from filename, content, and AI
        
        Priority:
        1. Filename patterns (HP, Canon, etc.)
        2. Content analysis (first few pages)
        3. AI classification
        """
        filename = file_path.name.lower()
        
        # 1. Check filename for manufacturer patterns
        for manufacturer in self.known_manufacturers:
            if manufacturer.lower() in filename:
                normalized = normalize_manufacturer(manufacturer)
                adapter.info("Manufacturer detected from filename: %s", normalized)
                return normalized
        
        # 2. Check document title
        title = doc_metadata.get('title', '').lower()
        for manufacturer in self.known_manufacturers:
            if manufacturer.lower() in title:
                normalized = normalize_manufacturer(manufacturer)
                adapter.info("Manufacturer detected from title: %s", normalized)
                return normalized
        
        # 3. Use AI to detect from content (if available)
        if self.ai_service and self.features_service:
            try:
                # Get first few chunks for analysis
                chunks = await self._get_document_chunks(context.document_id, limit=5)
                if chunks:
                    content_sample = "\n".join([chunk.get('content', '') for chunk in chunks[:3]])
                    
                    # Use AI to detect manufacturer
                    manufacturer = await self._ai_detect_manufacturer(content_sample)
                    if manufacturer:
                        adapter.info("Manufacturer detected by AI: %s", manufacturer)
                        return manufacturer
            except Exception as e:
                adapter.warning("AI manufacturer detection failed: %s", e)
        
        return None
    
    async def _ai_detect_manufacturer(self, content: str) -> Optional[str]:
        """Use AI to detect manufacturer from content"""
        if not self.ai_service or not content:
            return None
        
        try:
            prompt = f"""Analyze this technical document excerpt and identify the manufacturer.
Look for brand names, model numbers, and company references.

Content:
{content[:1000]}

Respond with ONLY the manufacturer name (e.g., "HP", "Canon", "Konica Minolta").
If uncertain, respond with "Unknown"."""

            response = await self.ai_service.generate(prompt, max_tokens=50)
            
            if response and response.strip():
                manufacturer = response.strip()
                # Normalize the response
                normalized = normalize_manufacturer(manufacturer)
                if normalized and normalized != "Unknown":
                    return normalized
        except Exception as e:
            self.logger.warning(f"AI manufacturer detection error: {e}")
        
        return None
    
    async def _detect_document_type(
        self,
        file_path: Path,
        doc_metadata: Dict,
        manufacturer: str,
        context,
        adapter
    ) -> tuple[str, str]:
        """Detect document type and version"""
        
        # Get content statistics
        content_stats = await self._get_content_statistics(context.document_id)
        
        # Use document type detector
        pdf_metadata = {
            'title': doc_metadata.get('title', ''),
            'filename': file_path.name,
            'creation_date': doc_metadata.get('created_at', '')
        }
        
        document_type, version = self.type_detector.detect(
            pdf_metadata=pdf_metadata,
            content_stats=content_stats,
            manufacturer=manufacturer
        )
        
        adapter.info("Document type detected: %s", document_type)
        
        return document_type, version
    
    async def _get_content_statistics(self, document_id: str) -> Dict:
        """Get content statistics for document"""
        stats = {
            'total_error_codes': 0,
            'parts_count': 0
        }
        
        if not self.database_service:
            return stats
        
        try:
            # Count error codes
            if hasattr(self.database_service, 'client'):
                error_codes = self.database_service.client.table('error_codes').select('id').eq('document_id', document_id).execute()
                stats['total_error_codes'] = len(error_codes.data) if error_codes.data else 0
                
                # Count parts
                parts = self.database_service.client.table('parts_catalog').select('id').eq('document_id', document_id).execute()
                stats['parts_count'] = len(parts.data) if parts.data else 0
        except Exception as e:
            self.logger.warning(f"Could not get content statistics: {e}")
        
        return stats
    
    async def _get_document_chunks(self, document_id: str, limit: int = 5) -> list:
        """Get first N chunks of document"""
        if not self.database_service or not hasattr(self.database_service, 'client'):
            return []
        
        try:
            result = self.database_service.client.table('chunks').select('content').eq('document_id', document_id).order('chunk_index').limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            self.logger.warning(f"Could not get chunks: {e}")
            return []
    
    async def _update_document_classification(
        self,
        document_id: str,
        manufacturer: str,
        document_type: str,
        version: str
    ):
        """Update document with classification results"""
        try:
            if hasattr(self.database_service, 'update_document'):
                await self.database_service.update_document(
                    document_id,
                    {
                        'manufacturer': manufacturer,
                        'document_type': document_type,
                        'version': version
                    }
                )
            elif hasattr(self.database_service, 'client'):
                self.database_service.client.table('documents').update({
                    'manufacturer': manufacturer,
                    'document_type': document_type,
                    'version': version
                }).eq('id', document_id).execute()
            
            self.logger.info(f"Updated document classification in database")
        except Exception as e:
            self.logger.error(f"Failed to update document classification: {e}")
    
    def _create_result(self, success: bool, message: str, data: Dict) -> Any:
        """Create a processing result object"""
        class Result:
            def __init__(self, success, message, data):
                self.success = success
                self.message = message
                self.data = data
        
        return Result(success, message, data)
