"""
Pipeline Optimizer
Optimizes pipeline performance and resolves bottlenecks
"""

import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

class PipelineOptimizer:
    """Optimizes pipeline performance and resolves bottlenecks"""
    
    def __init__(self, database_service, ai_service=None, storage_service=None):
        self.database_service = database_service
        self.ai_service = ai_service
        self.storage_service = storage_service
        self.logger = logging.getLogger("krai.pipeline_optimizer")
    
    async def optimize_classification_batch(self, batch_size: int = 5):
        """Optimize classification by processing documents in batches"""
        try:
            # Find documents ready for classification
            docs_query = """
                SELECT 
                    d.id,
                    d.filename,
                    d.file_path,
                    COUNT(c.id) as chunk_count
                FROM krai_core.documents d
                LEFT JOIN krai_content.chunks c ON d.id = c.document_id
                WHERE d.manufacturer IS NULL 
                AND d.id IN (SELECT DISTINCT document_id FROM krai_content.chunks)
                GROUP BY d.id, d.filename, d.file_path
                HAVING COUNT(c.id) > 0
                ORDER BY d.created_at ASC
                LIMIT %s
            """
            
            docs_result = await self.database_service.execute_query(docs_query, [batch_size])
            
            if not docs_result:
                self.logger.info("No documents ready for classification")
                return
            
            self.logger.info(f"Processing {len(docs_result)} documents for classification")
            
            # Process documents in parallel
            tasks = []
            for doc_data in docs_result:
                task = self._classify_document_optimized(doc_data)
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successes
            success_count = sum(1 for result in results if result is True)
            self.logger.info(f"Classification batch complete: {success_count}/{len(results)} successful")
            
        except Exception as e:
            self.logger.error(f"Classification batch optimization failed: {e}")
    
    async def _classify_document_optimized(self, doc_data: Dict[str, Any]) -> bool:
        """Optimized document classification"""
        try:
            doc_id = doc_data['id']
            filename = doc_data['filename']
            
            # Get document chunks for classification
            chunks_query = """
                SELECT content, page_number, chunk_index
                FROM krai_content.chunks 
                WHERE document_id = %s
                ORDER BY page_number, chunk_index
                LIMIT 10
            """
            
            chunks_result = await self.database_service.execute_query(chunks_query, [doc_id])
            
            if not chunks_result:
                self.logger.warning(f"No chunks found for document {filename}")
                return False
            
            # Combine chunks for classification
            combined_text = "\n".join([chunk['content'] for chunk in chunks_result[:5]])  # Use first 5 chunks
            
            # Perform classification
            if self.ai_service:
                classification = await self.ai_service.classify_document(combined_text, filename)
            else:
                # Fallback classification based on filename
                classification = self._fallback_classification(filename)
            
            # Update document with classification results
            update_query = """
                UPDATE krai_core.documents 
                SET 
                    manufacturer = %s,
                    series = %s,
                    models = %s,
                    version = %s,
                    language = %s,
                    updated_at = NOW()
                WHERE id = %s
            """
            
            await self.database_service.execute_query(update_query, [
                classification.get('manufacturer'),
                classification.get('series'),
                classification.get('models', []),
                classification.get('version'),
                classification.get('language', 'en'),
                doc_id
            ])
            
            self.logger.info(f"Successfully classified document {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to classify document {doc_data.get('filename', 'unknown')}: {e}")
            return False
    
    def _fallback_classification(self, filename: str) -> Dict[str, Any]:
        """Fallback classification based on filename patterns"""
        filename_lower = filename.lower()
        
        # Manufacturer detection
        manufacturer = "Unknown"
        if "hp" in filename_lower:
            manufacturer = "HP Inc."
        elif "konica" in filename_lower or "bizhub" in filename_lower:
            manufacturer = "Konica Minolta"
        elif "utax" in filename_lower:
            manufacturer = "UTAX"
        elif "canon" in filename_lower:
            manufacturer = "Canon Inc."
        
        # Document type detection
        document_type = "service_manual"
        if "troubleshoot" in filename_lower:
            document_type = "troubleshooting_guide"
        elif "parts" in filename_lower:
            document_type = "parts_catalog"
        
        # Model extraction (simplified)
        models = []
        import re
        model_patterns = [
            r'[A-Z]\d{3,4}[A-Z]?\d*',  # HP models like E776, E55040
            r'[A-Z]{2,4}\d{3,4}',      # UTAX models like P4531MFP
            r'bizhub_[A-Z]\d+',        # Bizhub models
        ]
        
        for pattern in model_patterns:
            matches = re.findall(pattern, filename)
            models.extend(matches)
        
        return {
            'manufacturer': manufacturer,
            'series': manufacturer,
            'models': models[:3],  # Limit to 3 models
            'version': None,
            'language': 'en',
            'document_type': document_type,
            'confidence': 0.7
        }
    
    async def optimize_image_processing_batch(self, batch_size: int = 3):
        """Optimize image processing by batching small images"""
        try:
            # Find documents with images but no processing
            docs_query = """
                SELECT 
                    d.id,
                    d.filename,
                    d.file_path
                FROM krai_core.documents d
                WHERE d.id IN (
                    SELECT DISTINCT document_id 
                    FROM krai_content.images 
                    WHERE ai_description IS NULL OR ai_description = ''
                )
                LIMIT %s
            """
            
            docs_result = await self.database_service.execute_query(docs_query, [batch_size])
            
            if not docs_result:
                self.logger.info("No documents need image processing optimization")
                return
            
            self.logger.info(f"Optimizing image processing for {len(docs_result)} documents")
            
            # Process images in parallel
            tasks = []
            for doc_data in docs_result:
                task = self._process_document_images_optimized(doc_data)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for result in results if result is True)
            self.logger.info(f"Image processing batch complete: {success_count}/{len(results)} successful")
            
        except Exception as e:
            self.logger.error(f"Image processing batch optimization failed: {e}")
    
    async def _process_document_images_optimized(self, doc_data: Dict[str, Any]) -> bool:
        """Optimized image processing for a document"""
        try:
            doc_id = doc_data['id']
            
            # Get unprocessed images
            images_query = """
                SELECT id, filename, content
                FROM krai_content.images 
                WHERE document_id = %s 
                AND (ai_description IS NULL OR ai_description = '')
                LIMIT 10
            """
            
            images_result = await self.database_service.execute_query(images_query, [doc_id])
            
            if not images_result:
                return True  # No images to process
            
            # Process images in parallel
            tasks = []
            for image_data in images_result:
                task = self._process_single_image_optimized(image_data)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for result in results if result is True)
            self.logger.info(f"Processed {success_count}/{len(results)} images for document {doc_data['filename']}")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to process images for document {doc_data.get('filename', 'unknown')}: {e}")
            return False
    
    async def _process_single_image_optimized(self, image_data: Dict[str, Any]) -> bool:
        """Optimized processing of a single image"""
        try:
            image_id = image_data['id']
            
            # Simple AI analysis (can be optimized further)
            if self.ai_service:
                ai_analysis = await self.ai_service.analyze_image(
                    image_data['content'],
                    "Technical diagram or illustration"
                )
            else:
                # Fallback analysis
                ai_analysis = {
                    'image_type': 'diagram',
                    'description': 'Technical image',
                    'confidence': 0.6,
                    'contains_text': False,
                    'tags': ['technical']
                }
            
            # Update image with AI analysis
            update_query = """
                UPDATE krai_content.images 
                SET 
                    ai_description = %s,
                    ai_confidence = %s,
                    image_type = %s,
                    tags = %s,
                    updated_at = NOW()
                WHERE id = %s
            """
            
            await self.database_service.execute_query(update_query, [
                ai_analysis.get('description', ''),
                ai_analysis.get('confidence', 0.5),
                ai_analysis.get('image_type', 'diagram'),
                ai_analysis.get('tags', []),
                image_id
            ])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to process image {image_data.get('filename', 'unknown')}: {e}")
            return False
    
    async def run_optimization_cycle(self):
        """Run a complete optimization cycle"""
        self.logger.info("🚀 Starting pipeline optimization cycle")
        
        try:
            # Step 1: Optimize classification
            await self.optimize_classification_batch(batch_size=5)
            
            # Small delay between optimization steps
            await asyncio.sleep(2)
            
            # Step 2: Optimize image processing
            await self.optimize_image_processing_batch(batch_size=3)
            
            self.logger.info("✅ Optimization cycle complete")
            
        except Exception as e:
            self.logger.error(f"Optimization cycle failed: {e}")
