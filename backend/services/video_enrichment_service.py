"""
Video Enrichment Service
Wraps the video enrichment script for use in the API
"""

import logging
import sys
import os
from typing import Optional, Dict, Any

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

try:
    from enrich_video_metadata import VideoEnricher
except ImportError as e:
    logger.warning(f"⚠️ VideoEnricher not available: {e}")
    VideoEnricher = None

logger = logging.getLogger(__name__)


class VideoEnrichmentService:
    """Service for enriching video links with metadata"""
    
    def __init__(self):
        """Initialize video enrichment service"""
        self.enricher = None
        logger.info("✅ Video Enrichment Service initialized")
    
    async def process_videos(self, limit: Optional[int] = None, force: bool = False) -> Dict[str, Any]:
        """
        Process and enrich video links
        
        Args:
            limit: Maximum number of videos to process
            force: Re-process already enriched videos
            
        Returns:
            Dictionary with enrichment results
        """
        try:
            if VideoEnricher is None:
                raise RuntimeError("VideoEnricher not available - check dependencies")
            
            logger.info(f"🎬 Starting video enrichment (limit={limit}, force={force})")
            
            # Create enricher instance
            enricher = VideoEnricher()
            
            # Process videos
            await enricher.process_unenriched_links(limit=limit, force=force)
            
            # Get results
            result = {
                "enriched": enricher.enriched_count,
                "errors": enricher.error_count,
                "checked": enricher.checked_count
            }
            
            # Close enricher
            await enricher.close()
            
            logger.info(f"✅ Video enrichment complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in video enrichment: {e}")
            raise
    
    async def enrich_video_url(
        self, 
        url: str, 
        document_id: Optional[str] = None,
        manufacturer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enrich a single video URL
        
        Args:
            url: Video URL to enrich
            document_id: Optional document ID to link to
            manufacturer_id: Optional manufacturer ID to link to
            
        Returns:
            Dictionary with video metadata
        """
        try:
            if VideoEnricher is None:
                raise RuntimeError("VideoEnricher not available - check dependencies")
            
            logger.info(f"🎬 Enriching single video: {url}")
            
            # Create enricher instance
            enricher = VideoEnricher()
            
            # Enrich the video
            result = await enricher.enrich_single_url(
                url=url,
                document_id=document_id,
                manufacturer_id=manufacturer_id
            )
            
            # Close enricher
            await enricher.close()
            
            logger.info(f"✅ Video enriched: {result.get('title', 'N/A')}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error enriching video: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for video enrichment service"""
        try:
            # Check if YouTube API key is configured
            youtube_key = os.getenv("YOUTUBE_API_KEY")
            
            return {
                "status": "healthy",
                "youtube_api_configured": bool(youtube_key and youtube_key != "your_youtube_api_key_here"),
                "supported_platforms": ["youtube", "vimeo", "brightcove"]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
