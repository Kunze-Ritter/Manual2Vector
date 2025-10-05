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

from enrich_video_metadata import VideoEnricher

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
