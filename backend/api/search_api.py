"""
Search API for KR-AI-Engine
FastAPI endpoints for semantic search and vector operations
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime

from core.data_models import SearchRequest, SearchResponse
from services.database_service import DatabaseService
from services.ai_service import AIService

class SearchAPI:
    """
    Search API for KR-AI-Engine
    
    Endpoints:
    - POST /search: Semantic search
    - GET /search/suggestions: Search suggestions
    - POST /search/vector: Vector similarity search
    - GET /search/error-codes: Search error codes
    """
    
    def __init__(self, database_service: DatabaseService, ai_service: AIService):
        self.database_service = database_service
        self.ai_service = ai_service
        self.logger = logging.getLogger("krai.api.search")
        self._setup_logging()
        
        # Create router
        self.router = APIRouter(prefix="/search", tags=["search"])
        self._setup_routes()
    
    def _setup_logging(self):
        """Setup logging for search API"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - SearchAPI - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.router.post("/", response_model=SearchResponse)
        async def semantic_search(request: SearchRequest):
            """Perform semantic search"""
            try:
                start_time = datetime.utcnow()
                
                # Generate query embedding
                query_embedding = await self.ai_service.generate_embeddings(request.query)
                
                # Perform vector search
                search_results = await self.database_service.vector_search(
                    query_embedding,
                    limit=request.limit,
                    threshold=0.7
                )
                
                # Process results
                processed_results = []
                for result in search_results:
                    processed_result = {
                        'chunk_id': result.get('id'),
                        'document_id': result.get('document_id'),
                        'content': result.get('text_chunk', ''),
                        'similarity_score': result.get('similarity', 0.0),
                        'page_start': result.get('page_start', 0),
                        'page_end': result.get('page_end', 0),
                        'metadata': result.get('metadata', {})
                    }
                    processed_results.append(processed_result)
                
                # Filter by document types if specified
                if request.document_types:
                    # This would typically filter results by document type
                    pass
                
                # Filter by manufacturers if specified
                if request.manufacturers:
                    # This would typically filter results by manufacturer
                    pass
                
                # Filter by models if specified
                if request.models:
                    # This would typically filter results by model
                    pass
                
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Log search analytics
                await self.database_service.log_audit(
                    action="semantic_search",
                    entity_type="search",
                    entity_id="",
                    details={
                        'query': request.query,
                        'results_count': len(processed_results),
                        'processing_time_ms': processing_time,
                        'filters': {
                            'document_types': request.document_types,
                            'manufacturers': request.manufacturers,
                            'models': request.models
                        }
                    }
                )
                
                return SearchResponse(
                    results=processed_results,
                    total_count=len(processed_results),
                    processing_time_ms=processing_time,
                    query=request.query
                )
                
            except Exception as e:
                self.logger.error(f"Semantic search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/suggestions")
        async def get_search_suggestions(q: str = Query(..., min_length=2)):
            """Get search suggestions"""
            try:
                # This would typically query a suggestions index
                # For now, return placeholder suggestions
                suggestions = [
                    f"{q} error codes",
                    f"{q} troubleshooting",
                    f"{q} service manual",
                    f"{q} parts catalog"
                ]
                
                return {
                    'query': q,
                    'suggestions': suggestions
                }
                
            except Exception as e:
                self.logger.error(f"Failed to get search suggestions: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/vector")
        async def vector_similarity_search(
            query: str,
            limit: int = Query(10, ge=1, le=100),
            threshold: float = Query(0.7, ge=0.0, le=1.0)
        ):
            """Perform vector similarity search"""
            try:
                start_time = datetime.utcnow()
                
                # Generate query embedding
                query_embedding = await self.ai_service.generate_embeddings(query)
                
                # Perform vector search
                search_results = await self.database_service.vector_search(
                    query_embedding,
                    limit=limit,
                    threshold=threshold
                )
                
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                return {
                    'query': query,
                    'results': search_results,
                    'total_count': len(search_results),
                    'processing_time_ms': processing_time,
                    'threshold': threshold
                }
                
            except Exception as e:
                self.logger.error(f"Vector search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/error-codes")
        async def search_error_codes(
            q: str = Query(..., min_length=1),
            manufacturer: Optional[str] = Query(None),
            limit: int = Query(10, ge=1, le=100)
        ):
            """Search error codes"""
            try:
                # This would typically query the error_codes table
                # For now, return placeholder results
                error_codes = [
                    {
                        'error_code': '13.20.01',
                        'description': 'Paper jam in duplex unit',
                        'solution': 'Clear paper jam from duplex unit',
                        'manufacturer': 'HP',
                        'confidence': 0.95
                    },
                    {
                        'error_code': 'C2557',
                        'description': 'Toner cartridge error',
                        'solution': 'Replace toner cartridge',
                        'manufacturer': 'Konica Minolta',
                        'confidence': 0.90
                    }
                ]
                
                # Filter by manufacturer if specified
                if manufacturer:
                    error_codes = [ec for ec in error_codes if ec['manufacturer'].lower() == manufacturer.lower()]
                
                return {
                    'query': q,
                    'error_codes': error_codes[:limit],
                    'total_count': len(error_codes),
                    'manufacturer_filter': manufacturer
                }
                
            except Exception as e:
                self.logger.error(f"Error code search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/health")
        async def search_health_check():
            """Search service health check"""
            try:
                # Test AI service
                ai_health = await self.ai_service.health_check()
                
                # Test database service
                db_health = await self.database_service.health_check()
                
                return {
                    'status': 'healthy' if ai_health['status'] == 'healthy' and db_health['status'] == 'healthy' else 'degraded',
                    'ai_service': ai_health,
                    'database_service': db_health,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                return {
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
