"""Pipeline Processor

Master processor that runs all processing stages in sequence.
"""

from typing import Dict, Optional
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import with relative paths from processors directory
from .logger import get_logger
from .parts_processor import PartsProcessor
from .series_processor import SeriesProcessor

logger = get_logger()


class PipelineProcessor:
    """Master processor that orchestrates all processing stages"""
    
    def __init__(self):
        """Initialize pipeline processor"""
        from database.supabase_client import get_supabase_client
        self.supabase = get_supabase_client()
        self.logger = get_logger()
        self.parts_processor = PartsProcessor()
        self.series_processor = SeriesProcessor()
        
    def process_document_full_pipeline(self, document_id: str) -> Dict:
        """
        Run complete processing pipeline for a document
        
        Stages:
        1. Document Upload (already done)
        2. Text Extraction (already done)
        3. Image Processing (already done)
        4. Classification (already done)
        5. Metadata Extraction - Error Codes (already done)
        6. Parts Extraction (NEW!)
        7. Series Detection (NEW!)
        8. Storage (already done)
        9. Embedding (already done)
        10. Search Indexing (already done)
        
        Args:
            document_id: UUID of document to process
            
        Returns:
            Dict with statistics from all stages
        """
        self.logger.info(f"=" * 80)
        self.logger.info(f"STARTING FULL PIPELINE FOR DOCUMENT: {document_id}")
        self.logger.info(f"=" * 80)
        
        start_time = time.time()
        
        pipeline_stats = {
            'document_id': document_id,
            'stages': {},
            'total_duration_seconds': 0,
            'success': True
        }
        
        try:
            # Get document info
            doc_result = self.supabase.table('documents').select(
                '*, manufacturer:manufacturer_id(name)'
            ).eq('id', document_id).execute()
            
            if not doc_result.data:
                raise ValueError(f"Document {document_id} not found")
            
            document = doc_result.data[0]
            doc_title = document.get('title', 'Unknown')
            manufacturer = document.get('manufacturer', {}).get('name', 'Unknown')
            
            self.logger.info(f"Document: {doc_title}")
            self.logger.info(f"Manufacturer: {manufacturer}")
            self.logger.info("")
            
            # ============================================================
            # STAGE 6: PARTS EXTRACTION
            # ============================================================
            self.logger.info("STAGE 6: Parts Extraction")
            self.logger.info("-" * 80)
            
            stage_start = time.time()
            parts_stats = self.parts_processor.process_document(document_id)
            stage_duration = time.time() - stage_start
            
            pipeline_stats['stages']['parts_extraction'] = {
                **parts_stats,
                'duration_seconds': round(stage_duration, 2)
            }
            
            self.logger.info(f"✅ Parts Extraction Complete in {stage_duration:.2f}s")
            self.logger.info(f"   - Chunks processed: {parts_stats['chunks_processed']}")
            self.logger.info(f"   - Parts found: {parts_stats['parts_found']}")
            self.logger.info(f"   - Parts created: {parts_stats['parts_created']}")
            self.logger.info(f"   - Parts updated: {parts_stats['parts_updated']}")
            self.logger.info("")
            
            # ============================================================
            # STAGE 7: SERIES DETECTION
            # ============================================================
            self.logger.info("STAGE 7: Series Detection")
            self.logger.info("-" * 80)
            
            stage_start = time.time()
            series_stats = self._detect_series_for_document_products(document_id)
            stage_duration = time.time() - stage_start
            
            pipeline_stats['stages']['series_detection'] = {
                **series_stats,
                'duration_seconds': round(stage_duration, 2)
            }
            
            self.logger.info(f"✅ Series Detection Complete in {stage_duration:.2f}s")
            self.logger.info(f"   - Products processed: {series_stats['products_processed']}")
            self.logger.info(f"   - Series detected: {series_stats['series_detected']}")
            self.logger.info(f"   - Series created: {series_stats['series_created']}")
            self.logger.info(f"   - Products linked: {series_stats['products_linked']}")
            self.logger.info("")
            
            # ============================================================
            # PIPELINE COMPLETE
            # ============================================================
            total_duration = time.time() - start_time
            pipeline_stats['total_duration_seconds'] = round(total_duration, 2)
            
            self.logger.info("=" * 80)
            self.logger.info(f"✅ PIPELINE COMPLETE IN {total_duration:.2f}s")
            self.logger.info("=" * 80)
            
            return pipeline_stats
            
        except Exception as e:
            self.logger.error(f"❌ Pipeline failed: {e}")
            pipeline_stats['success'] = False
            pipeline_stats['error'] = str(e)
            return pipeline_stats
    
    def _detect_series_for_document_products(self, document_id: str) -> Dict:
        """
        Detect series for all products mentioned in a document
        
        Args:
            document_id: Document UUID
            
        Returns:
            Dict with statistics
        """
        stats = {
            'products_processed': 0,
            'series_detected': 0,
            'series_created': 0,
            'products_linked': 0,
            'errors': 0
        }
        
        try:
            # Get all error codes for this document (they have product_id)
            error_codes_result = self.supabase.table('error_codes').select(
                'product_id'
            ).eq('document_id', document_id).not_.is_('product_id', 'null').execute()
            
            # Get unique product IDs
            product_ids = list(set([ec['product_id'] for ec in error_codes_result.data]))
            
            self.logger.info(f"Found {len(product_ids)} unique products in document")
            
            # Process each product
            for product_id in product_ids:
                stats['products_processed'] += 1
                
                try:
                    result = self.series_processor.process_product(product_id)
                    if result:
                        stats['series_detected'] += 1
                        if result['series_created']:
                            stats['series_created'] += 1
                        if result['product_linked']:
                            stats['products_linked'] += 1
                except Exception as e:
                    self.logger.error(f"Error processing product {product_id}: {e}")
                    stats['errors'] += 1
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error detecting series for document: {e}")
            stats['errors'] += 1
            return stats
    
    def process_all_documents(self) -> Dict:
        """
        Run pipeline for all documents that need processing
        
        Returns:
            Dict with overall statistics
        """
        self.logger.info("=" * 80)
        self.logger.info("PROCESSING ALL DOCUMENTS")
        self.logger.info("=" * 80)
        
        overall_stats = {
            'documents_processed': 0,
            'total_parts_found': 0,
            'total_series_created': 0,
            'errors': 0
        }
        
        try:
            # Get all documents
            docs_result = self.supabase.table('documents').select('id, title').execute()
            documents = docs_result.data
            
            self.logger.info(f"Found {len(documents)} documents to process")
            self.logger.info("")
            
            for doc in documents:
                doc_id = doc['id']
                doc_title = doc.get('title', 'Unknown')
                
                self.logger.info(f"Processing: {doc_title}")
                
                try:
                    stats = self.process_document_full_pipeline(doc_id)
                    
                    if stats['success']:
                        overall_stats['documents_processed'] += 1
                        overall_stats['total_parts_found'] += stats['stages']['parts_extraction']['parts_found']
                        overall_stats['total_series_created'] += stats['stages']['series_detection']['series_created']
                    else:
                        overall_stats['errors'] += 1
                        
                except Exception as e:
                    self.logger.error(f"Error processing document {doc_id}: {e}")
                    overall_stats['errors'] += 1
                
                self.logger.info("")
            
            self.logger.info("=" * 80)
            self.logger.info("ALL DOCUMENTS PROCESSED")
            self.logger.info("=" * 80)
            self.logger.info(f"Documents processed: {overall_stats['documents_processed']}")
            self.logger.info(f"Total parts found: {overall_stats['total_parts_found']}")
            self.logger.info(f"Total series created: {overall_stats['total_series_created']}")
            self.logger.info(f"Errors: {overall_stats['errors']}")
            
            return overall_stats
            
        except Exception as e:
            self.logger.error(f"Error in batch processing: {e}")
            overall_stats['errors'] += 1
            return overall_stats


