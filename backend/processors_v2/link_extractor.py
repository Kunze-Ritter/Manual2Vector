"""
Link Extractor - Extract URLs and Video Links from Documents

Extracts:
- PDF annotations/hyperlinks
- URLs from text (http://, https://)
- YouTube video links with metadata
- Support/Download links
"""

import re
import hashlib
from typing import List, Dict, Optional, Tuple
from uuid import UUID, uuid4
from pathlib import Path
import requests
from urllib.parse import urlparse, parse_qs

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️  pdfplumber not available - PDF link extraction disabled")

from .logger import get_logger


class LinkExtractor:
    """Extract and process links from documents"""
    
    def __init__(self, youtube_api_key: Optional[str] = None):
        """
        Initialize link extractor
        
        Args:
            youtube_api_key: Optional YouTube Data API key for metadata
        """
        self.logger = get_logger()
        self.youtube_api_key = youtube_api_key
        
        # URL patterns
        self.url_pattern = re.compile(
            r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b'
            r'(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)',
            re.IGNORECASE
        )
        
        # YouTube patterns
        self.youtube_patterns = [
            re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})', re.IGNORECASE),
            re.compile(r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})', re.IGNORECASE),
            re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})', re.IGNORECASE),
        ]
    
    def extract_from_document(
        self,
        pdf_path: Path,
        page_texts: Dict[int, str],
        document_id: UUID
    ) -> Dict:
        """
        Extract all links from document
        
        Args:
            pdf_path: Path to PDF file
            page_texts: Dictionary of {page_number: text}
            document_id: Document UUID
            
        Returns:
            Dict with extracted links and videos
        """
        all_links = []
        all_videos = []
        
        # Extract from PDF annotations
        if PDF_AVAILABLE and pdf_path.exists():
            pdf_links = self._extract_pdf_links(pdf_path)
            all_links.extend(pdf_links)
        
        # Extract from text
        for page_num, text in page_texts.items():
            text_links = self._extract_text_links(text, page_num)
            all_links.extend(text_links)
        
        # Deduplicate links
        unique_links = self._deduplicate_links(all_links)
        
        # Classify and enrich links
        enriched_links = []
        for link in unique_links:
            link['document_id'] = str(document_id)
            link['id'] = str(uuid4())
            
            # Check if YouTube
            youtube_id = self._extract_youtube_id(link['url'])
            if youtube_id:
                # Get YouTube metadata
                video_metadata = self._fetch_youtube_metadata(youtube_id)
                if video_metadata:
                    video_metadata['link_id'] = link['id']
                    video_metadata['id'] = str(uuid4())
                    all_videos.append(video_metadata)
                    link['video_id'] = video_metadata['id']
                    link['link_type'] = 'video'
                    link['link_category'] = 'youtube'
                else:
                    link['link_type'] = 'video'
                    link['link_category'] = 'youtube'
            else:
                # Classify link type
                link['link_type'] = self._classify_link(link['url'])
                link['link_category'] = self._categorize_link(link['url'])
            
            enriched_links.append(link)
        
        self.logger.success(f"Extracted {len(enriched_links)} unique links ({len(all_videos)} videos)")
        
        return {
            'links': enriched_links,
            'videos': all_videos,
            'total_links': len(enriched_links),
            'total_videos': len(all_videos)
        }
    
    def _extract_pdf_links(self, pdf_path: Path) -> List[Dict]:
        """Extract links from PDF annotations"""
        links = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Get annotations
                    if hasattr(page, 'annots') and page.annots:
                        for annot in page.annots:
                            if 'uri' in annot or 'URI' in annot:
                                url = annot.get('uri') or annot.get('URI')
                                if url:
                                    links.append({
                                        'url': url,
                                        'page_number': page_num,
                                        'description': annot.get('contents', ''),
                                        'position_data': {
                                            'rect': annot.get('rect'),
                                            'type': 'pdf_annotation'
                                        },
                                        'confidence_score': 1.0  # PDF annotations are reliable
                                    })
        except Exception as e:
            self.logger.warning(f"Failed to extract PDF links: {e}")
        
        return links
    
    def _extract_text_links(self, text: str, page_num: int) -> List[Dict]:
        """Extract URLs from text using regex"""
        links = []
        
        # Find all URLs
        matches = self.url_pattern.finditer(text)
        
        for match in matches:
            url = match.group(0)
            
            # Get context around URL
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            
            links.append({
                'url': url,
                'page_number': page_num,
                'description': context,
                'position_data': {
                    'char_start': match.start(),
                    'char_end': match.end(),
                    'type': 'text_extraction'
                },
                'confidence_score': 0.9  # Text extraction is pretty reliable
            })
        
        return links
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        for pattern in self.youtube_patterns:
            match = pattern.search(url)
            if match:
                return match.group(1)
        return None
    
    def _fetch_youtube_metadata(self, youtube_id: str) -> Optional[Dict]:
        """
        Fetch YouTube video metadata
        
        If API key is available, uses YouTube Data API.
        Otherwise, uses oembed (limited data).
        """
        try:
            if self.youtube_api_key:
                # Use YouTube Data API v3
                url = f"https://www.googleapis.com/youtube/v3/videos"
                params = {
                    'part': 'snippet,contentDetails,statistics',
                    'id': youtube_id,
                    'key': self.youtube_api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                if data.get('items'):
                    item = data['items'][0]
                    snippet = item.get('snippet', {})
                    details = item.get('contentDetails', {})
                    stats = item.get('statistics', {})
                    
                    # Parse duration (PT15M33S -> seconds)
                    duration = self._parse_youtube_duration(details.get('duration', ''))
                    
                    return {
                        'youtube_id': youtube_id,
                        'title': snippet.get('title'),
                        'description': snippet.get('description'),
                        'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url'),
                        'duration': duration,
                        'view_count': int(stats.get('viewCount', 0)),
                        'like_count': int(stats.get('likeCount', 0)),
                        'comment_count': int(stats.get('commentCount', 0)),
                        'channel_id': snippet.get('channelId'),
                        'channel_title': snippet.get('channelTitle'),
                        'published_at': snippet.get('publishedAt'),
                        'metadata': {
                            'category_id': snippet.get('categoryId'),
                            'tags': snippet.get('tags', []),
                            'default_language': snippet.get('defaultLanguage')
                        }
                    }
            else:
                # Fallback to oEmbed (no API key required, limited data)
                url = f"https://www.youtube.com/oembed"
                params = {
                    'url': f"https://www.youtube.com/watch?v={youtube_id}",
                    'format': 'json'
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                return {
                    'youtube_id': youtube_id,
                    'title': data.get('title'),
                    'description': None,
                    'thumbnail_url': data.get('thumbnail_url'),
                    'duration': None,
                    'view_count': None,
                    'like_count': None,
                    'comment_count': None,
                    'channel_id': None,
                    'channel_title': data.get('author_name'),
                    'published_at': None,
                    'metadata': {
                        'provider_name': data.get('provider_name'),
                        'provider_url': data.get('provider_url')
                    }
                }
        
        except Exception as e:
            self.logger.warning(f"Failed to fetch YouTube metadata for {youtube_id}: {e}")
            return None
    
    def _parse_youtube_duration(self, duration_str: str) -> Optional[int]:
        """
        Parse YouTube duration string to seconds
        
        Examples:
            PT15M33S -> 933 seconds
            PT1H2M10S -> 3730 seconds
            PT45S -> 45 seconds
        """
        if not duration_str:
            return None
        
        pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = pattern.match(duration_str)
        
        if not match:
            return None
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _classify_link(self, url: str) -> str:
        """Classify link type based on URL"""
        url_lower = url.lower()
        
        if 'support' in url_lower or 'help' in url_lower or 'kb' in url_lower:
            return 'support'
        elif 'download' in url_lower or 'driver' in url_lower or 'software' in url_lower:
            return 'download'
        elif 'manual' in url_lower or 'documentation' in url_lower or 'doc' in url_lower:
            return 'documentation'
        elif any(ext in url_lower for ext in ['.pdf', '.zip', '.exe', '.dmg', '.pkg']):
            return 'download'
        elif 'video' in url_lower or 'tutorial' in url_lower:
            return 'video'
        else:
            return 'other'
    
    def _categorize_link(self, url: str) -> str:
        """Categorize link by domain/platform"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if 'youtube.com' in domain or 'youtu.be' in domain:
            return 'youtube'
        elif 'vimeo.com' in domain:
            return 'vimeo'
        elif 'support' in domain or 'kb' in domain:
            return 'support_portal'
        elif 'download' in domain or 'driver' in domain:
            return 'download_portal'
        else:
            return 'external'
    
    def _deduplicate_links(self, links: List[Dict]) -> List[Dict]:
        """Remove duplicate links, keep best version"""
        seen_urls = {}
        
        for link in links:
            url = link['url']
            
            # Normalize URL for comparison
            url_normalized = url.lower().rstrip('/')
            
            if url_normalized not in seen_urls:
                seen_urls[url_normalized] = link
            else:
                # Keep link with higher confidence or more info
                existing = seen_urls[url_normalized]
                if link.get('confidence_score', 0) > existing.get('confidence_score', 0):
                    seen_urls[url_normalized] = link
                elif link.get('description') and not existing.get('description'):
                    seen_urls[url_normalized] = link
        
        return list(seen_urls.values())
