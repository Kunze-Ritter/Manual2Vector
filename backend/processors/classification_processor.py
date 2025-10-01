"""
Classification Processor for KR-AI-Engine
Stage 4: Document classification and features extraction
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult, ProcessingError
from core.data_models import ManufacturerModel, ProductSeriesModel, ProductModel, DocumentType
from services.database_service import DatabaseService
from services.ai_service import AIService
from services.features_service import FeaturesService
from services.manufacturer_normalization import ManufacturerNormalizationService, ModelDetectionService

class ClassificationProcessor(BaseProcessor):
    """
    Classification Processor - Stage 4 of the processing pipeline
    
    Responsibilities:
    - Document type classification
    - Manufacturer detection
    - Product series and model identification
    - Features extraction (Serie + Produkt)
    
    Output: krai_core.manufacturers, krai_core.products, krai_core.product_series
    """
    
    def __init__(self, 
                 database_service: DatabaseService, 
                 ai_service: AIService,
                 features_service: FeaturesService = None):
        super().__init__("classification_processor")
        self.database_service = database_service
        self.ai_service = ai_service
        self.features_service = features_service
        
        # Initialize normalization services
        self.manufacturer_normalizer = ManufacturerNormalizationService()
        self.model_detector = ModelDetectionService()
    
    def get_required_inputs(self) -> List[str]:
        """Get required inputs for classification processor"""
        return ['document_id', 'file_path', 'filename']
    
    def get_outputs(self) -> List[str]:
        """Get outputs from classification processor"""
        return ['manufacturer_id', 'series_id', 'product_id', 'classification_result']
    
    def get_output_tables(self) -> List[str]:
        """Get database tables this processor writes to"""
        return ['krai_core.manufacturers', 'krai_core.products', 'krai_core.product_series']
    
    def get_dependencies(self) -> List[str]:
        """Get processor dependencies"""
        return ['upload_processor', 'text_processor']
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        """Get resource requirements for classification processor"""
        return {
            'cpu_intensive': True,
            'memory_intensive': False,
            'gpu_required': True,
            'estimated_ram_gb': 3.0,
            'estimated_gpu_gb': 2.0,
            'parallel_safe': True
        }
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Process document classification and features extraction
        
        Args:
            context: Processing context with document information
            
        Returns:
            ProcessingResult: Classification processing result
        """
        try:
            # Get document info
            document = await self.database_service.get_document(context.document_id)
            if not document:
                raise ProcessingError(
                    f"Document not found: {context.document_id}",
                    self.name,
                    "DOCUMENT_NOT_FOUND"
                )
            
            # Read document text for classification
            self.logger.info(f"Classification processing for document {context.document_id}")
            self.logger.info(f"File path: {context.file_path}")
            document_text = self._extract_document_text(context.file_path)
            
            # If no PDF text available, use chunks from database
            if not document_text:
                self.logger.info(f"PDF not available for {context.document_id}, using chunks for classification")
                chunks = await self.database_service.get_chunks_by_document_id(context.document_id)
                if chunks:
                    # Combine first few chunks for classification
                    document_text = "\n".join([chunk.content[:500] for chunk in chunks[:5]])
                    self.logger.info(f"Using {len(chunks)} chunks for classification")
                else:
                    self.logger.warning(f"No chunks found for document {context.document_id}")
                    document_text = ""
            
            # AI-powered document classification
            filename = context.processing_config.get('filename', 'Unknown')
            if not filename or filename == 'Unknown':
                filename = document.filename if hasattr(document, 'filename') else 'Unknown'
            
            classification_result = await self.ai_service.classify_document(
                text=document_text,
                filename=filename
            )
            
            # Normalize manufacturer name to prevent duplicates
            raw_manufacturer = classification_result.get('manufacturer', 'Unknown')
            normalized_manufacturer = self.manufacturer_normalizer.normalize_manufacturer_name(raw_manufacturer)
            classification_result['manufacturer'] = normalized_manufacturer
            
            # Extract all models from document text (not just AI result)
            ai_models = classification_result.get('models', [])
            detected_models = self.model_detector.extract_all_models(document_text, normalized_manufacturer)
            
            # Combine AI models with detected models
            all_models = list(set(ai_models + detected_models))
            classification_result['models'] = all_models
            
            # Extract series if not detected by AI
            if not classification_result.get('series') or classification_result.get('series') == 'Unknown':
                detected_series = self.model_detector.extract_series(document_text, normalized_manufacturer)
                classification_result['series'] = detected_series
            
            # Create or get manufacturer
            manufacturer_id = await self._create_or_get_manufacturer(
                classification_result['manufacturer']
            )
            
            # Create or get product series
            series_id = await self._create_or_get_product_series(
                manufacturer_id,
                classification_result['series'],
                classification_result
            )
            
            # Create or get products
            product_ids = await self._create_or_get_products(
                manufacturer_id,
                series_id,
                classification_result['models'],
                classification_result
            )
            
            # Extract features
            features_result = await self.features_service.extract_features(
                document_text,
                classification_result['manufacturer'],
                classification_result['series']
            )
            
            # Update document with classification results
            await self.database_service.update_document(
                context.document_id,
                {
                    'manufacturer': classification_result['manufacturer'],
                    'series': classification_result['series'],
                    'models': classification_result['models'],
                    'version': classification_result['version'],
                    'language': classification_result['language']
                }
            )
            
            # Log audit event
            await self.database_service.log_audit(
                action="document_classified",
                entity_type="document",
                entity_id=context.document_id,
                details={
                    'manufacturer': classification_result['manufacturer'],
                    'series': classification_result['series'],
                    'models': classification_result['models'],
                    'confidence': classification_result['confidence'],
                    'features_extracted': bool(features_result)
                }
            )
            
            # Return success result
            data = {
                'manufacturer_id': manufacturer_id,
                'series_id': series_id,
                'product_id': product_ids[0] if product_ids else None,
                'classification_result': classification_result,
                'features_result': features_result
            }
            
            metadata = {
                'confidence': classification_result['confidence'],
                'processing_timestamp': datetime.utcnow().isoformat(),
                'ai_model_used': 'llama3.2:latest'
            }
            
            return self.create_success_result(data, metadata)
            
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            else:
                raise ProcessingError(
                    f"Classification processing failed: {str(e)}",
                    self.name,
                    "CLASSIFICATION_FAILED"
                )
    
    def _extract_document_text(self, file_path: str) -> str:
        """Extract text from document for classification"""
        try:
            # Check if file exists
            if not file_path or not os.path.exists(file_path):
                self.logger.warning(f"File not found: {file_path}, using document chunks for classification")
                return ""
            
            try:
                import fitz
                
                doc = fitz.open(file_path)
                text_content = ""
                
                # Extract text from first few pages for classification
                for page_num in range(min(3, len(doc))):
                    page = doc.load_page(page_num)
                    text_content += page.get_text() + "\n"
                
                doc.close()
                return text_content[:5000]  # Limit for classification
                
            except ImportError:
                self.logger.error("PyMuPDF not available - cannot extract text from PDF")
                return ""
            
        except Exception as e:
            self.logger.error(f"Failed to extract document text: {e}")
            return ""
    
    async def _create_or_get_manufacturer(self, manufacturer_name: str) -> str:
        """Create or get manufacturer with normalization"""
        try:
            # Manufacturer name is already normalized at this point
            # Check if manufacturer exists
            existing_manufacturer = await self.database_service.get_manufacturer_by_name(manufacturer_name)
            if existing_manufacturer:
                self.logger.info(f"Found existing manufacturer: {manufacturer_name}")
                return existing_manufacturer['id']
            
            # Create new manufacturer
            manufacturer = ManufacturerModel(
                name=manufacturer_name,
                description=f"Manufacturer: {manufacturer_name}"
            )
            
            manufacturer_id = await self.database_service.create_manufacturer(manufacturer)
            self.logger.info(f"Created new manufacturer: {manufacturer_name}")
            return manufacturer_id
            
        except Exception as e:
            self.logger.error(f"Failed to create/get manufacturer {manufacturer_name}: {e}")
            raise
    
    async def _create_or_get_product_series(self, 
                                         manufacturer_id: str, 
                                         series_name: str, 
                                         classification_result: Dict[str, Any]) -> str:
        """Create or get product series"""
        try:
            # Check if series exists
            existing_series = await self.database_service.get_product_series_by_name(
                series_name, manufacturer_id
            )
            if existing_series:
                return existing_series.id
            
            # Create new product series
            series = ProductSeriesModel(
                manufacturer_id=manufacturer_id,
                series_name=series_name,
                series_code=series_name.upper().replace(' ', '_'),
                target_market=classification_result.get('target_market', 'Unknown'),
                price_range=classification_result.get('price_range', 'Unknown'),
                key_features=classification_result.get('key_features', {}),
                series_description=f"Product series: {series_name}"
            )
            
            series_id = await self.database_service.create_product_series(series)
            self.logger.info(f"Created product series: {series_name}")
            return series_id
            
        except Exception as e:
            self.logger.error(f"Failed to create/get product series {series_name}: {e}")
            raise
    
    async def _create_or_get_products(self, 
                                    manufacturer_id: str, 
                                    series_id: str, 
                                    models: List[str], 
                                    classification_result: Dict[str, Any]) -> List[str]:
        """Create or get products for ALL detected models"""
        try:
            product_ids = []
            
            self.logger.info(f"Creating products for {len(models)} models: {models}")
            
            for model in models:
                if not model or model.strip() == "":
                    continue
                    
                # Check if product exists
                existing_product = await self.database_service.get_product_by_model(
                    model, manufacturer_id
                )
                if existing_product:
                    self.logger.info(f"Found existing product: {model}")
                    product_ids.append(existing_product['id'])
                    continue
                
                # Create new product
                product = ProductModel(
                    manufacturer_id=manufacturer_id,
                    series_id=series_id,
                    model_number=model,
                    model_name=model,
                    product_type=classification_result.get('document_type', 'printer')
                )
                
                product_id = await self.database_service.create_product(product)
                product_ids.append(product_id)
                self.logger.info(f"Created new product: {model}")
            
            self.logger.info(f"Total products created/found: {len(product_ids)}")
            return product_ids
            
        except Exception as e:
            self.logger.error(f"Failed to create/get products: {e}")
            raise
