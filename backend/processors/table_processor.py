"""
Table Processor - Extract and embed structured tables
Stage 2b of the processing pipeline. Extracts tables from PDFs using PyMuPDF.

Features:
- PyMuPDF table detection (strategy: lines, text)
- Markdown export for embeddings
- JSONB storage for structured queries
- Column-specific embeddings (future)
- Integration with embeddings_v2 table
"""

import os
import json
import hashlib
import logging
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4

import pymupdf  # PyMuPDF
import pandas as pd

from core.base_processor import BaseProcessor, ProcessingResult, Stage, ProcessingContext

class TableProcessor(BaseProcessor):
    """Extract tables from PDFs and generate embeddings"""
    
    def __init__(
        self,
        database_service,
        embedding_service,
        strategy: str = 'lines',
        fallback_strategy: str = 'text',
        min_rows: int = 2,
        min_cols: int = 2
    ):
        super().__init__(name="TableProcessor")
        self.stage = Stage.TABLE_EXTRACTION
        self.database_service = database_service
        self.embedding_service = embedding_service
        self.strategy = strategy
        self.fallback_strategy = fallback_strategy
        self.min_rows = min_rows
        self.min_cols = min_cols
        
        # Remove custom logger - use BaseProcessor.logger_context instead
        
        # Check if table extraction is enabled
        self.enabled = os.getenv('ENABLE_TABLE_EXTRACTION', 'true').lower() == 'true'
        if not self.enabled:
            with self.logger_context() as adapter:
                adapter.info("Table extraction disabled via ENABLE_TABLE_EXTRACTION")
            return
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """Extract and process tables from document"""
        with self.logger_context(document_id=context.document_id, stage=self.stage.value) as adapter:
            adapter.info(f"Starting table extraction for document {context.document_id}")
            
            # Start stage tracking
            if self.stage_tracker:
                self.stage_tracker.start_stage(str(context.document_id), self.stage.value)
            
            try:
                # Validate context
                if not context.document_id:
                    if self.stage_tracker:
                        self.stage_tracker.fail_stage(
                            str(context.document_id) if context.document_id else "unknown",
                            self.stage.value,
                            error="Document ID is required"
                        )
                    return self.create_error_result("Document ID is required")
                
                if not hasattr(context, 'pdf_path') or not context.pdf_path:
                    if self.stage_tracker:
                        self.stage_tracker.fail_stage(
                            str(context.document_id),
                            self.stage.value,
                            error="PDF path is required"
                        )
                    return self.create_error_result("PDF path is required")
                
                if not os.path.exists(context.pdf_path):
                    if self.stage_tracker:
                        self.stage_tracker.fail_stage(
                            str(context.document_id),
                            self.stage.value,
                            error=f"PDF file not found: {context.pdf_path}"
                        )
                    return self.create_error_result(f"PDF file not found: {context.pdf_path}")
                
                # Process tables
                result = await self.process_document(context.document_id, context.pdf_path)
                
                if result['success']:
                    return self.create_success_result(
                        data={
                            'tables_extracted': result['tables_extracted'],
                            'embeddings_created': result['embeddings_created']
                        },
                        metadata={
                            'stage': self.stage.value,
                            'processing_time': result.get('processing_time', 0)
                        }
                    )
                else:
                    if self.stage_tracker:
                        self.stage_tracker.fail_stage(
                            str(context.document_id),
                            self.stage.value,
                            error=result.get('error', 'Unknown error')
                        )
                    return self.create_error_result(
                        result.get('error', 'Unknown error'),
                        data={'tables_extracted': 0, 'embeddings_created': 0}
                    )
                    
            except Exception as e:
                adapter.error(f"Table processing failed: {e}")
                if self.stage_tracker:
                    self.stage_tracker.fail_stage(
                        str(context.document_id) if context.document_id else "unknown",
                        self.stage.value,
                        error=str(e)
                    )
                return self.create_error_result(
                    str(e),
                    data={'tables_extracted': 0, 'embeddings_created': 0}
                )  
    
    async def process_document(self, document_id: UUID, pdf_path: str) -> Dict[str, Any]:
        """Extract tables from PDF document"""
        with self.logger_context(document_id=document_id, stage=self.stage.value) as adapter:
            try:
                # Open PDF document
                doc = pymupdf.open(pdf_path)
                
                # Start stage tracking
                if self.stage_tracker:
                    self.stage_tracker.start_stage(str(document_id), self.stage.value)
                
                all_tables = []
                
                # Extract tables from all pages
                for page_num, page in enumerate(doc):
                    try:
                        page_tables = self._extract_page_tables(page, page_num + 1)
                        all_tables.extend(page_tables)
                        
                        if page_tables:
                            adapter.info(f"Page {page_num + 1}: Found {len(page_tables)} tables")
                            
                    except Exception as e:
                        adapter.warning(f"Failed to extract tables from page {page_num + 1}: {e}")
                        continue
                
                doc.close()
                
                # Generate embeddings for tables
                tables_with_embeddings = []
                for table in all_tables:
                    try:
                        embedding = self._generate_table_embedding(table['table_markdown'])
                        table['embedding'] = embedding
                        tables_with_embeddings.append(table)
                    except Exception as e:
                        adapter.warning(f"Failed to generate embedding for table {table['id']}: {e}")
                        # Still include table without embedding
                        tables_with_embeddings.append(table)
                
                # Store tables in database
                storage_results = await self._store_tables(document_id, tables_with_embeddings)
                
                # Complete stage tracking
                if self.stage_tracker:
                    self.stage_tracker.complete_stage(
                        str(document_id),
                        self.stage.value,
                        metadata={
                            'tables_extracted': len(all_tables),
                            'embeddings_created': storage_results['embedding_count'],
                            'storage_success': storage_results['storage_success'],
                            'storage_failed': storage_results['storage_failed']
                        }
                    )
                
                return {
                    'success': True,
                    'tables_extracted': len(all_tables),
                    'embeddings_created': storage_results['embedding_count'],
                    'tables': tables_with_embeddings,
                    'storage_results': storage_results
                }
                
            except Exception as e:
                adapter.error(f"Table extraction failed: {e}")
                if self.stage_tracker:
                    self.stage_tracker.fail_stage(
                        str(document_id),
                        self.stage.value,
                        error=str(e)
                    )
                return {
                    'success': False,
                    'error': str(e),
                    'tables_extracted': 0,
                    'embeddings_created': 0
                }
    
    def _extract_page_tables(self, page, page_number: int) -> List[Dict[str, Any]]:
        """Extract tables from a single page"""
        tables = []
        
        with self.logger_context() as adapter:
            try:
                # Try primary strategy
                tabs = page.find_tables(strategy=self.strategy)
                
                # If no tables found, try fallback strategy
                if not tabs.tables:
                    tabs = page.find_tables(strategy=self.fallback_strategy)
                    adapter.debug(f"Page {page_number}: Used fallback strategy '{self.fallback_strategy}'")
                
                # Process each detected table
                for table_idx, tab in enumerate(tabs.tables):
                    try:
                        table_data = self._extract_table_data(tab, page, page_number, table_idx)
                        if table_data:
                            tables.append(table_data)
                    except Exception as e:
                        adapter.warning(f"Failed to extract table {table_idx} on page {page_number}: {e}")
                        continue
                
            except Exception as e:
                adapter.warning(f"Table detection failed on page {page_number}: {e}")
        
        return tables
    
    def _extract_table_data(self, tab, page, page_number: int, table_index: int) -> Optional[Dict[str, Any]]:
        """Extract and process table data"""
        with self.logger_context() as adapter:
            try:
                # Extract table data
                raw_data = tab.extract()
                
                # Validate table structure
                if len(raw_data) < self.min_rows + 1:  # +1 for header
                    adapter.debug(f"Table too small: {len(raw_data)} rows (min: {self.min_rows + 1})")
                    return None
                
                if len(raw_data[0]) < self.min_cols:
                    adapter.debug(f"Table too narrow: {len(raw_data[0])} columns (min: {self.min_cols})")
                    return None
                
                # Convert to DataFrame for easier processing
                try:
                    df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                except Exception as e:
                    adapter.warning(f"Failed to create DataFrame: {e}")
                    return None
                
                # Clean DataFrame
                df = df.dropna(how='all')  # Drop empty rows
                df = df.loc[:, ~df.columns.duplicated()]  # Remove duplicate columns
                
                if len(df) < self.min_rows or len(df.columns) < self.min_cols:
                    adapter.debug(f"Table too small after cleaning: {len(df)} rows x {len(df.columns)} cols")
                    return None
                
                # Generate markdown representation
                table_markdown = df.to_markdown(index=False, tablefmt='grid')
                
                # Extract context around table
                context_text = self._extract_table_context(page, tab.bbox)
                
                # Detect table type
                table_type = self._detect_table_type(df)
                
                # Extract caption if available
                caption = self._extract_caption(page, tab.bbox)
                
                # Convert bbox to primitive sequence for JSON serialization
                bbox_list = [float(tab.bbox.x0), float(tab.bbox.y0), float(tab.bbox.x1), float(tab.bbox.y1)]
                
                # Create table record
                table_record = {
                    'id': str(uuid4()),
                    'page_number': page_number,
                    'table_index': table_index,
                    'table_type': table_type,
                    'column_headers': raw_data[0],
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'table_data': raw_data,  # Raw data as list of lists
                    'table_markdown': table_markdown,
                    'caption': caption,
                    'context_text': context_text,
                    'bbox': json.dumps(bbox_list),
                    'metadata': {
                        'extraction_strategy': self.strategy,
                        'data_quality': self._assess_data_quality(df),
                        'has_headers': True,  # Assume first row is headers
                        'extraction_timestamp': pd.Timestamp.now().isoformat()
                    }
                }
                
                return table_record
                
            except Exception as e:
                adapter.error(f"Table data extraction failed: {e}")
                return None
    
    def _extract_table_context(self, page, bbox: tuple) -> str:
        """Extract text context around table"""
        with self.logger_context() as adapter:
            try:
                # Get text before and after table
                page_rect = page.rect
                
                # Extract text from regions above and below table
                above_rect = pymupdf.Rect(0, 0, page_rect.width, bbox[1])
                below_rect = pymupdf.Rect(0, bbox[3], page_rect.width, page_rect.height)
                
                above_text = page.get_text(clip=above_rect).strip()
                below_text = page.get_text(clip=below_rect).strip()
                
                # Get last 200 characters from above and first 200 from below
                context_above = above_text[-200:] if above_text else ""
                context_below = below_text[:200] if below_text else ""
                
                context = f"{context_above} ... {context_below}".strip()
                
                # Extract error codes and product numbers from context
                error_codes = re.findall(r'\d{2}\.\d{2}\.\d{2}', context)
                products = re.findall(r'[A-Z]\d{4}', context)
                
                # Add structured context info
                structured_context = {
                    'text': context,
                    'error_codes': error_codes,
                    'products': products,
                    'page_header': self._extract_page_header(page)
                }
                
                return json.dumps(structured_context, ensure_ascii=False)
                
            except Exception as e:
                adapter.warning(f"Context extraction failed: {e}")
                return "{}"
    
    def _detect_table_type(self, df: pd.DataFrame) -> str:
        """Detect table type based on content and structure"""
        with self.logger_context() as adapter:
            try:
                # Convert column names to lowercase for analysis
                cols_lower = [col.lower() if isinstance(col, str) else str(col).lower() for col in df.columns]
                cols_text = ' '.join(cols_lower)
                
                # Specification table
                if any(keyword in cols_text for keyword in ['specification', 'spec', 'value', 'parameter', 'eigenschaft']):
                    return 'specification'
                
                # Comparison table
                if any(keyword in cols_text for keyword in ['model', 'speed', 'resolution', 'leistung', 'geschwindigkeit']):
                    return 'comparison'
                
                # Parts list
                if any(keyword in cols_text for keyword in ['part', 'number', 'description', 'teil', 'nummer', 'beschreibung']):
                    return 'parts_list'
                
                # Error codes
                if any(keyword in cols_text for keyword in ['error', 'code', 'fehler', 'fehlercode']):
                    return 'error_codes'
                
                # Compatibility table
                if any(keyword in cols_text for keyword in ['compatible', 'compatibility', 'kompatibel']):
                    return 'compatibility'
                
                # Default
                return 'other'
                
            except Exception as e:
                adapter.warning(f"Table type detection failed: {e}")
                return 'other'
    
    def _extract_caption(self, page, bbox: tuple) -> Optional[str]:
        """Extract table caption from text above table"""
        with self.logger_context() as adapter:
            try:
                # Look for text in the 50 points above the table
                caption_rect = pymupdf.Rect(bbox[0], bbox[1] - 50, bbox[2], bbox[1])
                caption_text = page.get_text(clip=caption_rect).strip()
                
                # Look for common caption patterns
                caption_patterns = [
                    r'table\s+\d+[.:]\s*(.+)',
                    r'tabelle\s+\d+[.:]\s*(.+)',
                    r'fig[ure]*\s*\d+[.:]\s*(.+)',
                    r'abbildung\s*\d+[.:]\s*(.+)'
                ]
                
                for pattern in caption_patterns:
                    match = re.search(pattern, caption_text, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
                
                # Return text if no pattern matched but text exists
                return caption_text if caption_text else None
                
            except Exception as e:
                adapter.warning(f"Caption extraction failed: {e}")
                return None
    
    def _extract_page_header(self, page) -> str:
        """Extract page header text"""
        with self.logger_context() as adapter:
            try:
                # Extract text from top of page (first 50 points)
                header_rect = pymupdf.Rect(0, 0, page.rect.width, 50)
                header_text = page.get_text(clip=header_rect).strip()
                return header_text
            except Exception as e:
                adapter.warning(f"Page header extraction failed: {e}")
                return ""
    
    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess quality of extracted table data"""
        with self.logger_context() as adapter:
            try:
                total_cells = len(df) * len(df.columns)
                empty_cells = df.isnull().sum().sum()
                completeness = (total_cells - empty_cells) / total_cells if total_cells > 0 else 0
                
                # Check for consistent data types in columns
                consistent_types = 0
                for col in df.columns:
                    non_null = df[col].dropna()
                    if len(non_null) > 1:
                        first_type = type(non_null.iloc[0])
                        if all(isinstance(x, first_type) for x in non_null):
                            consistent_types += 1
                
                type_consistency = consistent_types / len(df.columns) if len(df.columns) > 0 else 0
                
                return {
                    'completeness': round(completeness, 2),
                    'type_consistency': round(type_consistency, 2),
                    'total_rows': len(df),
                    'total_columns': len(df.columns),
                    'empty_cells': int(empty_cells)
                }
                
            except Exception as e:
                adapter.warning(f"Data quality assessment failed: {e}")
                return {'completeness': 0, 'type_consistency': 0}
    
    def _generate_table_embedding(self, table_markdown: str) -> List[float]:
        """Generate embedding for table using embedding service"""
        with self.logger_context() as adapter:
            try:
                # Use the embedding service to generate embedding
                # This assumes the embedding service has a _generate_embedding method
                embedding = self.embedding_service._generate_embedding(table_markdown)
                return embedding
            except Exception as e:
                adapter.error(f"Table embedding generation failed: {e}")
                return []
    
    async def _store_tables(self, document_id: UUID, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store tables and their embeddings in database"""
        storage_success = 0
        storage_failed = 0
        embedding_count = 0
        
        with self.logger_context() as adapter:
            try:
                for table in tables:
                    try:
                        # Create table record for structured_tables
                        table_record = {
                            'id': table['id'],
                            'document_id': str(document_id),
                            'page_number': table['page_number'],
                            'table_index': table['table_index'],
                            'table_type': table['table_type'],
                            'column_headers': table['column_headers'],
                            'row_count': table['row_count'],
                            'column_count': table['column_count'],
                            'table_data': json.dumps(table['table_data'], ensure_ascii=False),
                            'table_markdown': table['table_markdown'],
                            'caption': table.get('caption'),
                            'context_text': table.get('context_text'),
                            'bbox': table['bbox'],  # Already serialized as JSON string
                            'metadata': json.dumps(table.get('metadata', {}), ensure_ascii=False)
                        }
                        
                        # Store structured table
                        table_id = await self.database_service.create_structured_table(table_record)
                        
                        # Store embedding if available
                        if 'embedding' in table and table['embedding']:
                            embedding_id = await self.database_service.create_embedding_v2(
                                source_id=table['id'],
                                source_type='table',
                                embedding=table['embedding'],
                                model_name='nomic-embed-text:latest',
                                embedding_context=table['table_markdown'][:500],
                                metadata={
                                    'table_type': table['table_type'],
                                    'page_number': table['page_number'],
                                    'row_count': table['row_count'],
                                    'column_count': table['column_count']
                                }
                            )
                            embedding_count += 1
                        
                        storage_success += 1
                        
                    except Exception as e:
                        adapter.error(f"Failed to store table {table.get('id', 'unknown')}: {e}")
                        storage_failed += 1
                
                return {
                    'storage_success': storage_success,
                    'storage_failed': storage_failed,
                    'embedding_count': embedding_count
                }
                
            except Exception as e:
                adapter.error(f"Batch table storage failed: {e}")
                return {
                    'storage_success': storage_success,
                    'storage_failed': len(tables),
                    'embedding_count': embedding_count
                }
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get processor configuration status"""
        return {
            'enabled': self.enabled,
            'strategy': self.strategy,
            'fallback_strategy': self.fallback_strategy,
            'min_rows': self.min_rows,
            'min_cols': self.min_cols,
            'dependencies': {
                'pymupdf': pymupdf.__version__,
                'pandas': pd.__version__
            }
        }
