"""Auto Processor

Automatically processes PDFs from input_pdfs/ folder and runs complete pipeline.
"""

from pathlib import Path
import sys
import shutil
from typing import Dict

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Now import
from document_processor import DocumentProcessor
from pipeline_processor import PipelineProcessor
from logger import get_logger

logger = get_logger()


class AutoProcessor:
    """Automatically process PDFs with complete pipeline"""
    
    def __init__(self, input_dir: str = "input_pdfs", processed_dir: str = "processed_pdfs"):
        """Initialize auto processor"""
        self.logger = get_logger()
        self.input_dir = Path(input_dir)
        self.processed_dir = Path(processed_dir)
        self.document_processor = DocumentProcessor(manufacturer="AUTO")
        self.pipeline_processor = PipelineProcessor()
        
        # Create directories if they don't exist
        self.input_dir.mkdir(exist_ok=True)
        self.processed_dir.mkdir(exist_ok=True)
    
    def process_all_pdfs(self) -> Dict:
        """
        Process all PDFs in input_pdfs/ folder
        
        Returns:
            Dict with statistics
        """
        self.logger.info("=" * 80)
        self.logger.info("AUTO PROCESSOR - PROCESSING ALL PDFs")
        self.logger.info("=" * 80)
        
        stats = {
            'pdfs_found': 0,
            'pdfs_processed': 0,
            'pdfs_failed': 0,
            'total_parts_found': 0,
            'total_series_created': 0
        }
        
        # Find all PDFs
        pdf_files = list(self.input_dir.glob("*.pdf"))
        stats['pdfs_found'] = len(pdf_files)
        
        if not pdf_files:
            self.logger.warning(f"No PDFs found in {self.input_dir}")
            return stats
        
        self.logger.info(f"Found {len(pdf_files)} PDFs to process")
        self.logger.info("")
        
        for pdf_path in pdf_files:
            self.logger.info("=" * 80)
            self.logger.info(f"PROCESSING: {pdf_path.name}")
            self.logger.info("=" * 80)
            
            try:
                result = self.process_single_pdf(pdf_path)
                
                if result['success']:
                    stats['pdfs_processed'] += 1
                    stats['total_parts_found'] += result.get('parts_found', 0)
                    stats['total_series_created'] += result.get('series_created', 0)
                    
                    # Move to processed folder
                    self._move_to_processed(pdf_path)
                else:
                    stats['pdfs_failed'] += 1
                    self.logger.error(f"Failed: {result.get('error')}")
                    
            except Exception as e:
                stats['pdfs_failed'] += 1
                self.logger.error(f"Error processing {pdf_path.name}: {e}")
            
            self.logger.info("")
        
        # Final summary
        self.logger.info("=" * 80)
        self.logger.info("AUTO PROCESSOR COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"PDFs found: {stats['pdfs_found']}")
        self.logger.info(f"PDFs processed: {stats['pdfs_processed']}")
        self.logger.info(f"PDFs failed: {stats['pdfs_failed']}")
        self.logger.info(f"Total parts found: {stats['total_parts_found']}")
        self.logger.info(f"Total series created: {stats['total_series_created']}")
        
        return stats
    
    def process_single_pdf(self, pdf_path: Path) -> Dict:
        """
        Process single PDF with complete pipeline
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dict with result
        """
        result = {
            'success': False,
            'document_id': None,
            'parts_found': 0,
            'series_created': 0
        }
        
        try:
            # STAGE 1-5: Document Processing (Text, Images, Classification, Error Codes)
            self.logger.info("STAGE 1-5: Document Processing")
            self.logger.info("-" * 80)
            
            doc_result = self.document_processor.process_document(pdf_path)
            
            if not doc_result or not doc_result.get('success'):
                result['error'] = doc_result.get('error', 'Unknown error')
                return result
            
            document_id = doc_result['document_id']
            result['document_id'] = document_id
            
            self.logger.info(f"✅ Document Processing Complete")
            self.logger.info(f"   - Document ID: {document_id}")
            self.logger.info(f"   - Pages: {doc_result.get('metadata', {}).get('page_count', 0)}")
            self.logger.info(f"   - Error Codes: {len(doc_result.get('error_codes', []))}")
            self.logger.info("")
            
            # STAGE 6-7: Pipeline Processing (Parts + Series)
            self.logger.info("STAGE 6-7: Parts & Series Processing")
            self.logger.info("-" * 80)
            
            pipeline_result = self.pipeline_processor.process_document_full_pipeline(document_id)
            
            if pipeline_result.get('success'):
                result['success'] = True
                result['parts_found'] = pipeline_result['stages']['parts_extraction']['parts_found']
                result['series_created'] = pipeline_result['stages']['series_detection']['series_created']
            else:
                result['error'] = pipeline_result.get('error', 'Pipeline failed')
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Error in process_single_pdf: {e}")
            return result
    
    def _move_to_processed(self, pdf_path: Path):
        """Move PDF to processed folder"""
        try:
            dest_path = self.processed_dir / pdf_path.name
            
            # If file exists in processed, add timestamp
            if dest_path.exists():
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_path = self.processed_dir / f"{pdf_path.stem}_{timestamp}.pdf"
            
            shutil.move(str(pdf_path), str(dest_path))
            self.logger.info(f"✅ Moved to: {dest_path}")
            
            # Also move log file if exists
            log_file = pdf_path.parent / f"{pdf_path.stem}.log.txt"
            if log_file.exists():
                log_dest = self.processed_dir / f"{pdf_path.stem}.log.txt"
                shutil.move(str(log_file), str(log_dest))
                
        except Exception as e:
            self.logger.warning(f"Could not move file: {e}")


def main():
    """Run auto processor"""
    processor = AutoProcessor()
    stats = processor.process_all_pdfs()
    
    print("\n" + "=" * 80)
    print("FINAL STATISTICS")
    print("=" * 80)
    print(f"PDFs processed: {stats['pdfs_processed']}/{stats['pdfs_found']}")
    print(f"PDFs failed: {stats['pdfs_failed']}")
    print(f"Total parts found: {stats['total_parts_found']}")
    print(f"Total series created: {stats['total_series_created']}")


if __name__ == '__main__':
    main()
