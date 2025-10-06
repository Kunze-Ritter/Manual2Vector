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
                                    # Safely decode description (may be UTF-16-LE encoded)
                                    description = annot.get('contents', '')
                                    if isinstance(description, bytes):
                                        try:
                                            # Try UTF-16-LE first (common in PDF annotations)
                                            description = description.decode('utf-16-le', errors='ignore')
                                        except:
                                            try:
                                                description = description.decode('utf-8', errors='ignore')
                                            except:
                                                description = str(description, errors='ignore')
                                    
                                    links.append({
                                        'url': url,
                                        'page_number': page_num,
                                        'description': description if description else '',
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
                    
                    thumbnail_url = snippet.get('thumbnails', {}).get('high', {}).get('url') or \
                                   snippet.get('thumbnails', {}).get('default', {}).get('url')
                    
                    return {
                        'youtube_id': youtube_id,
                        'title': snippet.get('title'),
                        'description': snippet.get('description'),
                        'thumbnail_url': thumbnail_url,
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
    
    def analyze_video_thumbnail(
        self,
        video_metadata: Dict,
        enable_ocr: bool = True,
        enable_vision: bool = True
    ) -> Dict:
        """
        Analyze video thumbnail with OCR and Vision AI
        
        Args:
            video_metadata: Video metadata dict with thumbnail_url
            enable_ocr: Run OCR on thumbnail
            enable_vision: Run Vision AI on thumbnail
            
        Returns:
            Updated video_metadata with thumbnail_ocr_text and thumbnail_ai_description
        """
        thumbnail_url = video_metadata.get('thumbnail_url')
        if not thumbnail_url:
            return video_metadata
        
        try:
            import requests
            from PIL import Image
            from io import BytesIO
            import base64
            
            # Download thumbnail
            response = requests.get(thumbnail_url, timeout=10)
            if response.status_code != 200:
                return video_metadata
            
            thumbnail_image = Image.open(BytesIO(response.content))
            
            # OCR on thumbnail
            if enable_ocr:
                try:
                    import pytesseract
                    import sys
                    import os
                    
                    # Configure Tesseract path (Windows) - BEFORE using OCR
                    if sys.platform == "win32":
                        possible_paths = [
                            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                        ]
                        for path in possible_paths:
                            if os.path.exists(path):
                                pytesseract.pytesseract.tesseract_cmd = path
                                break
                    
                    ocr_text = pytesseract.image_to_string(thumbnail_image)
                    if ocr_text.strip():
                        video_metadata['thumbnail_ocr_text'] = ocr_text.strip()
                        self.logger.debug(f"OCR extracted {len(ocr_text)} chars from video thumbnail")
                except Exception as e:
                    self.logger.debug(f"Thumbnail OCR failed: {e}")
            
            # Vision AI on thumbnail
            if enable_vision:
                try:
                    import os
                    ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
                    
                    # Check for vision model
                    models_response = requests.get(f"{ollama_url}/api/tags", timeout=2)
                    models = models_response.json().get('models', [])
                    vision_models = [m for m in models if 'llava' in m.get('name', '').lower()]
                    
                    if vision_models:
                        # Convert image to base64
                        buffer = BytesIO()
                        thumbnail_image.save(buffer, format='JPEG')
                        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                        
                        # Analyze with LLaVA
                        prompt = """Briefly describe this video thumbnail in 1-2 sentences. 
What is shown? Is it a tutorial, demonstration, or presentation?
Any visible text or product names?"""
                        
                        vision_response = requests.post(
                            f"{ollama_url}/api/generate",
                            json={
                                "model": vision_models[0]['name'],
                                "prompt": prompt,
                                "images": [image_data],
                                "stream": False
                            },
                            timeout=20
                        )
                        
                        if vision_response.status_code == 200:
                            description = vision_response.json().get('response', '').strip()
                            if description:
                                video_metadata['thumbnail_ai_description'] = description
                                self.logger.debug(f"Vision AI analyzed thumbnail: {description[:50]}...")
                except Exception as e:
                    self.logger.debug(f"Thumbnail Vision AI failed: {e}")
            
            return video_metadata
            
        except Exception as e:
            self.logger.debug(f"Thumbnail analysis failed: {e}")
            return video_metadata
    
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
        """
        Classify link type based on URL
        
        Valid types (per database constraint):
        - 'video', 'external', 'tutorial', 'support', 'download', 'email', 'phone'
        """
        url_lower = url.lower()
        
        # Email links
        if url_lower.startswith('mailto:'):
            return 'email'
        
        # Phone links
        if url_lower.startswith('tel:'):
            return 'phone'
        
        # Support links
        if 'support' in url_lower or 'help' in url_lower or 'kb' in url_lower:
            return 'support'
        
        # Download links
        elif 'download' in url_lower or 'driver' in url_lower or 'software' in url_lower:
            return 'download'
        elif any(ext in url_lower for ext in ['.pdf', '.zip', '.exe', '.dmg', '.pkg']):
            return 'download'
        
        # Video/Tutorial links
        elif 'video' in url_lower or 'youtube' in url_lower or 'vimeo' in url_lower:
            return 'video'
        elif 'tutorial' in url_lower or 'how-to' in url_lower or 'guide' in url_lower:
            return 'tutorial'
        
        # Default: external
        else:
            return 'external'
    
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
