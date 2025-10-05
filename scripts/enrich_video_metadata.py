#!/usr/bin/env python3
"""
Video Metadata Enrichment Script
=================================
Enriches video links with metadata from YouTube, Vimeo, and other sources.

Features:
- YouTube API integration (title, description, duration, views, etc.)
- Vimeo API support (when needed)
- Thumbnail extraction for generic videos
- Batch processing with rate limiting
- Auto-linking to videos table

Usage:
    python scripts/enrich_video_metadata.py [--limit 10] [--force]
    
Options:
    --limit N    Process only N videos (default: all)
    --force      Re-process already enriched videos
"""

import os
import re
import sys
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


class VideoEnricher:
    """Enriches video links with metadata from various sources"""
    
    def __init__(self):
        self.youtube_api_key = YOUTUBE_API_KEY
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.processed_count = 0
        self.error_count = 0
        
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
    
    def extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def extract_vimeo_id(self, url: str) -> Optional[str]:
        """Extract Vimeo video ID from URL"""
        patterns = [
            r'player\.vimeo\.com\/video\/(\d+)',  # player.vimeo.com/video/123
            r'vimeo\.com\/(\d+)'                    # vimeo.com/123
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def get_youtube_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Fetch metadata from YouTube API"""
        if not self.youtube_api_key or self.youtube_api_key == 'your_youtube_api_key_here':
            logger.warning("YouTube API key not configured. Skipping YouTube enrichment.")
            return None
        
        try:
            url = f"https://www.googleapis.com/youtube/v3/videos"
            params = {
                'id': video_id,
                'key': self.youtube_api_key,
                'part': 'snippet,contentDetails,statistics'
            }
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('items'):
                logger.warning(f"No data found for YouTube video: {video_id}")
                return None
            
            item = data['items'][0]
            snippet = item['snippet']
            stats = item.get('statistics', {})
            content = item.get('contentDetails', {})
            
            # Parse duration (PT1H2M10S format)
            duration_str = content.get('duration', 'PT0S')
            duration_seconds = self._parse_iso8601_duration(duration_str)
            
            return {
                'youtube_id': video_id,
                'title': snippet.get('title'),
                'description': snippet.get('description'),
                'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url'),
                'duration': duration_seconds,
                'view_count': int(stats.get('viewCount', 0)),
                'like_count': int(stats.get('likeCount', 0)),
                'comment_count': int(stats.get('commentCount', 0)),
                'channel_id': snippet.get('channelId'),
                'channel_title': snippet.get('channelTitle'),
                'published_at': snippet.get('publishedAt')
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.error("YouTube API quota exceeded or invalid API key")
            else:
                logger.error(f"YouTube API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching YouTube metadata: {e}")
            return None
    
    def _parse_iso8601_duration(self, duration: str) -> int:
        """Parse ISO 8601 duration (PT1H2M10S) to seconds"""
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    async def get_vimeo_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Fetch metadata from Vimeo API (unauthenticated)"""
        try:
            url = f"https://vimeo.com/api/v2/video/{video_id}.json"
            response = await self.http_client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return None
            
            video = data[0]
            return {
                'title': video.get('title'),
                'description': video.get('description'),
                'thumbnail_url': video.get('thumbnail_large'),
                'duration': video.get('duration'),
                'view_count': video.get('stats_number_of_plays', 0),
                'channel_title': video.get('user_name')
            }
            
        except Exception as e:
            logger.error(f"Error fetching Vimeo metadata: {e}")
            return None
    
    async def enrich_youtube_link(self, link: Dict[str, Any]) -> bool:
        """Enrich a YouTube link with metadata"""
        video_id = self.extract_youtube_id(link['url'])
        if not video_id:
            logger.warning(f"Could not extract YouTube ID from: {link['url']}")
            return False
        
        metadata = await self.get_youtube_metadata(video_id)
        if not metadata:
            return False
        
        try:
            # Insert into videos table (krai_content schema)
            video_record = supabase.table('videos').insert({
                'link_id': link['id'],
                'youtube_id': metadata['youtube_id'],
                'title': metadata['title'],
                'description': metadata['description'],
                'thumbnail_url': metadata['thumbnail_url'],
                'duration': metadata['duration'],
                'view_count': metadata['view_count'],
                'like_count': metadata['like_count'],
                'comment_count': metadata['comment_count'],
                'channel_id': metadata['channel_id'],
                'channel_title': metadata['channel_title'],
                'published_at': metadata['published_at'],
                'metadata': {
                    'enriched_at': datetime.now(timezone.utc).isoformat(),
                    'source': 'youtube_api'
                }
            }).execute()
            
            if video_record.data:
                # Update link with video_id
                supabase.table('links').update({
                    'video_id': video_record.data[0]['id']
                }).eq('id', link['id']).execute()
                
                logger.info(f"✅ Enriched YouTube video: {metadata['title'][:50]}...")
                return True
            
        except Exception as e:
            logger.error(f"Error saving YouTube metadata: {e}")
            return False
        
        return False
    
    async def enrich_vimeo_link(self, link: Dict[str, Any]) -> bool:
        """Enrich a Vimeo link with metadata"""
        video_id = self.extract_vimeo_id(link['url'])
        if not video_id:
            logger.warning(f"Could not extract Vimeo ID from: {link['url']}")
            return False
        
        metadata = await self.get_vimeo_metadata(video_id)
        if not metadata:
            return False
        
        try:
            # Insert into videos table (simplified for Vimeo)
            video_record = supabase.table('videos').insert({
                'link_id': link['id'],
                'youtube_id': None,  # Vimeo doesn't use youtube_id
                'title': metadata['title'],
                'description': metadata['description'],
                'thumbnail_url': metadata['thumbnail_url'],
                'duration': metadata['duration'],
                'view_count': metadata['view_count'],
                'channel_title': metadata['channel_title'],
                'metadata': {
                    'enriched_at': datetime.now(timezone.utc).isoformat(),
                    'source': 'vimeo_api',
                    'vimeo_id': video_id
                }
            }).execute()
            
            if video_record.data:
                # Update link with video_id
                supabase.table('links').update({
                    'video_id': video_record.data[0]['id']
                }).eq('id', link['id']).execute()
                
                logger.info(f"✅ Enriched Vimeo video: {metadata['title'][:50]}...")
                return True
            
        except Exception as e:
            logger.error(f"Error saving Vimeo metadata: {e}")
            return False
        
        return False
    
    async def enrich_link(self, link: Dict[str, Any]) -> bool:
        """Enrich a video link based on its type"""
        url = link['url']
        
        if 'youtube.com' in url or 'youtu.be' in url:
            return await self.enrich_youtube_link(link)
        elif 'vimeo.com' in url:
            return await self.enrich_vimeo_link(link)
        else:
            logger.info(f"⏭️  Skipping unsupported video platform: {url}")
            return False
    
    async def process_unenriched_links(self, limit: Optional[int] = None, force: bool = False):
        """Process all unenriched video links"""
        logger.info("🔍 Finding video links to enrich...")
        
        try:
            # Query for video links without video_id
            query = supabase.table('links').select('*')
            
            if not force:
                query = query.is_('video_id', 'null')
            
            query = query.in_('link_type', ['video', 'youtube', 'vimeo'])
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            links = response.data
            
            if not links:
                logger.info("✅ No video links found to enrich!")
                return
            
            logger.info(f"📹 Found {len(links)} video links to process")
            
            for i, link in enumerate(links, 1):
                logger.info(f"\n[{i}/{len(links)}] Processing: {link['url']}")
                
                success = await self.enrich_link(link)
                
                if success:
                    self.processed_count += 1
                else:
                    self.error_count += 1
                
                # Rate limiting (YouTube API: 10,000 quota/day)
                await asyncio.sleep(0.5)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Processing complete!")
            logger.info(f"   Enriched: {self.processed_count}")
            logger.info(f"   Errors: {self.error_count}")
            logger.info(f"{'='*60}")
            
        except Exception as e:
            logger.error(f"Error processing links: {e}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich video links with metadata')
    parser.add_argument('--limit', type=int, help='Limit number of videos to process')
    parser.add_argument('--force', action='store_true', help='Re-process already enriched videos')
    args = parser.parse_args()
    
    # Check API key
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == 'your_youtube_api_key_here':
        logger.warning("⚠️  YouTube API key not configured!")
        logger.warning("   Set YOUTUBE_API_KEY in .env file")
        logger.warning("   Get your key at: https://console.cloud.google.com/apis/credentials")
        logger.warning("")
        logger.warning("   Vimeo videos will still be processed.")
        logger.warning("")
    
    enricher = VideoEnricher()
    
    try:
        await enricher.process_unenriched_links(limit=args.limit, force=args.force)
    finally:
        await enricher.close()


if __name__ == '__main__':
    asyncio.run(main())
