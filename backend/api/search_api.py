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
            """Search error codes in database"""
            try:
                # Build query
                query = """
                SELECT 
                    ec.error_code,
                    ec.error_description as description,
                    ec.solution_text as solution,
                    ec.page_number,
                    ec.severity_level,
                    ec.confidence_score,
                    m.name as manufacturer,
                    d.filename as source_document
                FROM krai_intelligence.error_codes ec
                LEFT JOIN krai_core.manufacturers m ON ec.manufacturer_id = m.id
                LEFT JOIN krai_core.documents d ON ec.document_id = d.id
                WHERE ec.error_code ILIKE %s
                """
                
                params = [f"%{q}%"]
                
                # Add manufacturer filter if specified
                if manufacturer:
                    query += " AND m.name ILIKE %s"
                    params.append(f"%{manufacturer}%")
                
                query += " ORDER BY ec.confidence_score DESC NULLS LAST, ec.error_code LIMIT %s"
                params.append(limit)
                
                # Execute query
                result = await self.database_service.execute_query(query, params)
                
                # Format results
                error_codes = []
                for row in result:
                    error_codes.append({
                        'error_code': row['error_code'],
                        'description': row['description'],
                        'solution': row['solution'],
                        'manufacturer': row['manufacturer'],
                        'page_number': row['page_number'],
                        'severity_level': row['severity_level'],
                        'source_document': row['source_document'],
                        'confidence': float(row['confidence_score']) if row['confidence_score'] else 0.0
                    })
                
                return {
                    'query': q,
                    'error_codes': error_codes,
                    'total_count': len(error_codes),
                    'manufacturer_filter': manufacturer
                }
                
            except Exception as e:
                self.logger.error(f"Error code search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/parts")
        async def search_parts(
            q: str = Query(..., min_length=1),
            manufacturer: Optional[str] = Query(None),
            limit: int = Query(10, ge=1, le=100)
        ):
            """Search parts in database"""
            try:
                # Build query
                query = """
                SELECT 
                    p.part_number,
                    p.part_name,
                    p.description,
                    p.category,
                    p.price,
                    p.availability_status,
                    m.name as manufacturer,
                    d.filename as source_document
                FROM krai_parts.parts_catalog p
                LEFT JOIN krai_core.manufacturers m ON p.manufacturer_id = m.id
                LEFT JOIN krai_core.documents d ON p.document_id = d.id
                WHERE (p.part_number ILIKE %s OR p.part_name ILIKE %s OR p.description ILIKE %s)
                """
                
                search_pattern = f"%{q}%"
                params = [search_pattern, search_pattern, search_pattern]
                
                # Add manufacturer filter if specified
                if manufacturer:
                    query += " AND m.name ILIKE %s"
                    params.append(f"%{manufacturer}%")
                
                query += " ORDER BY p.part_number LIMIT %s"
                params.append(limit)
                
                # Execute query
                result = await self.database_service.execute_query(query, params)
                
                # Format results
                parts = []
                for row in result:
                    parts.append({
                        'part_number': row['part_number'],
                        'part_name': row['part_name'],
                        'description': row['description'],
                        'category': row['category'],
                        'price': float(row['price']) if row['price'] else None,
                        'availability': row['availability_status'],
                        'manufacturer': row['manufacturer'],
                        'source_document': row['source_document']
                    })
                
                return {
                    'query': q,
                    'parts': parts,
                    'total_count': len(parts),
                    'manufacturer_filter': manufacturer
                }
                
            except Exception as e:
                self.logger.error(f"Parts search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/videos")
        async def search_videos(
            q: str = Query(..., min_length=1),
            manufacturer: Optional[str] = Query(None),
            limit: int = Query(10, ge=1, le=100)
        ):
            """Search videos in database"""
            try:
                # Build query
                query = """
                SELECT 
                    v.video_id,
                    v.title,
                    v.description,
                    v.url,
                    v.duration,
                    v.view_count,
                    v.published_at,
                    v.channel_title,
                    m.name as manufacturer
                FROM krai_content.videos v
                LEFT JOIN krai_core.manufacturers m ON v.manufacturer_id = m.id
                WHERE (v.title ILIKE %s OR v.description ILIKE %s)
                """
                
                search_pattern = f"%{q}%"
                params = [search_pattern, search_pattern]
                
                # Add manufacturer filter if specified
                if manufacturer:
                    query += " AND m.name ILIKE %s"
                    params.append(f"%{manufacturer}%")
                
                query += " ORDER BY v.view_count DESC NULLS LAST LIMIT %s"
                params.append(limit)
                
                # Execute query
                result = await self.database_service.execute_query(query, params)
                
                # Format results
                videos = []
                for row in result:
                    videos.append({
                        'video_id': row['video_id'],
                        'title': row['title'],
                        'description': row['description'],
                        'url': row['url'],
                        'duration': row['duration'],
                        'view_count': row['view_count'],
                        'published_at': row['published_at'].isoformat() if row['published_at'] else None,
                        'channel': row['channel_title'],
                        'manufacturer': row['manufacturer']
                    })
                
                return {
                    'query': q,
                    'videos': videos,
                    'total_count': len(videos),
                    'manufacturer_filter': manufacturer
                }
                
            except Exception as e:
                self.logger.error(f"Videos search failed: {e}")
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
