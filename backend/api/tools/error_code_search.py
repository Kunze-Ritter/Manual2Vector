"""
Multi-Source Error Code Search Tool
==================================
FastAPI endpoint for the search_error_code_multi_source tool.

Implements the exact response format specified in Agent System Message V2.4.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List

from supabase import Client, create_client

from backend.api.check_error_code_in_db import normalize_error_code
from backend.api.check_db_schema import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL

logger = logging.getLogger(__name__)

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.processors.env_loader import load_all_env_files

load_all_env_files(project_root)

logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class ErrorCodeSearchRequest(BaseModel):
    """Request model for error code search"""
    error_code: str = Field(..., description="Error code to search for")
    manufacturer: str = Field(..., description="Manufacturer name")
    product: Optional[str] = Field(None, description="Product model/series")


class ErrorCodeSearchResponse(BaseModel):
    """Response model for error code search"""
    found: bool
    message: Optional[str] = None
    error_code: Optional[str] = None
    description: Optional[str] = None
    documents: Optional[List[Dict]] = None
    videos: Optional[List[Dict]] = None
    parts: Optional[List[str]] = None


# ============================================================================
# Multi-Source Search Logic
# ============================================================================

class MultiSourceErrorCodeSearch:
    """Multi-source error code search implementation"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.logger = logging.getLogger(__name__)
    
    async def search_error_code(
        self, 
        error_code: str, 
        manufacturer: str, 
        product: Optional[str] = None
    ) -> ErrorCodeSearchResponse:
        """
        Search for error code across multiple sources
        
        Args:
            error_code: The error code to search for
            manufacturer: Manufacturer name
            product: Optional product model/series
        
        Returns:
            ErrorCodeSearchResponse with formatted results
        """
        try:
            self.logger.info(f"Searching error code: {error_code} for manufacturer: {manufacturer}")
            
            # 1. Search error codes in database
            error_results = await self._search_error_codes_in_db(error_code, manufacturer)
            
            # 2. Search related videos
            video_results = await self._search_videos(error_code, manufacturer, product)
            
            # 3. Extract parts from error code solutions
            parts_results = await self._extract_parts_from_solutions(error_code, manufacturer)
            
            # 4. Format response according to Agent System Message spec
            if not error_results:
                return ErrorCodeSearchResponse(
                    found=False,
                    message=f"Fehlercode {error_code} für {manufacturer} nicht gefunden."
                )
            
            # Get description from first error result
            description = error_results[0].get('error_description', 'Unbekannter Fehler')
            
            # Format documents
            documents = []
            for result in error_results:
                doc_info = {
                    'filename': result.get('document_filename', 'Unbekanntes Dokument'),
                    'page': result.get('page_number', 'N/A'),
                    'solution': result.get('solution_text', 'Keine Lösung verfügbar')
                }
                documents.append(doc_info)
            
            # Format videos
            videos = []
            for video in video_results:
                video_info = {
                    'title': video.get('title', 'Unbekanntes Video'),
                    'url': video.get('url', ''),
                    'duration': video.get('duration', 'N/A')
                }
                videos.append(video_info)
            
            return ErrorCodeSearchResponse(
                found=True,
                error_code=error_code,
                description=description,
                documents=documents,
                videos=videos,
                parts=parts_results
            )
            
        except Exception as e:
            self.logger.error(f"Error in multi-source search: {e}", exc_info=True)
            return ErrorCodeSearchResponse(
                found=False,
                message=f"Fehler bei der Suche: {str(e)}"
            )
    
    async def _search_error_codes_in_db(self, error_code: str, manufacturer: str) -> List[Dict]:
        """Search error codes in the database"""
        try:
            # Use the existing vw_error_codes view
            response = self.supabase.table('vw_error_codes') \
                .select('error_code, error_description, solution_text, page_number, manufacturer_id, document_id') \
                .ilike('error_code', f'%{error_code}%') \
                .order('confidence_score', desc=True) \
                .limit(5) \
                .execute()
            
            if not response.data:
                return []
            
            # Get manufacturer and document names
            manufacturer_ids = list(set([row['manufacturer_id'] for row in response.data if row.get('manufacturer_id')]))
            document_ids = list(set([row['document_id'] for row in response.data if row.get('document_id')]))
            
            manufacturers = {}
            if manufacturer_ids:
                mfr_response = self.supabase.table('vw_manufacturers') \
                    .select('id, name') \
                    .in_('id', manufacturer_ids) \
                    .execute()
                manufacturers = {row['id']: row['name'] for row in mfr_response.data}
            
            documents = {}
            if document_ids:
                doc_response = self.supabase.table('vw_documents') \
                    .select('id, filename') \
                    .in_('id', document_ids) \
                    .execute()
                documents = {row['id']: row['filename'] for row in doc_response.data}
            
            # Filter by manufacturer if specified
            filtered_results = []
            for row in response.data:
                mfr_name = manufacturers.get(row.get('manufacturer_id'), '').lower()
                if mfr_name == manufacturer.lower() or mfr_name in manufacturer.lower():
                    result = {
                        'error_code': row.get('error_code'),
                        'error_description': row.get('error_description'),
                        'solution_text': row.get('solution_text'),
                        'page_number': row.get('page_number'),
                        'document_filename': documents.get(row.get('document_id'), 'Unbekanntes Dokument'),
                        'manufacturer_name': manufacturers.get(row.get('manufacturer_id'), manufacturer)
                    }
                    filtered_results.append(result)
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Error searching error codes in DB: {e}")
            return []
    
    async def _search_videos(self, error_code: str, manufacturer: str, product: Optional[str]) -> List[Dict]:
        """Search for related videos"""
        try:
            search_terms = [error_code, manufacturer]
            if product:
                search_terms.append(product)
            
            # Search in videos table
            query_parts = []
            for term in search_terms:
                query_parts.append(f"title.ilike.%{term}%")
                query_parts.append(f"description.ilike.%{term}%")
            
            query = " OR ".join(query_parts[:6])  # Limit query parts
            
            response = self.supabase.table('vw_videos') \
                .select('title, url, description, duration, manufacturer_id, model_series') \
                .or_(query) \
                .limit(5) \
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"Error searching videos: {e}")
            return []
    
    async def _extract_parts_from_solutions(self, error_code: str, manufacturer: str) -> List[str]:
        """Extract part numbers from error code solutions"""
        try:
            # Get error code solutions
            solutions_response = self.supabase.table('vw_error_codes') \
                .select('solution_text') \
                .ilike('error_code', f'%{error_code}%') \
                .execute()
            
            parts = set()
            for row in solutions_response.data:
                solution_text = row.get('solution_text', '')
                if solution_text:
                    # Extract part numbers using regex
                    part_patterns = [
                        r'\b[A-Z]{2,4}[-_]?\d{3,8}\b',  # ABC12345, ABC-12345
                        r'\b\d{4,8}[-_]?[A-Z]{0,3}\b',   # 12345ABC
                        r'\b[A-Z]-\d{4,8}\b'            # A-12345
                    ]
                    
                    for pattern in part_patterns:
                        matches = re.findall(pattern, solution_text.upper())
                        for match in matches:
                            parts.add(match.strip())
            
            # Also search in error_code_parts table if it exists
            try:
                parts_response = self.supabase.table('error_code_parts') \
                    .select('part_id') \
                    .execute()
                
                for row in parts_response.data:
                    if row.get('part_id'):
                        parts.add(str(row['part_id']))
            except Exception:
                # Table might not exist, continue
                pass
            
            return list(parts)[:5]  # Limit to 5 parts
            
        except Exception as e:
            self.logger.error(f"Error extracting parts: {e}")
            return []


