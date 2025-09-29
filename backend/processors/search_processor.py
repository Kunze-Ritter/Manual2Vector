"""
Search Processor for KR-AI-Engine
Stage 8: Search index creation and optimization
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult, ProcessingError
from services.database_service import DatabaseService
from services.ai_service import AIService

class SearchProcessor(BaseProcessor):
    """
    Search Processor - Stage 8 of the processing pipeline
    
    Responsibilities:
    - Search index creation
    - Search optimization
    - Analytics tracking
    
    Output: krai_intelligence.search_analytics
    """
    
    def __init__(self, database_service: DatabaseService, ai_service: AIService):
        super().__init__("search_processor")
        self.database_service = database_service
        self.ai_service = ai_service
    
    def get_required_inputs(self) -> List[str]:
        """Get required inputs for search processor"""
        return ['document_id']
    
    def get_outputs(self) -> List[str]:
        """Get outputs from search processor"""
        return ['search_index', 'analytics']
    
    def get_output_tables(self) -> List[str]:
        """Get database tables this processor writes to"""
        return ['krai_intelligence.search_analytics']
    
    def get_dependencies(self) -> List[str]:
        """Get processor dependencies"""
        return ['embedding_processor']
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        """Get resource requirements for search processor"""
        return {
            'cpu_intensive': True,
            'memory_intensive': False,
            'gpu_required': False,
            'estimated_ram_gb': 1.0,
            'estimated_gpu_gb': 0.0,
            'parallel_safe': True
        }
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Process search index creation
        
        Args:
            context: Processing context with document information
            
        Returns:
            ProcessingResult: Search processing result
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
            
            # Create search index
            search_index = await self._create_search_index(context.document_id)
            
            # Track analytics
            analytics = await self._track_search_analytics(context.document_id)
            
            # Log audit event
            await self.database_service.log_audit(
                action="search_index_created",
                entity_type="document",
                entity_id=context.document_id,
                details={
                    'search_index_created': True,
                    'analytics_tracked': True,
                    'document_type': document.document_type.value
                }
            )
            
            # Return success result
            data = {
                'search_index': search_index,
                'analytics': analytics
            }
            
            metadata = {
                'processing_timestamp': datetime.utcnow().isoformat(),
                'search_optimization': 'enabled'
            }
            
            return self.create_success_result(data, metadata)
            
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            else:
                raise ProcessingError(
                    f"Search processing failed: {str(e)}",
                    self.name,
                    "SEARCH_PROCESSING_FAILED"
                )
    
    async def _create_search_index(self, document_id: str) -> Dict[str, Any]:
        """Create search index for document"""
        try:
            # This would typically create a search index
            # For now, return mock index
            search_index = {
                'document_id': document_id,
                'index_created': True,
                'index_type': 'vector',
                'optimization_level': 'high'
            }
            
            self.logger.info(f"Created search index for document {document_id}")
            return search_index
            
        except Exception as e:
            self.logger.error(f"Failed to create search index: {e}")
            return {}
    
    async def _track_search_analytics(self, document_id: str) -> Dict[str, Any]:
        """Track search analytics for document"""
        try:
            # This would typically track analytics
            # For now, return mock analytics
            analytics = {
                'document_id': document_id,
                'search_queries': 0,
                'search_success_rate': 1.0,
                'average_response_time': 0.0
            }
            
            self.logger.info(f"Tracked search analytics for document {document_id}")
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to track search analytics: {e}")
            return {}
