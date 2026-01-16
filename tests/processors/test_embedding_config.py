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
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.processors.embedding_processor import EmbeddingProcessor
from backend.processors.logger import get_logger
from backend.services.database_adapter import create_database_adapter


def main():
    logger = get_logger()
    
    logger.info("=" * 70)
    logger.info("🔍 TESTING EMBEDDING CONFIGURATION")
    logger.info("=" * 70)
    
    # Load environment variables
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        logger.info(f"\n📄 Loading .env from: {env_path}")
        load_dotenv(env_path)
    else:
        logger.warning(f"\n⚠️  No .env file found at: {env_path}")
    
    # Initialize database adapter
    database_adapter = None
    logger.info("\n🔑 Checking database connection...")
    
    try:
        database_adapter = create_database_adapter()
        logger.success("✅ Database adapter created successfully")
        
        # Test connection
        try:
            result = database_adapter.select("krai_core.documents", columns=["id"], limit=1)
            logger.success("✅ Database connection verified (can query database)")
        except Exception as e:
            logger.warning(f"⚠️  Database adapter created but query failed: {e}")
            logger.info("   → This might be OK if tables don't exist yet")
    except Exception as e:
        logger.error(f"❌ Failed to create database adapter: {e}")
    
    # Initialize processor with database adapter
    processor = EmbeddingProcessor(database_adapter=database_adapter)
    
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
    logger.info(f"  ✓ Database Configured: {status['supabase_configured']}")
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
            logger.error("\n🔴 PROBLEM: Database adapter is not configured")
            logger.info("\n📝 SOLUTION:")
            logger.info("   • Make sure to pass database_adapter to EmbeddingProcessor")
            logger.info("   • Check your .env file for database credentials")
            logger.info("   • Verify DATABASE_URL and DATABASE_SERVICE_KEY are set")
            logger.info("")
        
        logger.error("=" * 70)
        logger.error("⚠️  EMBEDDINGS WILL NOT WORK!")
        logger.error("⚠️  Semantic search will be DISABLED!")
        logger.error("=" * 70)
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
