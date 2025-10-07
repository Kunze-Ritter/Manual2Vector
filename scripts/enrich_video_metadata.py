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
from supabase import create_client, Client

# Load environment variables (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, use system environment
    pass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration (lazy loaded)
def get_youtube_api_key():
    return os.getenv('YOUTUBE_API_KEY')

def get_supabase_client():
    """Lazy initialization of Supabase client"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(url, key)


class VideoEnricher:
    """Enriches video links with metadata from various sources"""
    
    def __init__(self):
        self.youtube_api_key = get_youtube_api_key()
        self.supabase = None  # Lazy loaded
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.processed_count = 0
        self.error_count = 0
    
    def _get_supabase(self):
        """Get or create Supabase client"""
        if self.supabase is None:
            self.supabase = get_supabase_client()
        return self.supabase
        
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
    
    def extract_brightcove_ids(self, url: str) -> Optional[tuple]:
        """
        Extract Brightcove account_id, player_id, and video_id from URL
        Returns: (account_id, player_id, video_id) or None
        """
        # Pattern: https://players.brightcove.net/{account_id}/{player_id}/index.html?videoId={video_id}
        # Video ID can be numeric or reference ID (ref:...)
        match = re.search(r'players\.brightcove\.net/(\d+)/([^/]+)/.*?videoId=([^&\s]+)', url)
        if match:
            account_id = match.group(1)
            player_id = match.group(2)
            video_id = match.group(3)
            # URL decode video_id (e.g., ref%3A... → ref:...)
            from urllib.parse import unquote
            video_id = unquote(video_id)
            return (account_id, player_id, video_id)
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
    
    async def get_brightcove_metadata(self, account_id: str, player_id: str, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata from Brightcove Playback API
        Note: Uses public playback API (no auth needed for public videos)
        """
        try:
            # Try to get policy key from player config (public)
            # For now, we'll use a generic approach that works for most public videos
            
            # Brightcove Edge Playback API
            # Note: This requires a policy key. For public videos, we can try without auth
            # or extract the policy key from the player HTML
            
            # Try getting the player config to extract policy key
            # Try both config.json and index.min.js
            policy_key = None
            
            # Method 1: Try config.json (contains policy key directly)
            try:
                config_url = f"https://players.brightcove.net/{account_id}/{player_id}/config.json"
                config_response = await self.http_client.get(config_url)
                config_data = config_response.json()
                
                # Policy key is usually in video_cloud.policy_key
                if 'video_cloud' in config_data and 'policy_key' in config_data['video_cloud']:
                    policy_key = config_data['video_cloud']['policy_key']
                    logger.info(f"🔑 Extracted Brightcove policy key from config.json")
            except Exception as e:
                logger.debug(f"Could not fetch config.json: {e}")
            
            # Method 2: Try index.min.js (fallback)
            if not policy_key:
                try:
                    player_url = f"https://players.brightcove.net/{account_id}/{player_id}/index.min.js"
                    player_response = await self.http_client.get(player_url)
                    
                    # Try multiple patterns
                    patterns = [
                        r'policyKey["\']:\s*["\']([^"\']+)["\']',
                        r'"policyKey"\s*:\s*"([^"]+)"',
                        r'policy_key["\']:\s*["\']([^"\']+)["\']',
                        r'BCPolicyKey["\']:\s*["\']([^"\']+)["\']',
                    ]
                    
                    for pattern in patterns:
                        policy_match = re.search(pattern, player_response.text)
                        if policy_match:
                            policy_key = policy_match.group(1)
                            logger.info(f"🔑 Extracted Brightcove policy key from index.min.js")
                            break
                except Exception as e:
                    logger.debug(f"Could not extract policy key from JS: {e}")
            
            if not policy_key:
                logger.warning(f"Could not extract Brightcove policy key for account {account_id}")
                # Try a fallback approach with basic metadata
                return {
                    'title': f'Brightcove Video {video_id}',
                    'description': 'Brightcove video (policy key required for full metadata)',
                    'thumbnail_url': None,
                    'duration': 0,
                    'view_count': 0,
                    'channel_title': 'Brightcove',
                    'brightcove_id': video_id,
                    'account_id': account_id
                }
            
            # Use Playback API with policy key
            url = f"https://edge.api.brightcove.com/playback/v1/accounts/{account_id}/videos/{video_id}"
            headers = {
                'Accept': f'application/json;pk={policy_key}'
            }
            
            response = await self.http_client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract thumbnail (first poster or thumbnail)
            thumbnail_url = None
            if data.get('poster'):
                thumbnail_url = data['poster']
            elif data.get('thumbnail'):
                thumbnail_url = data['thumbnail']
            
            # Duration in milliseconds → seconds
            duration = data.get('duration', 0) // 1000 if data.get('duration') else 0
            
            return {
                'title': data.get('name', f'Brightcove Video {video_id}'),
                'description': data.get('description', 'No description available'),
                'thumbnail_url': thumbnail_url,
                'duration': duration,
                'view_count': 0,  # Not available in Playback API
                'channel_title': data.get('account_name', 'Brightcove'),
                'brightcove_id': str(data.get('id', video_id)),
                'account_id': account_id
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Brightcove video not found or private: {video_id}")
            else:
                logger.error(f"Error fetching Brightcove metadata: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching Brightcove metadata: {e}")
            return None
    
    async def get_vimeo_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata from Vimeo using oEmbed API (no auth required)
        Note: Vimeo API v2 is deprecated, oEmbed has limited data
        """
        try:
            # Try oEmbed API (works for public videos)
            url = f"https://vimeo.com/api/oembed.json?url=https://vimeo.com/{video_id}"
            response = await self.http_client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return None
            
            return {
                'title': data.get('title', f'Vimeo Video {video_id}'),
                'description': data.get('description', 'No description available'),
                'thumbnail_url': data.get('thumbnail_url'),
                'duration': data.get('duration', 0),
                'view_count': 0,  # Not available via oEmbed
                'channel_title': data.get('author_name', 'Unknown')
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Vimeo video not found or private: {video_id}")
            else:
                logger.error(f"Error fetching Vimeo metadata: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching Vimeo metadata: {e}")
            return None
    
    def get_link_context(self, link: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract manufacturer, series, and error codes from link context
        Returns dict with manufacturer_id, series_id, related_error_codes
        """
        return {
            'manufacturer_id': link.get('manufacturer_id'),
            'series_id': link.get('series_id'),
            'related_error_codes': link.get('related_error_codes', [])
        }
    
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
            # DEDUPLICATION: Check if video already exists by youtube_id (from ANY link)
            existing = self._get_supabase().table('videos').select('id').eq('youtube_id', metadata['youtube_id']).limit(1).execute()
            
            # Get contextual information from link
            context = self.get_link_context(link)
            
            if existing.data:
                # Video exists from another link! Reuse it
                video_id_to_link = existing.data[0]['id']
                logger.info(f"🔗 Video exists from another link, reusing (dedup)...")
            else:
                # Insert new video
                video_record = self._get_supabase().table('videos').insert({
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
                    'manufacturer_id': context['manufacturer_id'],
                    'series_id': context['series_id'],
                    'related_error_codes': context['related_error_codes'],
                    'metadata': {
                        'enriched_at': datetime.now(timezone.utc).isoformat(),
                        'source': 'youtube_api'
                    }
                }).execute()
                
                if not video_record.data:
                    logger.error("Failed to insert video")
                    return False
                
                video_id_to_link = video_record.data[0]['id']
            
            # Update link with video_id
            self._get_supabase().table('links').update({
                'video_id': video_id_to_link
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
            # DEDUPLICATION: Check if video already exists by vimeo_id (from ANY link)
            # Vimeo ID is stored in metadata JSON
            existing = self._get_supabase().table('videos').select('id').filter('metadata->>vimeo_id', 'eq', video_id).limit(1).execute()
            
            # Get contextual information from link
            context = self.get_link_context(link)
            
            if existing.data:
                # Video exists from another link! Reuse it
                video_id_to_link = existing.data[0]['id']
                logger.info(f"🔗 Video exists from another link, reusing (dedup)...")
            else:
                # Insert new video
                video_record = self._get_supabase().table('videos').insert({
                    'link_id': link['id'],
                    'youtube_id': None,  # Vimeo doesn't use youtube_id
                    'title': metadata['title'],
                    'description': metadata['description'],
                    'thumbnail_url': metadata['thumbnail_url'],
                    'duration': metadata['duration'],
                    'view_count': metadata['view_count'],
                    'channel_title': metadata['channel_title'],
                    'manufacturer_id': context['manufacturer_id'],
                    'series_id': context['series_id'],
                    'related_error_codes': context['related_error_codes'],
                    'metadata': {
                        'enriched_at': datetime.now(timezone.utc).isoformat(),
                        'source': 'vimeo_api',
                        'vimeo_id': video_id
                    }
                }).execute()
                
                if not video_record.data:
                    logger.error("Failed to insert video")
                    return False
                
                video_id_to_link = video_record.data[0]['id']
            
            # Update link with video_id
            self._get_supabase().table('links').update({
                'video_id': video_id_to_link
            }).eq('id', link['id']).execute()
            
            logger.info(f"✅ Enriched Vimeo video: {metadata['title'][:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error saving Vimeo metadata: {e}")
            return False
        
        return False
    
    async def enrich_brightcove_link(self, link: Dict[str, Any]) -> bool:
        """Enrich a Brightcove link with metadata"""
        ids = self.extract_brightcove_ids(link['url'])
        if not ids:
            logger.warning(f"Could not extract Brightcove IDs from: {link['url']}")
            return False
        
        account_id, player_id, video_id = ids
        
        metadata = await self.get_brightcove_metadata(account_id, player_id, video_id)
        if not metadata:
            return False
        
        try:
            # DEDUPLICATION: Check if video already exists by brightcove_id (from ANY link)
            # Brightcove ID is stored in metadata JSON
            existing = self._get_supabase().table('videos').select('id').filter('metadata->>brightcove_id', 'eq', metadata['brightcove_id']).limit(1).execute()
            
            # Get contextual information from link
            context = self.get_link_context(link)
            
            if existing.data:
                # Video exists from another link! Reuse it
                video_id_to_link = existing.data[0]['id']
                logger.info(f"🔗 Video exists from another link, reusing (dedup)...")
            else:
                # Insert new video
                video_record = self._get_supabase().table('videos').insert({
                    'link_id': link['id'],
                    'youtube_id': None,  # Brightcove doesn't use youtube_id
                    'title': metadata['title'],
                    'description': metadata['description'],
                    'thumbnail_url': metadata['thumbnail_url'],
                    'duration': metadata['duration'],
                    'view_count': metadata['view_count'],
                    'channel_title': metadata['channel_title'],
                    'manufacturer_id': context['manufacturer_id'],
                    'series_id': context['series_id'],
                    'related_error_codes': context['related_error_codes'],
                    'metadata': {
                        'enriched_at': datetime.now(timezone.utc).isoformat(),
                        'source': 'brightcove_api',
                        'brightcove_id': metadata['brightcove_id'],
                        'account_id': metadata['account_id']
                    }
                }).execute()
                
                if not video_record.data:
                    logger.error("Failed to insert video")
                    return False
                
                video_id_to_link = video_record.data[0]['id']
            
            # Update link with video_id
            self._get_supabase().table('links').update({
                'video_id': video_id_to_link
            }).eq('id', link['id']).execute()
            
            logger.info(f"✅ Enriched Brightcove video: {metadata['title'][:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error saving Brightcove metadata: {e}")
            return False
        
        return False
    
    async def enrich_link(self, link: Dict[str, Any]) -> bool:
        """Enrich a video link based on its type"""
        url = link['url']
        
        if 'youtube.com' in url or 'youtu.be' in url:
            return await self.enrich_youtube_link(link)
        elif 'vimeo.com' in url:
            return await self.enrich_vimeo_link(link)
        elif 'brightcove.net' in url:
            return await self.enrich_brightcove_link(link)
        else:
            logger.info(f"⏭️  Skipping unsupported video platform: {url}")
            return False
    
    async def process_unenriched_links(self, limit: Optional[int] = None, force: bool = False):
        """Process all unenriched video links"""
        logger.info("🔍 Finding video links to enrich...")
        
        try:
            # Query for video links without video_id
            query = self._get_supabase().table('links').select('*')
            
            if not force:
                query = query.is_('video_id', 'null')
            
            query = query.in_('link_type', ['video', 'youtube', 'vimeo', 'brightcove'])
            
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
