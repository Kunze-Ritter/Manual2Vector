#!/usr/bin/env python3
"""
Direct Service Manuals Processing Script
Verarbeitet alle Service Manuals direkt über die KR-AI-Engine Services
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")
    pass

# Import KR-AI-Engine services
from services.database_service import DatabaseService
from services.object_storage_service import ObjectStorageService
from services.ai_service import AIService
from services.config_service import ConfigService
from services.features_service import FeaturesService

# Import processors
from processors.upload_processor import UploadProcessor
from processors.text_processor import TextProcessor
from processors.image_processor import ImageProcessor
from processors.classification_processor import ClassificationProcessor
from processors.metadata_processor import MetadataProcessor
from processors.storage_processor import StorageProcessor
from processors.embedding_processor import EmbeddingProcessor

# Import data models
from core.data_models import DocumentModel, DocumentType
from core.base_processor import ProcessingContext

class DirectServiceManualProcessor:
    """Verarbeitet Service Manuals direkt über die KR-AI-Engine Services"""
    
    def __init__(self):
        self.database_service = None
        self.storage_service = None
        self.ai_service = None
        self.config_service = None
        self.features_service = None
        
        # Processors
        self.upload_processor = None
        self.text_processor = None
        self.image_processor = None
        self.classification_processor = None
        self.metadata_processor = None
        self.storage_processor = None
        self.embedding_processor = None
        
        self.processed_files = []
        self.failed_files = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("krai.direct_processor")
    
    async def initialize_services(self):
        """Initialisiert alle Services"""
        print("🚀 Initializing KR-AI-Engine Services...")
        
        try:
            # Initialize configuration service
            self.config_service = ConfigService()
            print("✅ Configuration service initialized")
            
            # Initialize database service
            self.database_service = DatabaseService(
                supabase_url=os.getenv("SUPABASE_URL"),
                supabase_key=os.getenv("SUPABASE_ANON_KEY")
            )
            await self.database_service.connect()
            print("✅ Database service connected")
            
            # Initialize object storage service
            self.storage_service = ObjectStorageService(
                r2_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
                r2_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
                r2_endpoint_url=os.getenv("R2_ENDPOINT_URL"),
                r2_public_url_documents=os.getenv("R2_PUBLIC_URL_DOCUMENTS"),
                r2_public_url_error=os.getenv("R2_PUBLIC_URL_ERROR"),
                r2_public_url_parts=os.getenv("R2_PUBLIC_URL_PARTS")
            )
            await self.storage_service.connect()
            print("✅ Object storage service connected")
            
            # Initialize AI service
            self.ai_service = AIService(
                ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434")
            )
            await self.ai_service.connect()
            print("✅ AI service connected")
            
            # Initialize features service
            self.features_service = FeaturesService(self.ai_service, self.database_service)
            print("✅ Features service initialized")
            
            # Initialize processors
            self.upload_processor = UploadProcessor(self.database_service)
            self.text_processor = TextProcessor(self.database_service, self.config_service)
            self.image_processor = ImageProcessor(self.database_service, self.storage_service, self.ai_service)
            self.classification_processor = ClassificationProcessor(self.database_service, self.ai_service, self.features_service)
            self.metadata_processor = MetadataProcessor(self.database_service, self.config_service)
            self.storage_processor = StorageProcessor(self.database_service, self.storage_service)
            self.embedding_processor = EmbeddingProcessor(self.database_service, self.ai_service)
            
            print("✅ All processors initialized")
            print("🎯 KR-AI-Engine ready for processing!")
            
        except Exception as e:
            print(f"❌ Service initialization failed: {e}")
            raise
    
    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Verarbeitet ein einzelnes Dokument durch die komplette Pipeline"""
        try:
            print(f"📄 Processing: {os.path.basename(file_path)}")
            
            # Create processing context
            context = ProcessingContext(
                document_id="",  # Will be set by upload processor
                file_path=file_path,
                file_hash="",  # Will be calculated by upload processor
                document_type=DocumentType.SERVICE_MANUAL,
                language="en",
                processing_config={"filename": os.path.basename(file_path)}  # Add filename to processing_config
            )
            
            # Add filename attribute to context for upload processor
            context.filename = os.path.basename(file_path)
            
            # Stage 1: Upload Processor
            print(f"  📤 Stage 1: Upload Processor")
            upload_result = await self.upload_processor.safe_process(context)
            if not upload_result.success:
                raise Exception(f"Upload failed: {upload_result.error}")
            
            document_id = upload_result.data.get('document_id')
            context.document_id = document_id
            print(f"  ✅ Document uploaded: {document_id}")
            
            # Stage 2: Text Processor
            print(f"  📄 Stage 2: Text Processor")
            text_result = await self.text_processor.safe_process(context)
            if not text_result.success:
                print(f"  ⚠️ Text processing failed: {text_result.error}")
            else:
                print(f"  ✅ Text extracted and chunked")
            
            # Stage 3: Image Processor
            print(f"  🖼️ Stage 3: Image Processor")
            image_result = await self.image_processor.safe_process(context)
            if not image_result.success:
                print(f"  ⚠️ Image processing failed: {image_result.error}")
            else:
                print(f"  ✅ Images extracted and stored")
            
            # Stage 4: Classification Processor
            print(f"  🏷️ Stage 4: Classification Processor")
            classification_result = await self.classification_processor.safe_process(context)
            if not classification_result.success:
                print(f"  ⚠️ Classification failed: {classification_result.error}")
            else:
                print(f"  ✅ Document classified")
            
            # Stage 5: Metadata Processor
            print(f"  📑 Stage 5: Metadata Processor")
            metadata_result = await self.metadata_processor.safe_process(context)
            if not metadata_result.success:
                print(f"  ⚠️ Metadata processing failed: {metadata_result.error}")
            else:
                print(f"  ✅ Metadata extracted")
            
            # Stage 6: Storage Processor
            print(f"  💾 Stage 6: Storage Processor")
            storage_result = await self.storage_processor.safe_process(context)
            if not storage_result.success:
                print(f"  ⚠️ Storage processing failed: {storage_result.error}")
            else:
                print(f"  ✅ Storage processing completed")
            
            # Stage 7: Embedding Processor
            print(f"  🔮 Stage 7: Embedding Processor")
            embedding_result = await self.embedding_processor.safe_process(context)
            if not embedding_result.success:
                print(f"  ⚠️ Embedding processing failed: {embedding_result.error}")
            else:
                print(f"  ✅ Embeddings generated")
            
            print(f"✅ Successfully processed: {os.path.basename(file_path)}")
            return {
                "file": file_path,
                "document_id": document_id,
                "status": "completed",
                "results": {
                    "upload": upload_result.success,
                    "text": text_result.success,
                    "image": image_result.success,
                    "classification": classification_result.success,
                    "metadata": metadata_result.success,
                    "storage": storage_result.success,
                    "embedding": embedding_result.success
                }
            }
            
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            return {
                "file": file_path,
                "status": "failed",
                "error": str(e)
            }
    
    async def process_directory(self, directory_path: str) -> Dict[str, Any]:
        """Verarbeitet alle PDFs in einem Verzeichnis"""
        print(f"🔍 Scanning directory: {directory_path}")
        
        # Find all PDF files
        pdf_files = []
        for file in os.listdir(directory_path):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(directory_path, file))
        
        print(f"📄 Found {len(pdf_files)} PDF files")
        
        if not pdf_files:
            return {"error": "No PDF files found"}
        
        # Initialize services
        await self.initialize_services()
        
        # Process each file
        for i, file_path in enumerate(pdf_files, 1):
            print(f"\n📋 Processing {i}/{len(pdf_files)}: {os.path.basename(file_path)}")
            
            result = await self.process_document(file_path)
            
            if result["status"] == "completed":
                self.processed_files.append(result)
                print(f"✅ Successfully processed: {os.path.basename(file_path)}")
            else:
                self.failed_files.append(result)
                print(f"❌ Failed to process: {os.path.basename(file_path)}")
            
            # Small delay between files
            await asyncio.sleep(1)
        
        return {
            "total_files": len(pdf_files),
            "processed": len(self.processed_files),
            "failed": len(self.failed_files),
            "processed_files": self.processed_files,
            "failed_files": self.failed_files
        }
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Gibt eine Zusammenfassung der Verarbeitung zurück"""
        return {
            "processed_count": len(self.processed_files),
            "failed_count": len(self.failed_files),
            "success_rate": len(self.processed_files) / (len(self.processed_files) + len(self.failed_files)) * 100 if (len(self.processed_files) + len(self.failed_files)) > 0 else 0,
            "processed_files": [f["file"] for f in self.processed_files],
            "failed_files": [f["file"] for f in self.failed_files]
        }

async def main():
    """Hauptfunktion"""
    print("🚀 KR-AI-Engine Direct Service Manuals Processor")
    print("=" * 60)
    
    # Service Manuals Verzeichnis
    service_manuals_dir = r"C:\Users\haast\Downloads\Office Printing\Service Manuals"
    
    if not os.path.exists(service_manuals_dir):
        print(f"❌ Directory not found: {service_manuals_dir}")
        return
    
    # Processor initialisieren
    processor = DirectServiceManualProcessor()
    
    # Verzeichnis verarbeiten
    print(f"📁 Processing directory: {service_manuals_dir}")
    results = await processor.process_directory(service_manuals_dir)
    
    # Ergebnisse anzeigen
    print("\n" + "=" * 60)
    print("📊 PROCESSING SUMMARY")
    print("=" * 60)
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print(f"📄 Total files: {results['total_files']}")
    print(f"✅ Processed: {results['processed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📈 Success rate: {results['processed'] / results['total_files'] * 100:.1f}%")
    
    if results['processed'] > 0:
        print(f"\n✅ Successfully processed files:")
        for file_info in results['processed_files']:
            print(f"   - {os.path.basename(file_info['file'])} (ID: {file_info['document_id']})")
            results_summary = file_info.get('results', {})
            stages = []
            for stage, success in results_summary.items():
                stages.append(f"{stage}: {'✅' if success else '❌'}")
            print(f"     Stages: {', '.join(stages)}")
    
    if results['failed'] > 0:
        print(f"\n❌ Failed files:")
        for file_info in results['failed_files']:
            print(f"   - {os.path.basename(file_info['file'])}: {file_info.get('error', 'Unknown error')}")
    
    print(f"\n🎯 Processing complete!")
    print(f"📊 All documents processed through KR-AI-Engine pipeline")

if __name__ == "__main__":
    asyncio.run(main())
