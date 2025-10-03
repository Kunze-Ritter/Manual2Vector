"""
Test script for Processor V2

Usage:
    python test_processor.py path/to/test.pdf
    python test_processor.py path/to/test.pdf --manufacturer Canon
"""

import sys
import argparse
from pathlib import Path
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors_v2.document_processor import DocumentProcessor
from processors_v2.logger import get_logger

def main():
    parser = argparse.ArgumentParser(
        description="Test Document Processor V2"
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output JSON file path (optional)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging for product extraction'
    )
    parser.add_argument(
        '--manufacturer',
        type=str,
        default="HP",
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1000,
        help="Chunk size (default: 1000)"
    )
    parser.add_argument(
        'pdf_path',
        type=Path,
        help="Path to PDF file"
    )
    
    args = parser.parse_args()
    
    # Check PDF exists
    if not args.pdf_path.exists():
        print(f"❌ PDF not found: {args.pdf_path}")
        sys.exit(1)
    
    # Get logger
    logger = get_logger()
    
    # Initialize processor
    logger.section("Processor V2 Test")
    logger.info(f"PDF: {args.pdf_path}")
    logger.info(f"Manufacturer: {args.manufacturer}")
    
    processor = DocumentProcessor(
        manufacturer=args.manufacturer,
        chunk_size=args.chunk_size,
        debug=args.debug
    )
    
    # Process
    result = processor.process_document(args.pdf_path)
    
    # Display results
    logger.section("Results")
    
    if result.success:
        # Summary
        summary_data = {
            "Document": args.pdf_path.name,
            "Pages": result.metadata.page_count,
            "Chunks": len(result.chunks),
            "Products": len(result.products),
            "Error Codes": len(result.error_codes),
            "Validation Errors": len(result.validation_errors)
        }
        logger.table(summary_data, title="📊 Processing Summary")
        
        # Products
        if result.products:
            logger.panel(
                "\n".join([
                    f"• {p.model_number} ({p.product_type}) - Confidence: {p.confidence:.2f}"
                    for p in result.products[:10]
                ]),
                title="📦 Products Extracted",
                style="green"
            )
        
        # Error Codes
        if result.error_codes:
            logger.panel(
                "\n".join([
                    f"• {e.error_code}: {e.error_description[:60]}... - Confidence: {e.confidence:.2f}"
                    for e in result.error_codes[:10]
                ]),
                title="🔴 Error Codes Extracted",
                style="yellow"
            )
        
        # Validation Errors
        if result.validation_errors:
            logger.warning(f"Found {len(result.validation_errors)} validation errors:")
            for error in result.validation_errors[:5]:
                logger.warning(f"  {error}")
        
        # Statistics
        logger.table(result.statistics, title="📈 Statistics")
        
        # Save to file
        if args.output:
            # Convert to absolute path if relative
            output_path = args.output if args.output.is_absolute() else Path.cwd() / args.output
            logger.info(f"Saving results to: {output_path}")
            save_results(result, output_path)
            logger.success(f"Results saved to: {output_path}")
        
    else:
        logger.error("Processing failed!")
        for error in result.validation_errors:
            logger.error(f"  {error}")
    
    logger.section("Test Complete")


def save_results(result, output_path: Path):
    """Save results to JSON file"""
    
    # Convert to dict
    data = {
        "document_id": str(result.document_id),
        "success": result.success,
        "metadata": {
            "title": result.metadata.title,
            "page_count": result.metadata.page_count,
            "document_type": result.metadata.document_type,
        },
        "chunks": [
            {
                "chunk_id": str(c.chunk_id),
                "chunk_index": c.chunk_index,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "text_preview": c.text[:200],
                "chunk_type": c.chunk_type,
            }
            for c in result.chunks[:50]  # First 50
        ],
        "products": [
            {
                "model_number": p.model_number,
                "product_type": p.product_type,
                "confidence": p.confidence,
                "source_page": p.source_page,
            }
            for p in result.products
        ],
        "error_codes": [
            {
                "error_code": e.error_code,
                "description": e.error_description,
                "solution": e.solution_text,
                "confidence": e.confidence,
                "page_number": e.page_number,
                "severity": e.severity_level,
            }
            for e in result.error_codes
        ],
        "statistics": result.statistics,
        "processing_time": result.processing_time_seconds
    }
    
    # Write
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
