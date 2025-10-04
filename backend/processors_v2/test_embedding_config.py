#!/usr/bin/env python3
"""
Test Embedding Configuration

Quick test to check if embeddings are properly configured.
Run this before processing documents to verify setup.

Usage:
    python test_embedding_config.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors_v2.embedding_processor import EmbeddingProcessor
from processors_v2.logger import get_logger


def main():
    logger = get_logger()
    
    logger.info("=" * 70)
    logger.info("🔍 TESTING EMBEDDING CONFIGURATION")
    logger.info("=" * 70)
    
    # Initialize processor
    processor = EmbeddingProcessor()
    
    # Get detailed status
    status = processor.get_configuration_status()
    
    logger.info("\n📊 Configuration Status:")
    logger.info("-" * 70)
    logger.info(f"  ✓ Is Configured: {status['is_configured']}")
    logger.info(f"  ✓ Ollama Available: {status['ollama_available']}")
    logger.info(f"  ✓ Ollama URL: {status['ollama_url']}")
    logger.info(f"  ✓ Model Name: {status['model_name']}")
    logger.info(f"  ✓ Embedding Dimension: {status['embedding_dimension']}")
    logger.info(f"  ✓ Batch Size: {status['batch_size']}")
    logger.info(f"  ✓ Supabase Configured: {status['supabase_configured']}")
    logger.info("-" * 70)
    
    # Overall result
    if status['is_configured']:
        logger.success("\n✅ EMBEDDING PROCESSOR IS FULLY CONFIGURED!")
        logger.success("   Ready to generate embeddings for semantic search.")
        
        # Test embedding generation
        logger.info("\n🧪 Testing embedding generation...")
        test_text = "This is a test sentence for embedding generation."
        
        try:
            embedding = processor._generate_embedding(test_text)
            
            if embedding and len(embedding) == status['embedding_dimension']:
                logger.success(f"✅ Test embedding generated successfully!")
                logger.info(f"   • Dimension: {len(embedding)}")
                logger.info(f"   • Sample values: {embedding[:3]}")
                return 0
            else:
                logger.error("❌ Test embedding failed - invalid dimension")
                return 1
                
        except Exception as e:
            logger.error(f"❌ Test embedding failed: {e}")
            return 1
    
    else:
        logger.error("\n❌ EMBEDDING PROCESSOR IS NOT CONFIGURED!")
        logger.error("=" * 70)
        
        # Show specific problems
        if not status['ollama_available']:
            logger.error("\n🔴 PROBLEM: Ollama is not available")
            logger.info("\n📝 SOLUTION:")
            logger.info("   1. Start Ollama service:")
            logger.info("      → ollama serve")
            logger.info("")
            logger.info(f"   2. Install the embedding model:")
            logger.info(f"      → ollama pull {status['model_name']}")
            logger.info("")
            logger.info(f"   3. Verify Ollama is running:")
            logger.info(f"      → curl {status['ollama_url']}/api/tags")
            logger.info("")
        
        if not status['supabase_configured']:
            logger.error("\n🔴 PROBLEM: Supabase client is not configured")
            logger.info("\n📝 SOLUTION:")
            logger.info("   • Make sure to pass supabase_client to EmbeddingProcessor")
            logger.info("   • Check your .env file for Supabase credentials")
            logger.info("   • Verify SUPABASE_URL and SUPABASE_KEY are set")
            logger.info("")
        
        logger.error("=" * 70)
        logger.error("⚠️  EMBEDDINGS WILL NOT WORK!")
        logger.error("⚠️  Semantic search will be DISABLED!")
        logger.error("=" * 70)
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
