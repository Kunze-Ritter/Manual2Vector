"""
Classification Processor for KR-AI-Engine
Stage 4: Document classification and features extraction
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult, ProcessingError
from core.data_models import ManufacturerModel, ProductSeriesModel, ProductModel, DocumentType
from services.database_service import DatabaseService
from services.ai_service import AIService
from services.features_service import FeaturesService

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
                 features_service: FeaturesService):
        super().__init__("classification_processor")
        self.database_service = database_service
        self.ai_service = ai_service
        self.features_service = features_service
    
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
            document_text = await self._extract_document_text(context.file_path)
            
            # AI-powered document classification
            classification_result = await self.ai_service.classify_document(
                text=document_text,
                filename=context.filename
            )
            
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
    
    async def _extract_document_text(self, file_path: str) -> str:
        """Extract text from document for classification"""
        try:
            try:
                import PyMuPDF as fitz
                
                doc = fitz.open(file_path)
                text_content = ""
                
                # Extract text from first few pages for classification
                for page_num in range(min(3, len(doc))):
                    page = doc.load_page(page_num)
                    text_content += page.get_text() + "\n"
                
                doc.close()
                return text_content[:5000]  # Limit for classification
                
            except ImportError:
                # Mock mode for testing
                self.logger.info("Using mock document text for classification")
                return "This is mock document text for testing classification. It contains technical information about printer maintenance and troubleshooting procedures."
            
        except Exception as e:
            self.logger.error(f"Failed to extract document text: {e}")
            return ""
    
    async def _create_or_get_manufacturer(self, manufacturer_name: str) -> str:
        """Create or get manufacturer"""
        try:
            # Check if manufacturer exists
            existing_manufacturer = await self.database_service.get_manufacturer_by_name(manufacturer_name)
            if existing_manufacturer:
                return existing_manufacturer.id
            
            # Create new manufacturer
            manufacturer = ManufacturerModel(
                name=manufacturer_name,
                code=manufacturer_name.upper()[:3],
                website=f"https://{manufacturer_name.lower()}.com",
                country="Unknown"
            )
            
            manufacturer_id = await self.database_service.create_manufacturer(manufacturer)
            self.logger.info(f"Created manufacturer: {manufacturer_name}")
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
        """Create or get products"""
        try:
            product_ids = []
            
            for model in models:
                # Check if product exists
                existing_product = await self.database_service.get_product_by_model(
                    model, manufacturer_id
                )
                if existing_product:
                    product_ids.append(existing_product.id)
                    continue
                
                # Create new product
                product = ProductModel(
                    manufacturer_id=manufacturer_id,
                    series_id=series_id,
                    model_number=model,
                    model_name=model,
                    product_type=classification_result.get('document_type', 'printer'),
                    duplex_capable=classification_result.get('duplex_capable', False),
                    network_capable=classification_result.get('network_capable', False),
                    mobile_print_support=classification_result.get('mobile_print_support', False),
                    energy_star_certified=classification_result.get('energy_star_certified', False)
                )
                
                product_id = await self.database_service.create_product(product)
                product_ids.append(product_id)
                self.logger.info(f"Created product: {model}")
            
            return product_ids
            
        except Exception as e:
            self.logger.error(f"Failed to create/get products: {e}")
            raise
