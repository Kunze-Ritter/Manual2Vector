"""
Metadata Processor (AI) - Extract metadata using AI

Stage 7 of the processing pipeline.

Extracts error codes, version numbers, and other metadata from documents.
Uses pattern matching and AI for intelligent extraction.
"""

from typing import Any, Dict, List
from pathlib import Path

from backend.core.base_processor import BaseProcessor, Stage, ProcessingError
from backend.core.data_models import ErrorCodeModel
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
                # Use extract_from_text method instead of missing extract method
                error_codes = self.error_code_extractor.extract_from_text(
                    text="",  # Will be overridden by PDF processing
                    page_number=1
                )
                # Fallback: try extract if available
                if hasattr(self.error_code_extractor, 'extract'):
                    error_codes = self.error_code_extractor.extract(
                        pdf_path=file_path,
                        manufacturer=manufacturer
                    )
                else:
                    adapter.warning("ErrorCodeExtractor.extract method not available - skipping error code extraction")

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

                version_info = None
                version_text = None
                page_texts = getattr(context, "page_texts", None)
                if isinstance(page_texts, dict) and page_texts:
                    first_pages = sorted(page_texts.keys())[:5]
                    version_text = "\n\n".join(
                        [page_texts.get(p, "") for p in first_pages if page_texts.get(p)]
                    ).strip()

                if version_text:
                    best_version = self.version_extractor.extract_best_version(
                        version_text,
                        manufacturer=None if manufacturer == "AUTO" else manufacturer,
                    )
                    version_info = best_version.version_string if best_version else None
                else:
                    adapter.warning("No page text available - skipping version extraction")

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
        """Save error codes to database via DatabaseAdapter or Supabase client. Fails or logs when neither is available."""
        if not self.database_service:
            adapter.error("Cannot save error codes: no database_service available")
            return 0

        has_adapter = hasattr(self.database_service, 'create_error_code')
        has_client = hasattr(self.database_service, 'client') and self.database_service.client is not None

        if not has_adapter and not has_client:
            adapter.error(
                "Cannot save error codes: neither DatabaseAdapter (create_error_code) nor Supabase client available"
            )
            return 0

        saved_count = 0
        for error_code in error_codes:
            try:
                code_value = getattr(error_code, 'error_code', None) or ''
                page_num = getattr(error_code, 'page_number', None)
                page_num = page_num if page_num is not None else 1

                if has_adapter:
                    model = ErrorCodeModel(
                        document_id=str(document_id),
                        error_code=str(code_value),
                        error_description=getattr(error_code, 'error_description', None) or 'No description available',
                        solution_text=getattr(error_code, 'solution_text', None) or 'Refer to service manual',
                        page_number=int(page_num),
                        confidence_score=float(getattr(error_code, 'confidence', 0) or 0),
                        extraction_method=getattr(error_code, 'extraction_method', None) or 'pattern',
                        requires_technician=bool(getattr(error_code, 'requires_technician', False)),
                        requires_parts=bool(getattr(error_code, 'requires_parts', False)),
                        severity_level=str(getattr(error_code, 'severity_level', None) or 'low'),
                    )
                    await self.database_service.create_error_code(model)
                    saved_count += 1
                elif has_client:
                    error_data = {
                        'document_id': str(document_id),
                        'error_code': code_value,
                        'error_description': getattr(error_code, 'error_description', None),
                        'solution_text': getattr(error_code, 'solution_text', None),
                        'page_number': page_num,
                        'confidence_score': getattr(error_code, 'confidence', None),
                        'extraction_method': getattr(error_code, 'extraction_method', None),
                        'requires_technician': getattr(error_code, 'requires_technician', False),
                        'requires_parts': getattr(error_code, 'requires_parts', False),
                        'severity_level': getattr(error_code, 'severity_level', None),
                        'chunk_id': getattr(error_code, 'chunk_id', None),
                        'product_id': getattr(error_code, 'product_id', None),
                        'video_id': getattr(error_code, 'video_id', None),
                    }
                    result = self.database_service.client.table('error_codes').insert(error_data).execute()
                    if result.data:
                        saved_count += 1
            except Exception as e:
                adapter.warning("Failed to save error code %s: %s", getattr(error_code, 'error_code', None), e)

        return saved_count
    
    async def _update_document_version(self, document_id: str, version_info: str, adapter):
        """Update document with version information via DatabaseAdapter or Supabase client. Fails or logs when neither is available."""
        if not self.database_service:
            adapter.error("Cannot update document version: no database_service available")
            return

        has_adapter = hasattr(self.database_service, 'update_document')
        has_client = hasattr(self.database_service, 'client') and self.database_service.client is not None

        if not has_adapter and not has_client:
            adapter.error(
                "Cannot update document version: neither DatabaseAdapter (update_document) nor Supabase client available"
            )
            return

        try:
            if has_adapter:
                await self.database_service.update_document(document_id, {'version': version_info})
            else:
                self.database_service.client.table('documents').update(
                    {'version': version_info}
                ).eq('id', document_id).execute()
            adapter.info("Updated document version: %s", version_info)
        except Exception as e:
            adapter.warning("Failed to update document version: %s", e)

    def _create_result(self, success: bool, message: str, data: Dict):
        """Create a processing result object using BaseProcessor helpers.

        Returns a ProcessingResult compatible with BaseProcessor.safe_process
        and logging helpers instead of a custom ad-hoc result type.
        """

        if success:
            # Attach human-readable message to metadata for downstream logging.
            return self.create_success_result(data=data, metadata={"message": message})

        error = ProcessingError(message, self.name, "METADATA_PROCESSING_ERROR")
        return self.create_error_result(error=error, metadata={})
