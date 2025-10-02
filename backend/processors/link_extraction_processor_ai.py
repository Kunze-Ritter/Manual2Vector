"""
AI-Powered Link Extraction Processor
Extracts and intelligently categorizes links from documents with video linking
"""

import re
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import asyncio

from core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult, ProcessingError

class LinkExtractionProcessorAI(BaseProcessor):
    """
    AI-Powered Link Extraction Processor
    - Extracts links from PDF annotations and text
    - Categorizes (video, support, download, etc.)
    - Links YouTube/Vimeo to instructional_videos table
    - AI-powered metadata extraction
    """
    
    def __init__(self, database_service, ai_service=None):
        super().__init__("link_extraction_ai")
        self.database_service = database_service
        self.ai_service = ai_service
        
        # URL patterns
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        # Video platforms
        self.video_platforms = {
            'youtube.com': 'youtube',
            'youtu.be': 'youtube',
            'vimeo.com': 'vimeo',
            'dailymotion.com': 'dailymotion',
            'wistia.com': 'wistia'
        }
        
        # Support domains
        self.support_domains = {
            'support.hp.com', 'support.utax.com', 'support.canon.com',
            'support.xerox.com', 'support.ricoh.com', 'support.kyocera.com',
            'www.hp.com/support', 'www.utax.com/support', 'www.canon.com/support'
        }
        
        # Download domains
        self.download_domains = {
            'download.hp.com', 'download.utax.com', 'download.canon.com',
            'drivers.hp.com', 'drivers.canon.com'
        }
    
    def get_required_inputs(self) -> List[str]:
        return ['document_id', 'file_path']
    
    def get_outputs(self) -> List[str]:
        return ['links_extracted', 'video_links_created', 'link_ids']
    
    def get_output_tables(self) -> List[str]:
        return ['krai_content.links', 'krai_content.instructional_videos']
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'cpu_intensive': False,
            'memory_intensive': False,
            'gpu_required': False,
            'estimated_ram_gb': 0.5,
            'parallel_safe': True
        }
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """Extract and categorize links from document"""
        try:
            self.logger.info(f"Extracting links from: {context.file_path}")
            
            # Get document info
            document = await self.database_service.get_document(context.document_id)
            if not document:
                raise ProcessingError("Document not found", self.name, "DOC_NOT_FOUND")
            
            # Extract links from PDF
            links = await self._extract_links_from_pdf(context.file_path)
            
            if not links:
                self.logger.info("No links found in document")
                return self.create_success_result({
                    'links_extracted': 0,
                    'video_links_created': 0,
                    'link_ids': []
                })
            
            # Categorize links with AI
            categorized_links = await self._categorize_links_ai(links, document)
            
            # Process video links (create instructional_videos if needed)
            video_count = await self._process_video_links(categorized_links, document)
            
            # Store links in database
            link_ids = await self._store_links(categorized_links, context.document_id)
            
            self.logger.info(f"Extracted {len(link_ids)} links ({video_count} videos)")
            
            return self.create_success_result({
                'links_extracted': len(link_ids),
                'video_links_created': video_count,
                'link_ids': link_ids
            }, {
                'processing_timestamp': datetime.utcnow().isoformat(),
                'categories': self._get_category_summary(categorized_links)
            })
            
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            raise ProcessingError(f"Link extraction failed: {str(e)}", self.name, "EXTRACTION_FAILED")
    
    async def _extract_links_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract links from PDF annotations and text"""
        links = []
        
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extract from annotations/links
                for link in page.get_links():
                    if 'uri' in link and link['uri']:
                        url = link['uri']
                        links.append({
                            'url': url,
                            'page_number': page_num + 1,
                            'position_data': {
                                'rect': link.get('from', []),
                                'type': 'annotation'
                            }
                        })
                
                # Extract from text (URLs)
                text = page.get_text()
                urls = self.url_pattern.findall(text)
                for url in urls:
                    links.append({
                        'url': url,
                        'page_number': page_num + 1,
                        'position_data': {'type': 'text'}
                    })
            
            doc.close()
            
            # Deduplicate by URL
            seen = set()
            unique_links = []
            for link in links:
                if link['url'] not in seen:
                    seen.add(link['url'])
                    unique_links.append(link)
            
            return unique_links
            
        except ImportError:
            self.logger.warning("PyMuPDF not available - using fallback extraction")
            # Fallback: just search text for URLs
            try:
                with open(file_path, 'rb') as f:
                    content = f.read().decode('latin-1', errors='ignore')
                urls = self.url_pattern.findall(content)
                return [{'url': url, 'page_number': 1, 'position_data': {'type': 'fallback'}} for url in set(urls)]
            except:
                return []
        except Exception as e:
            self.logger.error(f"PDF link extraction failed: {e}")
            return []
    
    async def _categorize_links_ai(self, links: List[Dict], document: Dict) -> List[Dict]:
        """Categorize links using AI and patterns"""
        categorized = []
        
        for link_data in links:
            url = link_data['url']
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Determine link_type and link_category
            link_type = 'external'
            link_category = None
            confidence = 0.8
            metadata = {}
            
            # Video platforms
            for video_domain, platform in self.video_platforms.items():
                if video_domain in domain:
                    link_type = 'video'
                    link_category = platform
                    confidence = 0.95
                    
                    # Extract video ID
                    if platform == 'youtube':
                        video_id = self._extract_youtube_id(url)
                        if video_id:
                            metadata['video_id'] = video_id
                            metadata['platform'] = 'youtube'
                    elif platform == 'vimeo':
                        video_id = self._extract_vimeo_id(url)
                        if video_id:
                            metadata['video_id'] = video_id
                            metadata['platform'] = 'vimeo'
                    break
            
            # Support links
            if link_type == 'external' and any(sup in url.lower() for sup in self.support_domains):
                link_type = 'support'
                link_category = f"support_{domain.split('.')[0]}"
                confidence = 0.9
            
            # Download links
            if link_type == 'external' and any(dl in url.lower() for dl in self.download_domains):
                link_type = 'download'
                link_category = 'driver_download'
                confidence = 0.85
            
            # Tutorial links (heuristic)
            if 'tutorial' in url.lower() or 'howto' in url.lower() or 'guide' in url.lower():
                if link_type == 'external':
                    link_type = 'tutorial'
                link_category = 'tutorial'
                confidence = 0.75
            
            categorized.append({
                **link_data,
                'link_type': link_type,
                'link_category': link_category,
                'confidence_score': confidence,
                'metadata': metadata
            })
        
        return categorized
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        try:
            parsed = urlparse(url)
            
            # youtu.be format
            if 'youtu.be' in parsed.netloc:
                return parsed.path.strip('/')
            
            # youtube.com format
            if 'youtube.com' in parsed.netloc:
                query = parse_qs(parsed.query)
                if 'v' in query:
                    return query['v'][0]
                # Embed format
                if '/embed/' in parsed.path:
                    return parsed.path.split('/embed/')[-1].split('?')[0]
            
            return None
        except:
            return None
    
    def _extract_vimeo_id(self, url: str) -> Optional[str]:
        """Extract Vimeo video ID from URL"""
        try:
            parsed = urlparse(url)
            if 'vimeo.com' in parsed.netloc:
                # Format: vimeo.com/123456789
                video_id = parsed.path.strip('/').split('/')[0]
                if video_id.isdigit():
                    return video_id
            return None
        except:
            return None
    
    async def _process_video_links(self, links: List[Dict], document: Dict) -> int:
        """Process video links - create instructional_videos if needed"""
        video_count = 0
        
        for link in links:
            if link['link_type'] != 'video':
                continue
            
            try:
                # Get video metadata (could be enhanced with YouTube API)
                video_metadata = await self._get_video_metadata(link)
                
                # Create or find instructional_video
                video_id = await self.database_service.find_or_create_video_from_link(
                    url=link['url'],
                    manufacturer_id=document.get('manufacturer_id'),
                    title=video_metadata.get('title'),
                    description=video_metadata.get('description'),
                    metadata=link['metadata']
                )
                
                if video_id:
                    link['video_id'] = video_id
                    video_count += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to process video link {link['url']}: {e}")
        
        return video_count
    
    async def _get_video_metadata(self, link: Dict) -> Dict:
        """Get video metadata - can be enhanced with YouTube/Vimeo API"""
        metadata = {}
        
        # Extract title from URL (basic heuristic)
        url = link['url']
        
        if link.get('link_category') == 'youtube' and 'video_id' in link['metadata']:
            video_id = link['metadata']['video_id']
            metadata['title'] = f"YouTube Video: {video_id}"
            metadata['url'] = url
            # TODO: Could call YouTube Data API here for real metadata
        
        elif link.get('link_category') == 'vimeo' and 'video_id' in link['metadata']:
            video_id = link['metadata']['video_id']
            metadata['title'] = f"Vimeo Video: {video_id}"
            metadata['url'] = url
            # TODO: Could call Vimeo API here
        
        return metadata
    
    async def _store_links(self, links: List[Dict], document_id: str) -> List[str]:
        """Store links in database"""
        link_ids = []
        
        for link in links:
            try:
                link_id = await self.database_service.create_link({
                    'document_id': document_id,
                    'url': link['url'],
                    'link_type': link['link_type'],
                    'link_category': link.get('link_category'),
                    'page_number': link.get('page_number'),
                    'position_data': link.get('position_data'),
                    'confidence_score': link.get('confidence_score', 0.8),
                    'video_id': link.get('video_id'),
                    'metadata': link.get('metadata', {})
                })
                
                if link_id:
                    link_ids.append(link_id)
                    
            except Exception as e:
                self.logger.error(f"Failed to store link {link['url']}: {e}")
        
        return link_ids
    
    def _get_category_summary(self, links: List[Dict]) -> Dict[str, int]:
        """Get summary of link categories"""
        summary = {}
        for link in links:
            link_type = link.get('link_type', 'unknown')
            summary[link_type] = summary.get(link_type, 0) + 1
        return summary
