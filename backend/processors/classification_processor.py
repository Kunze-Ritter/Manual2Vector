"""
Classification Processor - Classify documents by manufacturer and type

Stage 4 of the processing pipeline.

Detects manufacturer and document type using AI and pattern matching.
"""

import re
from typing import Any, Dict, Optional
from pathlib import Path

from backend.core.base_processor import BaseProcessor, Stage
from .document_type_detector import DocumentTypeDetector
from backend.utils.manufacturer_normalizer import (
    normalize_manufacturer, 
    normalize_manufacturer_prefix,
    MANUFACTURER_MAP
)


class ClassificationProcessor(BaseProcessor):
    """
    Stage 4: Classification Processor
    
    Classifies documents by manufacturer and document type.
    Uses AI for intelligent classification and pattern matching for validation.
    """
    
    def __init__(self, database_service=None, ai_service=None, features_service=None, 
                 manufacturer_verification_service=None):
        """
        Initialize classification processor
        
        Args:
            database_service: Database service instance
            ai_service: AI service instance
            features_service: Features service instance
            manufacturer_verification_service: Web-based manufacturer verification service
        """
        super().__init__(name="classification_processor")
        self.stage = Stage.CLASSIFICATION
        self.database_service = database_service
        self.ai_service = ai_service
        self.features_service = features_service
        self.manufacturer_verification_service = manufacturer_verification_service
        
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
                
                # Automatic Product Discovery after classification
                models_found = []
                if self.manufacturer_verification_service and manufacturer:
                    try:
                        # Extract models from context if available
                        models = getattr(context, 'models', [])
                        if not models and doc_metadata:
                            # Try to extract from filename with multiple patterns
                            filename = doc_metadata.get('filename', '')
                            import re
                            
                            # Multiple regex patterns for different model number formats
                            patterns = [
                                r'[A-Z]{1,3}[-_]?[0-9]{3,5}[A-Z]*',  # E877, M454dn, HL-L8360CDW
                                r'[A-Z]{2,4}[-_][A-Z]?[0-9]{3,5}[A-Z]*',  # HP-E877z, HL-L8360
                                r'(?:Color\s+)?LaserJet\s+(?:Managed\s+)?(?:MFP\s+)?([A-Z]?[0-9]{3,5}[A-Z]*)',  # LaserJet E877z
                            ]
                            
                            for pattern in patterns:
                                matches = re.findall(pattern, filename, re.IGNORECASE)
                                if matches:
                                    # Take first match, clean it up
                                    model = matches[0] if isinstance(matches[0], str) else matches[0][0]
                                    model = model.strip().replace('_', '-')
                                    models = [model]
                                    break
                        
                        if models:
                            self.logger.info(f"🔍 Starting product discovery for {len(models)} model(s)")
                            
                            for model in models[:3]:  # Limit to first 3 models
                                try:
                                    self.logger.info(f"   Discovering: {manufacturer} {model}")
                                    
                                    result = await self.manufacturer_verification_service.discover_product_page(
                                        manufacturer=manufacturer,
                                        model_number=model,
                                        save_to_db=True  # Auto-save to database
                                    )
                                    
                                    if result and result.get('url'):
                                        self.logger.success(f"   ✅ Found: {result['url']}")
                                        models_found.append({
                                            'model': model,
                                            'url': result['url'],
                                            'confidence': result.get('confidence', 0),
                                            'product_id': result.get('product_id')
                                        })
                                    else:
                                        self.logger.warning(f"   ⚠️  No product page found for {model}")
                                
                                except Exception as e:
                                    self.logger.warning(f"   ⚠️  Product discovery failed for {model}: {e}")
                            
                            if models_found:
                                self.logger.success(f"✅ Product Discovery: {len(models_found)}/{len(models)} products found")
                        else:
                            self.logger.debug("No models detected for product discovery")
                    
                    except Exception as e:
                        self.logger.warning(f"Product discovery error: {e}")

                return self._create_result(
                    success=True,
                    message=f"Classification completed: {manufacturer} - {document_type}",
                    data={
                        'manufacturer': manufacturer,
                        'document_type': document_type,
                        'version': version,
                        'products_discovered': models_found
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
        2. Document title
        3. First/last pages analysis (introduction & imprint)
        4. AI classification (content chunks)
        5. Filename parsing fallback (HP_, KM_, etc.)
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
        
        # 3. Check first and last pages for manufacturer
        if hasattr(context, 'page_texts') and context.page_texts:
            manufacturer = self._detect_manufacturer_from_pages(context.page_texts, adapter)
            if manufacturer:
                return manufacturer
        
        # 4. Use AI to detect from content (if available)
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
        
        # 5. FALLBACK: Parse filename pattern (e.g., HP_E475_SM.pdf, KM_C759_SM.pdf)
        manufacturer = self._parse_manufacturer_from_filename(file_path)
        if manufacturer:
            adapter.info("Manufacturer detected from filename pattern: %s", manufacturer)
            return manufacturer
        
        # 6. WEB VERIFICATION FALLBACK: Use web search to verify manufacturer from model numbers
        if self.manufacturer_verification_service:
            potential_models = self._extract_potential_models(file_path, context)
            if potential_models:
                adapter.debug("Attempting web verification with models: %s", potential_models)
                for model in potential_models:
                    try:
                        verification = await self.manufacturer_verification_service.verify_manufacturer(
                            model_number=model,
                            hints=[filename, title]
                        )
                        if verification and verification.get('confidence', 0) > 0.7:
                            manufacturer = verification['manufacturer']
                            adapter.info("Manufacturer verified via web search: %s (confidence: %.2f, source: %s)", 
                                       manufacturer, verification['confidence'], verification.get('source_url', 'N/A'))
                            return manufacturer
                    except Exception as e:
                        adapter.warning("Web verification failed for model %s: %s", model, e)
        
        return None
    
    def _detect_manufacturer_from_pages(
        self,
        page_texts: Dict[int, str],
        adapter
    ) -> Optional[str]:
        """
        Detect manufacturer from first and last pages
        
        Analyzes first 3 pages (introduction, branding) and last 2 pages (imprint)
        for manufacturer names using aliases from manufacturer_normalizer.
        More reliable than random chunk analysis.
        
        Args:
            page_texts: Dictionary mapping page numbers to extracted text
            adapter: Logger adapter for structured logging
            
        Returns:
            Normalized manufacturer name or None
        """
        if not page_texts or not isinstance(page_texts, dict):
            adapter.debug("No page texts available for manufacturer detection")
            return None
        
        if not page_texts:
            return None
        
        # Get total pages
        total_pages = max(page_texts.keys()) if page_texts else 0
        
        # Handle documents with few pages
        if total_pages < 3:
            # Use all available pages for small documents
            first_pages_text = "\n".join([page_texts.get(i, '') for i in sorted(page_texts.keys())])
            last_pages_text = ""
        elif total_pages < 5:
            # For documents with 3-4 pages, only use first pages (avoid overlap)
            first_pages_text = "\n".join([page_texts.get(i, '') for i in [1, 2, 3]])
            last_pages_text = ""
        else:
            # Extract first 3 pages (focus on first 2000 chars per page for performance)
            first_pages = []
            for i in [1, 2, 3]:
                page_text = page_texts.get(i, '')
                if page_text:
                    first_pages.append(page_text[:2000])
            first_pages_text = "\n".join(first_pages)
            
            # Extract last 2 pages
            last_page_numbers = [total_pages - 1, total_pages]
            last_pages = []
            for i in last_page_numbers:
                page_text = page_texts.get(i, '')
                if page_text:
                    last_pages.append(page_text)
            last_pages_text = "\n".join(last_pages)
        
        # Whitelist for short canonical names that should be detected (e.g., HP)
        SHORT_NAME_WHITELIST = {'HP'}
        
        # Search for manufacturer names in first pages (higher priority)
        # Iterate through all canonical manufacturers and their aliases
        for canonical_name, aliases in MANUFACTURER_MAP.items():
            # Check each alias for this manufacturer
            for alias in aliases:
                # Skip very short aliases to avoid false positives, unless whitelisted
                if len(alias) <= 3:
                    if alias.upper() not in SHORT_NAME_WHITELIST:
                        adapter.debug("Skipping short alias '%s' (not in whitelist)", alias)
                        continue
                    # For whitelisted short names, ensure strict word boundary matching
                    adapter.debug("Checking whitelisted short alias '%s'", alias)
                
                # Case-insensitive search with word boundaries
                pattern = r'\b' + re.escape(alias.lower()) + r'\b'
                adapter.debug("Testing alias '%s' with pattern '%s' in first pages", alias, pattern)
                
                if re.search(pattern, first_pages_text.lower()):
                    # Normalize to canonical name
                    normalized = normalize_manufacturer(alias)
                    adapter.info("Manufacturer detected from first pages (alias '%s'): %s", alias, normalized)
                    return normalized
        
        # Search for manufacturer names in last pages (lower priority)
        if last_pages_text:
            for canonical_name, aliases in MANUFACTURER_MAP.items():
                # Check each alias for this manufacturer
                for alias in aliases:
                    # Skip very short aliases to avoid false positives, unless whitelisted
                    if len(alias) <= 3:
                        if alias.upper() not in SHORT_NAME_WHITELIST:
                            adapter.debug("Skipping short alias '%s' in last pages (not in whitelist)", alias)
                            continue
                        adapter.debug("Checking whitelisted short alias '%s' in last pages", alias)
                    
                    # Case-insensitive search with word boundaries
                    pattern = r'\b' + re.escape(alias.lower()) + r'\b'
                    adapter.debug("Testing alias '%s' with pattern '%s' in last pages", alias, pattern)
                    
                    if re.search(pattern, last_pages_text.lower()):
                        # Normalize to canonical name
                        normalized = normalize_manufacturer(alias)
                        adapter.info("Manufacturer detected from last pages (alias '%s'): %s", alias, normalized)
                        return normalized
        
        return None
    
    def _extract_potential_models(self, file_path: Path, context) -> list:
        """
        Extract potential model numbers from filename and context for web verification.
        
        Args:
            file_path: Path to the document
            context: Processing context with page_texts
            
        Returns:
            List of potential model numbers (max 3 to avoid excessive API calls)
        """
        models = []
        
        # Extract from filename (e.g., HP_E475_SM.pdf → E475)
        filename_stem = file_path.stem
        # Use regex to find model-like patterns (alphanumeric, 3-10 chars)
        pattern = r'\b([A-Z0-9]{3,10})\b'
        matches = re.findall(pattern, filename_stem.upper())
        models.extend(matches)
        
        # Extract from first page if available
        if hasattr(context, 'page_texts') and context.page_texts:
            first_page = context.page_texts.get(1, '')
            if first_page:
                # Search first 500 chars for model numbers
                matches = re.findall(pattern, first_page[:500])
                models.extend(matches)
        
        # Remove duplicates and common false positives
        models = list(dict.fromkeys(models))  # Preserve order while removing duplicates
        # Filter out common document-related terms
        false_positives = {'PDF', 'SM', 'CPMD', 'FW', 'REV', 'DOC', 'MANUAL', 'SERVICE', 'PARTS', 'LIST'}
        models = [m for m in models if m not in false_positives]
        
        return models[:3]  # Limit to 3 models to avoid excessive API calls
    
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
    
    def _parse_manufacturer_from_filename(self, file_path: Path) -> Optional[str]:
        """
        Parse manufacturer from structured filename patterns
        
        Extracts manufacturer prefix from filenames like:
        - HP_E475_SM.pdf -> HP
        - KM_C759_C659_SM.pdf -> KM (Konica Minolta)
        - CANON_iR_ADV_C5550i.pdf -> CANON
        
        Args:
            file_path: Path object for the file
            
        Returns:
            Normalized manufacturer name or None
        """
        # Manufacturer prefix mapping
        PREFIX_PATTERNS = [
            'HP_', 'KM_', 'CANON_', 'RICOH_', 'XEROX_',
            'BROTHER_', 'LEXMARK_', 'SHARP_', 'EPSON_',
            'KYOCERA_', 'FUJIFILM_', 'FUJI_', 'RISO_',
            'TOSHIBA_', 'OKI_', 'UTAX_'
        ]
        
        # Get filename stem (without extension)
        filename_stem = file_path.stem.upper()
        
        # Check if filename starts with known prefix
        for prefix_pattern in PREFIX_PATTERNS:
            if filename_stem.startswith(prefix_pattern):
                # Extract prefix (remove trailing underscore)
                prefix = prefix_pattern.rstrip('_')
                # Normalize using manufacturer normalizer
                normalized = normalize_manufacturer_prefix(prefix)
                if normalized:
                    return normalized
        
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
        """Get content statistics for document via DatabaseAdapter or Supabase client. Logs and returns zeros when stats cannot be gathered."""
        stats = {
            'total_error_codes': 0,
            'parts_count': 0
        }

        if not self.database_service:
            self.logger.warning("Cannot get content statistics: no database_service available")
            return stats

        has_adapter = hasattr(self.database_service, 'fetch_one') or hasattr(self.database_service, 'fetch_all')
        has_client = hasattr(self.database_service, 'client') and self.database_service.client is not None

        if not has_adapter and not has_client:
            self.logger.warning(
                "Cannot get content statistics: neither DatabaseAdapter (fetch_one/fetch_all) nor Supabase client available"
            )
            return stats

        try:
            if has_adapter and hasattr(self.database_service, 'pg_pool') and self.database_service.pg_pool:
                intel_schema = getattr(self.database_service, '_intelligence_schema', 'krai_intelligence')
                parts_schema = getattr(self.database_service, '_parts_schema', 'krai_parts')
                async with self.database_service.pg_pool.acquire() as conn:
                    ec_row = await conn.fetchrow(
                        f"SELECT COUNT(*) as c FROM {intel_schema}.error_codes WHERE document_id = $1",
                        document_id
                    )
                    stats['total_error_codes'] = int(ec_row['c']) if ec_row else 0

                    parts_row = await conn.fetchrow(
                        f"SELECT COUNT(*) as c FROM {parts_schema}.parts_catalog WHERE document_id = $1",
                        document_id
                    )
                    stats['parts_count'] = int(parts_row['c']) if parts_row else 0
            elif has_client:
                error_codes = self.database_service.client.table('error_codes').select('id').eq('document_id', document_id).execute()
                stats['total_error_codes'] = len(error_codes.data) if error_codes.data else 0

                parts = self.database_service.client.table('parts_catalog').select('id').eq('document_id', document_id).execute()
                stats['parts_count'] = len(parts.data) if parts.data else 0
            else:
                self.logger.warning("Content statistics fallback: adapter has no pg_pool, cannot gather stats")
        except Exception as e:
            self.logger.warning("Could not get content statistics: %s", e)

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
