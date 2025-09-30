#!/usr/bin/env python3
"""
Simple Pipeline Test with Advanced Progress Tracking
Quick test with minimal output but full progress tracking
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from advanced_progress_tracker import AdvancedProgressTracker

async def simulate_pipeline_with_progress():
    """Simulate pipeline processing with advanced progress tracking"""
    
    print(" KR-AI-Engine Simple Test with Advanced Progress Tracking")
    print("=" * 70)
    
    # Initialize progress tracker
    with AdvancedProgressTracker(total_stages=8) as tracker:
        
        # Stage 1: Upload
        tracker.start_stage(1, {
            "file": "HP_X580_SM.pdf",
            "size": "2.5 MB",
            "stage": "Document upload and validation"
        })
        await asyncio.sleep(0.5)  # Simulate work
        tracker.end_stage(1, success=True, details={
            "document_id": "doc_12345",
            "file_hash": "a1b2c3d4...",
            "document_type": "service_manual"
        })
        
        # Stage 2: Text Processing
        tracker.start_stage(2, {
            "stage": "Text extraction and chunking",
            "document_id": "doc_12345"
        })
        await asyncio.sleep(1.2)  # Simulate work
        tracker.end_stage(2, success=True, details={
            "chunks_created": 45,
            "text_length": "125,000 chars"
        })
        
        # Stage 3: Image Processing
        tracker.start_stage(3, {
            "stage": "Image extraction and AI analysis",
            "document_id": "doc_12345"
        })
        await asyncio.sleep(2.1)  # Simulate work
        tracker.end_stage(3, success=True, details={
            "images_extracted": 12,
            "ai_analysis": "completed"
        })
        
        # Stage 4: Classification
        tracker.start_stage(4, {
            "stage": "Document classification",
            "document_id": "doc_12345"
        })
        await asyncio.sleep(0.8)  # Simulate work
        tracker.end_stage(4, success=True, details={
            "manufacturer": "HP Inc.",
            "product_series": "LaserJet Pro",
            "product": "M404dn"
        })
        
        # Stage 5: Metadata
        tracker.start_stage(5, {
            "stage": "Metadata extraction",
            "document_id": "doc_12345"
        })
        await asyncio.sleep(0.6)  # Simulate work
        tracker.end_stage(5, success=True, details={
            "error_codes_found": 8,
            "metadata_extracted": "completed"
        })
        
        # Stage 6: Storage
        tracker.start_stage(6, {
            "stage": "Object storage operations",
            "document_id": "doc_12345"
        })
        await asyncio.sleep(1.5)  # Simulate work
        tracker.end_stage(6, success=True, details={
            "storage_operations": "completed",
            "images_stored": 12
        })
        
        # Stage 7: Embeddings
        tracker.start_stage(7, {
            "stage": "Vector embedding generation",
            "document_id": "doc_12345"
        })
        await asyncio.sleep(3.2)  # Simulate work
        tracker.end_stage(7, success=True, details={
            "embeddings_created": 45,
            "model": "embeddinggemma:latest"
        })
        
        # Stage 8: Search
        tracker.start_stage(8, {
            "stage": "Search index creation",
            "document_id": "doc_12345"
        })
        await asyncio.sleep(0.9)  # Simulate work
        tracker.end_stage(8, success=True, details={
            "search_index": "created",
            "analytics": "tracked"
        })
        
        # Print final summary
        tracker.print_final_summary()

if __name__ == "__main__":
    asyncio.run(simulate_pipeline_with_progress())