def main():
    """Run pipeline processor"""
    import sys
    
    processor = PipelineProcessor()
    
    if len(sys.argv) > 1:
        # Process specific document
        document_id = sys.argv[1]
        stats = processor.process_document_full_pipeline(document_id)
        
        print("\n" + "=" * 80)
        print("PIPELINE RESULTS")
        print("=" * 80)
        
        if stats['success']:
            print(f"✅ SUCCESS in {stats['total_duration_seconds']}s")
            print("\nStage Results:")
            for stage_name, stage_stats in stats['stages'].items():
                print(f"\n{stage_name.upper()}:")
                for key, value in stage_stats.items():
                    if key != 'duration_seconds':
                        print(f"  - {key}: {value}")
                print(f"  - Duration: {stage_stats.get('duration_seconds', 0)}s")
        else:
            print(f"❌ FAILED: {stats.get('error', 'Unknown error')}")
    else:
        # Process all documents
        stats = processor.process_all_documents()
        
        print("\n" + "=" * 80)
        print("BATCH PROCESSING RESULTS")
        print("=" * 80)
        print(f"Documents processed: {stats['documents_processed']}")
        print(f"Total parts found: {stats['total_parts_found']}")
        print(f"Total series created: {stats['total_series_created']}")
        print(f"Errors: {stats['errors']}")


if __name__ == '__main__':
    main()