# ============================================================================
# FastAPI Router
# ============================================================================

router = APIRouter(prefix="/tools", tags=["error-code-search"])

# Global instances
_supabase_client = None
_search_service = None

def get_search_service() -> MultiSourceErrorCodeSearch:
    """Get or create search service instance"""
    global _supabase_client, _search_service
    
    if _search_service is None:
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Supabase configuration missing")
        
        _supabase_client = Client(supabase_url, supabase_key)
        _search_service = MultiSourceErrorCodeSearch(_supabase_client)
    
    return _search_service


@router.post("/search_error_code_multi_source", response_model=ErrorCodeSearchResponse)
async def search_error_code_multi_source(request: ErrorCodeSearchRequest):
    """
    Multi-source error code search tool
    
    Searches for error codes across documents, videos, and parts.
    Returns results in the format expected by the Agent System Message.
    """
    try:
        search_service = get_search_service()
        
        result = await search_service.search_error_code(
            error_code=request.error_code,
            manufacturer=request.manufacturer,
            product=request.product
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in search_error_code_multi_source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for the error code search service"""
    return {
        "status": "healthy",
        "service": "search_error_code_multi_source",
        "version": "1.0.0"
    }


# ============================================================================
# Tool Response Formatter
# ============================================================================

def format_tool_response(result: ErrorCodeSearchResponse) -> str:
    """
    Format the search result according to Agent System Message V2.4 specification
    
    Returns the exact format expected by the agent system.
    """
    if not result.found:
        return f"❌ Fehlercode {result.error_code} für {result.manufacturer} nicht gefunden."
    
    # Start building the response
    response_lines = []
    
    # Error code header
    response_lines.append(f"🔴 ERROR CODE: {result.error_code}")
    response_lines.append(f"📝 {result.description}")
    response_lines.append("")
    
    # Documents section
    if result.documents:
        doc_count = len(result.documents)
        response_lines.append(f"📖 DOKUMENTATION ({doc_count}):")
        
        for i, doc in enumerate(result.documents, 1):
            filename = doc.get('filename', 'Unbekanntes Dokument')
            page = doc.get('page', 'N/A')
            solution = doc.get('solution', 'Keine Lösung verfügbar')
            
            response_lines.append(f"{i}. {filename} (Seite {page})")
            response_lines.append(f"   💡 Lösung: {solution}")
            
            # Add parts if available
            if result.parts:
                parts_str = ", ".join(result.parts[:3])  # Show max 3 parts
                response_lines.append(f"   🔧 Parts: {parts_str}")
            
            response_lines.append("")
    
    # Videos section
    if result.videos:
        video_count = len(result.videos)
        response_lines.append(f"🎬 VIDEOS ({video_count}):")
        
        for i, video in enumerate(result.videos, 1):
            title = video.get('title', 'Unbekanntes Video')
            url = video.get('url', '')
            duration = video.get('duration', 'N/A')
            
            response_lines.append(f"{i}. {title} ({duration})")
            if url:
                response_lines.append(f"   🔗 {url}")
            
            response_lines.append("")
    
    # Final prompt
    response_lines.append("💡 Möchtest du mehr Details?")
    
    return "\n".join(response_lines)
