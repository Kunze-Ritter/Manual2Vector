"""
Metadata Processor (AI) - Extract metadata using AI

Stage 7 of the processing pipeline.

Extracts error codes, version numbers, and other metadata from documents.
Uses pattern matching and AI for intelligent extraction.
"""

from typing import Any, Dict, List
from pathlib import Path

from backend.core.base_processor import BaseProcessor, Stage
from .error_code_extractor import ErrorCodeExtractor
from .version_extractor import VersionExtractor


class MetadataProcessorAI(BaseProcessor):
    """
    Stage 7: Metadata Processor (AI)
    
    Extracts metadata like error codes and version numbers.
    Uses pattern matching for error codes and AI for complex metadata.
    """
    
    def __init__(self, database_service=None, ai_service=None, config_service=None):
        """
        Initialize metadata processor
        
        Args:
            database_service: Database service instance
            ai_service: AI service instance
            config_service: Config service instance
        """
        super().__init__(name="metadata_processor_ai")
        self.stage = Stage.METADATA_EXTRACTION
        self.database_service = database_service
        self.ai_service = ai_service
        self.config_service = config_service
        
        # Initialize extractors
        self.error_code_extractor = ErrorCodeExtractor()
        self.version_extractor = VersionExtractor()
        
        self.logger.info("MetadataProcessorAI initialized")
    
    async def process(self, context) -> Any:
        """
        Process metadata extraction
        
        Args:
            context: Processing context with file_path and document_id
            
        Returns:
            Processing result with error_codes_extracted count
        """
        with self.logger_context(
            document_id=getattr(context, "document_id", None),
            stage=self.stage
        ) as adapter:
            try:
                file_path = Path(context.file_path)

                manufacturer = await self._get_document_manufacturer(context.document_id)

                if not manufacturer or manufacturer == "Unknown":
                    adapter.warning("No manufacturer found - using AUTO detection")
                    manufacturer = "AUTO"

                adapter.info("Extracting error codes (manufacturer: %s)...", manufacturer)
                error_codes = self.error_code_extractor.extract(
                    pdf_path=file_path,
                    manufacturer=manufacturer
                )

                if error_codes:
                    self.logger.success(f"✅ Extracted {len(error_codes)} error codes")

                    if self.database_service:
                        saved_count = await self._save_error_codes(
                            error_codes,
                            context.document_id,
                            manufacturer,
                            adapter
                        )
                        self.logger.success(f"✅ Saved {saved_count} error codes to database")
                else:
                    adapter.info("No error codes found")

                adapter.info("Extracting version information...")
                version_info = self.version_extractor.extract(file_path)

                if version_info:
                    self.logger.success(f"✅ Extracted version: {version_info}")

                    if self.database_service:
                        await self._update_document_version(
                            context.document_id,
                            version_info,
                            adapter
                        )

                return self._create_result(
                    success=True,
                    message=f"Metadata extraction completed: {len(error_codes)} error codes",
                    data={
                        'error_codes_extracted': len(error_codes),
                        'version_info': version_info
                    }
                )

            except Exception as e:
                adapter.error("Metadata extraction failed: %s", e)
                self.logger.error(f"Metadata extraction failed: {e}")
                return self._create_result(
                    success=False,
                    message=f"Metadata extraction error: {str(e)}",
                    data={}
                )
    
    async def _get_document_manufacturer(self, document_id: str) -> str:
        """Get manufacturer from document"""
        if not self.database_service:
            return "AUTO"
        
        try:
            if hasattr(self.database_service, 'get_document'):
                doc = await self.database_service.get_document(document_id)
                if doc:
                    return getattr(doc, 'manufacturer', 'AUTO')
            elif hasattr(self.database_service, 'client'):
                result = self.database_service.client.table('documents').select('manufacturer').eq('id', document_id).execute()
                if result.data:
                    return result.data[0].get('manufacturer', 'AUTO')
        except Exception as e:
            self.logger.warning(f"Could not get manufacturer: {e}")
        
        return "AUTO"
    
    async def _save_error_codes(
        self,
        error_codes: List,
        document_id: str,
        manufacturer: str,
        adapter
    ) -> int:
        """Save error codes to database"""
        if not self.database_service:
            return 0
        
        saved_count = 0
        
        for error_code in error_codes:
            try:
                # Prepare error code data
                error_data = {
                    'document_id': str(document_id),
                    'manufacturer': manufacturer,
                    'code': error_code.code,
                    'description': error_code.description,
                    'solution': error_code.solution,
                    'page_number': error_code.page_number,
                    'severity': getattr(error_code, 'severity', None),
                    'category': getattr(error_code, 'category', None)
                }
                
                # Insert into database
                if hasattr(self.database_service, 'client'):
                    result = self.database_service.client.table('error_codes').insert(error_data).execute()
                    if result.data:
                        saved_count += 1
                        
            except Exception as e:
                adapter.warning("Failed to save error code %s: %s", error_code.code, e)
        
        return saved_count
    
    async def _update_document_version(self, document_id: str, version_info: str, adapter):
        """Update document with version information"""
        if not self.database_service:
            return
        
        try:
            if hasattr(self.database_service, 'update_document'):
                await self.database_service.update_document(
                    document_id,
                    {'version': version_info}
                )
            elif hasattr(self.database_service, 'client'):
                self.database_service.client.table('documents').update({
                    'version': version_info
                }).eq('id', document_id).execute()
            
            adapter.info("Updated document version: %s", version_info)
        except Exception as e:
            adapter.warning("Failed to update document version: %s", e)
    
    def _create_result(self, success: bool, message: str, data: Dict) -> Any:
        """Create a processing result object"""
        class Result:
            def __init__(self, success, message, data):
                self.success = success
                self.message = message
                self.data = data
        
        return Result(success, message, data)
