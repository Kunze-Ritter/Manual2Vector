"""
Video Metadata Enrichment Module
Extracts metadata from YouTube, Vimeo, Brightcove and direct video URLs
"""

import logging
import re
import json
import asyncio
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class VideoEnricher:
    """Real VideoEnricher class for YouTube, Vimeo, Brightcove metadata extraction"""
    
    def __init__(self, database_adapter=None):
        """Initialize video enricher"""
        self.database_adapter = database_adapter
        self.youtube_api_key = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Try to get YouTube API key from environment
        try:
            import os
            self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
            if self.youtube_api_key and self.youtube_api_key != "your_youtube_api_key_here":
                logger.info("YouTube API key configured")
            else:
                logger.warning("YouTube API key not configured - limited YouTube functionality")
        except Exception as e:
            logger.warning(f"Could not get YouTube API key: {e}")
        
        logger.info("VideoEnricher initialized - YouTube, Vimeo, Brightcove support ready")
    
    def detect_platform(self, url: str) -> str:
        """Detect video platform from URL"""
        domain = urlparse(url).netloc.lower()
        
        if 'youtube.com' in domain or 'youtu.be' in domain:
            return 'youtube'
        elif 'vimeo.com' in domain:
            return 'vimeo'
        elif 'brightcove' in domain or 'bcov' in domain:
            return 'brightcove'
        elif any(ext in url.lower() for ext in ['.mp4', '.webm', '.mov', '.avi', '.mkv']):
            return 'direct'
        else:
            return 'unknown'
    
    def extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def extract_vimeo_id(self, url: str) -> Optional[str]:
        """Extract Vimeo video ID from URL"""
        patterns = [
            r'vimeo\.com/(\d+)',
            r'player\.vimeo\.com/video/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def enrich_youtube_video(self, video_id: str) -> Dict[str, Any]:
        """Extract YouTube video metadata"""
        metadata = {
            'platform': 'youtube',
            'video_id': video_id,
            'url': f'https://www.youtube.com/watch?v={video_id}',
            'title': None,
            'description': None,
            'duration': None,
            'thumbnail_url': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
            'channel_title': None,
            'published_at': None,
            'view_count': None,
            'metadata': {}
        }
        
        # Try YouTube Data API if key is available
        if self.youtube_api_key:
            try:
                api_url = f"https://www.googleapis.com/youtube/v3/videos"
                params = {
                    'part': 'snippet,contentDetails,statistics',
                    'id': video_id,
                    'key': self.youtube_api_key
                }
                
                response = self.session.get(api_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('items'):
                        item = data['items'][0]
                        snippet = item.get('snippet', {})
                        content_details = item.get('contentDetails', {})
                        statistics = item.get('statistics', {})
                        
                        metadata.update({
                            'title': snippet.get('title'),
                            'description': snippet.get('description'),
                            'channel_title': snippet.get('channelTitle'),
                            'published_at': snippet.get('publishedAt'),
                            'view_count': statistics.get('viewCount'),
                            'metadata': {
                                'api_enriched': True,
                                'tags': snippet.get('tags', []),
                                'category_id': snippet.get('categoryId'),
                                'duration_iso': content_details.get('duration'),
                                'definition': content_details.get('definition'),
                                'caption': content_details.get('caption')
                            }
                        })
                        
                        # Parse duration
                        duration_str = content_details.get('duration', '')
                        if duration_str:
                            metadata['duration'] = self._parse_youtube_duration(duration_str)
                        
                        logger.info(f"✅ YouTube API enrichment successful for {video_id}")
                    else:
                        logger.warning(f"YouTube video not found: {video_id}")
                else:
                    logger.warning(f"YouTube API error: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"YouTube API request failed: {e}")
        
        # Fallback to oembed if API fails
        if not metadata['title']:
            try:
                oembed_url = f"https://www.youtube.com/oembed"
                params = {'url': f'https://www.youtube.com/watch?v={video_id}', 'format': 'json'}
                
                response = self.session.get(oembed_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    metadata.update({
                        'title': data.get('title'),
                        'author_name': data.get('author_name'),
                        'thumbnail_url': data.get('thumbnail_url'),
                        'metadata': {**metadata['metadata'], 'oembed_enriched': True}
                    })
                    logger.info(f"✅ YouTube oEmbed fallback successful for {video_id}")
                    
            except Exception as e:
                logger.error(f"YouTube oEmbed fallback failed: {e}")
        
        return metadata
    
    async def enrich_vimeo_video(self, video_id: str) -> Dict[str, Any]:
        """Extract Vimeo video metadata"""
        metadata = {
            'platform': 'vimeo',
            'video_id': video_id,
            'url': f'https://vimeo.com/{video_id}',
            'title': None,
            'description': None,
            'duration': None,
            'thumbnail_url': None,
            'channel_title': None,
            'published_at': None,
            'metadata': {}
        }
        
        try:
            # Try Vimeo oEmbed API
            oembed_url = f"https://vimeo.com/api/oembed.json"
            params = {'url': f'https://vimeo.com/{video_id}'}
            
            response = self.session.get(oembed_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                metadata.update({
                    'title': data.get('title'),
                    'description': data.get('description'),
                    'author_name': data.get('author_name'),
                    'duration': data.get('duration'),
                    'thumbnail_url': data.get('thumbnail_url'),
                    'upload_date': data.get('upload_date'),
                    'metadata': {
                        'oembed_enriched': True,
                        'author_url': data.get('author_url'),
                        'width': data.get('width'),
                        'height': data.get('height')
                    }
                })
                logger.info(f"✅ Vimeo enrichment successful for {video_id}")
            else:
                logger.warning(f"Vimeo API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Vimeo enrichment failed: {e}")
        
        return metadata
    
    async def enrich_brightcove_video(self, url: str) -> Dict[str, Any]:
        """Extract Brightcove video metadata"""
        metadata = {
            'platform': 'brightcove',
            'video_id': None,
            'url': url,
            'title': None,
            'description': None,
            'duration': None,
            'thumbnail_url': None,
            'channel_title': None,
            'published_at': None,
            'metadata': {}
        }
        
        # Extract video ID from Brightcove URL patterns
        brightcove_patterns = [
            r'brightcove\.net/[^/]+/[^/]+/([^/]+)/',
            r'players\.brightcove\.net/[^/]+/([^/]+)/index\.html\?videoId=([^&]+)'
        ]
        
        video_id = None
        for pattern in brightcove_patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1) if len(match.groups()) == 1 else match.group(2)
                break
        
        if video_id:
            metadata['video_id'] = video_id
            metadata['metadata']['extracted_id'] = True
            logger.info(f"✅ Brightcove video ID extracted: {video_id}")
        else:
            logger.warning("Could not extract Brightcove video ID")
            metadata['metadata']['id_extraction_failed'] = True
        
        # Note: Full Brightcove API integration would require account-specific API keys
        # This is a basic implementation that extracts what's possible from the URL
        
        return metadata
    
    async def enrich_direct_video(self, url: str) -> Dict[str, Any]:
        """Extract metadata from direct video URLs"""
        metadata = {
            'platform': 'direct',
            'video_id': None,
            'url': url,
            'title': self._extract_title_from_url(url),
            'description': f"Direct video file: {url}",
            'duration': None,
            'thumbnail_url': None,
            'channel_title': None,
            'published_at': None,
            'metadata': {
                'direct_video': True,
                'file_extension': self._get_file_extension(url)
            }
        }
        
        # Try to extract models from title for product linking
        try:
            from backend.utils.model_detector import extract_models_from_text
            if metadata['title']:
                models = extract_models_from_text(metadata['title'])
                if models:
                    metadata['models'] = models
                    metadata['metadata']['models_extracted'] = True
        except Exception as e:
            logger.debug(f"Model extraction failed: {e}")
        
        return metadata
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract basic title from URL"""
        filename = url.split('/')[-1]
        # Remove file extension
        if '.' in filename:
            filename = '.'.join(filename.split('.')[:-1])
        # Replace separators with spaces and capitalize
        title = re.sub(r'[-_]', ' ', filename).title()
        return title or "Unknown Video"
    
    def _get_file_extension(self, url: str) -> str:
        """Get file extension from URL"""
        parsed = urlparse(url)
        path = parsed.path
        if '.' in path:
            return path.split('.')[-1].lower()
        return 'unknown'
    
    def _parse_youtube_duration(self, duration_str: str) -> Optional[int]:
        """Parse YouTube duration format (PT4M13S) to seconds"""
        try:
            import re
            # PT4M13S -> 4 minutes 13 seconds
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                return hours * 3600 + minutes * 60 + seconds
        except Exception as e:
            logger.error(f"Failed to parse YouTube duration: {e}")
        return None
    
    async def enrich_video(self, video_url: str, **kwargs) -> Dict[str, Any]:
        """
        Enrich video with platform-specific metadata
        
        Args:
            video_url: URL of the video to enrich
            **kwargs: Additional parameters (document_id, manufacturer_id)
            
        Returns:
            Complete video metadata
        """
        logger.info(f"🎬 Enriching video: {video_url}")
        
        # Detect platform
        platform = self.detect_platform(video_url)
        
        if platform == 'youtube':
            video_id = self.extract_youtube_id(video_url)
            if video_id:
                metadata = await self.enrich_youtube_video(video_id)
            else:
                return {'error': 'Invalid YouTube URL', 'url': video_url}
                
        elif platform == 'vimeo':
            video_id = self.extract_vimeo_id(video_url)
            if video_id:
                metadata = await self.enrich_vimeo_video(video_id)
            else:
                return {'error': 'Invalid Vimeo URL', 'url': video_url}
                
        elif platform == 'brightcove':
            metadata = await self.enrich_brightcove_video(video_url)
            
        elif platform == 'direct':
            metadata = await self.enrich_direct_video(video_url)
            
        else:
            return {'error': f'Unsupported platform: {platform}', 'url': video_url}
        
        # Add additional context if provided
        if kwargs.get('document_id'):
            metadata['document_id'] = kwargs['document_id']
        if kwargs.get('manufacturer_id'):
            metadata['manufacturer_id'] = kwargs['manufacturer_id']
        
        return metadata
    
    async def batch_enrich(self, video_urls: List[str], **kwargs) -> Dict[str, Any]:
        """
        Batch enrich multiple videos
        
        Args:
            video_urls: List of video URLs
            **kwargs: Additional parameters
            
        Returns:
            Batch enrichment results
        """
        results = []
        errors = []
        
        for url in video_urls:
            try:
                result = await self.enrich_video(url, **kwargs)
                if 'error' in result:
                    errors.append(result)
                else:
                    results.append(result)
            except Exception as e:
                errors.append({'url': url, 'error': str(e)})
        
        return {
            'results': results,
            'errors': errors,
            'total': len(video_urls),
            'successful': len(results),
            'failed': len(errors)
        }
