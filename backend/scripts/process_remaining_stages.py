#!/usr/bin/env python3
"""
Process Remaining Stages Script
Verarbeitet alle verbleibenden Stages für Dokumente die bereits in der DB sind
"""

import asyncio
import logging
from typing import Dict, List, Any
import sys
import os
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.krai_master_pipeline import KRMasterPipeline

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to process remaining stages"""
    logger.info("Starting Remaining Stages Processing")
    
    try:
        # Initialize pipeline
        pipeline = KRMasterPipeline()
        await pipeline.initialize_services()
        
        # Get documents that need processing
        pending_docs = await pipeline.get_documents_needing_processing()
        
        if not pending_docs:
            logger.info("No documents need remaining stages processing!")
            return
        
        logger.info(f"Found {len(pending_docs)} documents that need remaining stages:")
        
        # Show document list
        for i, doc in enumerate(pending_docs[:10]):  # Show first 10
            status_icon = "[FAILED]" if doc['processing_status'] == 'failed' else "[PENDING]"
            logger.info(f"  {i+1}. {doc['filename']} {status_icon}")
        
        if len(pending_docs) > 10:
            logger.info(f"  ... und {len(pending_docs) - 10} weitere")
        
        # Ask for confirmation
        response = input(f"\nProcess remaining stages for {len(pending_docs)} documents? (y/n): ").lower().strip()
        if response != 'y':
            logger.info("Processing cancelled by user")
            return
        
        # Process documents
        results = {'successful': [], 'failed': [], 'total_files': len(pending_docs)}
        
        for i, doc in enumerate(pending_docs):
            logger.info(f"\n[{i+1}/{len(pending_docs)}] Processing remaining stages: {doc['filename']}")
            
            result = await pipeline.process_document_remaining_stages(
                doc['id'], doc['filename'], doc['file_path']
            )
            
            if result['success']:
                results['successful'].append(result)
                logger.info(f"✅ Successfully processed: {result['filename']}")
                if 'images' in result:
                    logger.info(f"   Images: {result['images']}")
                if 'chunks' in result:
                    logger.info(f"   Chunks: {result['chunks']}")
            else:
                results['failed'].append(result)
                logger.error(f"❌ Failed to process: {result.get('filename', 'Unknown')} - {result.get('error', 'Unknown error')}")
        
        # Calculate success rate
        results['success_rate'] = len(results['successful']) / len(pending_docs) * 100
        
        # Print summary
        print("\n" + "="*80)
        print("REMAINING STAGES PROCESSING SUMMARY")
        print("="*80)
        print(f"Total Documents: {results['total_files']}")
        print(f"Successful: {len(results['successful'])}")
        print(f"Failed: {len(results['failed'])}")
        print(f"Success Rate: {results['success_rate']:.1f}%")
        print("="*80)
        
        if results['failed']:
            print("\nFAILED DOCUMENTS:")
            for result in results['failed']:
                print(f"  - {result.get('filename', 'Unknown')}: {result.get('error', 'Unknown error')}")
        
        logger.info("Remaining stages processing completed!")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
