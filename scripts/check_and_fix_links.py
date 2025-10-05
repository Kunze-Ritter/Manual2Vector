#!/usr/bin/env python3
"""
Link Checker & Fixer Script
============================
Checks links for validity and attempts to fix broken links.

Features:
- HTTP status check (200, 404, etc.)
- Multiline link detection and fixing
- URL encoding fixes
- Redirect following
- Batch processing with rate limiting
- Auto-update database with fixed links

Usage:
    python scripts/check_and_fix_links.py [--check-only] [--limit 10]
    
Options:
    --check-only    Only check links, don't fix them
    --limit N       Check only N links (default: all)
    --inactive      Also check inactive links
"""

import os
import re
import sys
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from urllib.parse import urlparse, quote, unquote

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
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


class LinkChecker:
    """Checks and fixes broken links"""
    
    def __init__(self, check_only: bool = False):
        self.check_only = check_only
        self.http_client = httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        # Statistics
        self.checked_count = 0
        self.valid_count = 0
        self.broken_count = 0
        self.fixed_count = 0
        self.error_count = 0
        
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
    
    def is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def fix_multiline_url(self, url: str, document_text: str = None) -> Optional[str]:
        """
        Attempt to fix URLs that were split across lines.
        Common patterns:
        - URL ends abruptly without TLD
        - Spaces in URL (should be %20)
        - Missing protocol
        """
        
        # Remove whitespace
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            # Try https first
            fixed = f"https://{url}"
            if self.is_valid_url(fixed):
                return fixed
        
        # Fix common encoding issues
        # Replace spaces with %20
        if ' ' in url:
            fixed = url.replace(' ', '%20')
            if self.is_valid_url(fixed):
                return fixed
        
        # Remove line breaks
        if '\n' in url or '\r' in url:
            fixed = url.replace('\n', '').replace('\r', '')
            if self.is_valid_url(fixed):
                return fixed
        
        return None
    
    def try_common_fixes(self, url: str) -> List[str]:
        """Generate list of potential fixes for a broken URL"""
        fixes = []
        
        # Original
        fixes.append(url)
        
        # Add/change protocol
        if url.startswith('http://'):
            fixes.append(url.replace('http://', 'https://'))
        elif url.startswith('https://'):
            fixes.append(url.replace('https://', 'http://'))
        else:
            fixes.append(f"https://{url}")
            fixes.append(f"http://{url}")
        
        # Remove trailing slashes or add them
        if url.endswith('/'):
            fixes.append(url.rstrip('/'))
        else:
            fixes.append(f"{url}/")
        
        # URL decode and re-encode
        try:
            decoded = unquote(url)
            if decoded != url:
                fixes.append(decoded)
        except:
            pass
        
        # Remove www or add it
        parsed = urlparse(url)
        if parsed.netloc.startswith('www.'):
            fixed = url.replace('www.', '', 1)
            fixes.append(fixed)
        else:
            fixed = url.replace('://', '://www.', 1)
            fixes.append(fixed)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_fixes = []
        for fix in fixes:
            if fix not in seen and self.is_valid_url(fix):
                seen.add(fix)
                unique_fixes.append(fix)
        
        return unique_fixes
    
    async def check_url(self, url: str) -> Tuple[int, str, Optional[str]]:
        """
        Check if URL is accessible.
        Returns: (status_code, status_text, final_url)
        """
        if not self.is_valid_url(url):
            return (0, "Invalid URL", None)
        
        try:
            response = await self.http_client.head(url)
            return (response.status_code, "OK" if response.is_success else "Error", str(response.url))
        except httpx.HTTPStatusError as e:
            return (e.response.status_code, str(e), None)
        except httpx.ConnectError:
            return (0, "Connection failed", None)
        except httpx.TimeoutException:
            return (0, "Timeout", None)
        except Exception as e:
            return (0, str(e), None)
    
    async def find_working_url(self, original_url: str) -> Optional[Tuple[str, int, str]]:
        """
        Try to find a working version of the URL.
        Returns: (working_url, status_code, method) or None
        """
        
        # First check original
        status, msg, final_url = await self.check_url(original_url)
        if 200 <= status < 400:
            return (final_url or original_url, status, "original")
        
        # Try common fixes
        fixes = self.try_common_fixes(original_url)
        
        for i, fixed_url in enumerate(fixes[1:], 1):  # Skip first (original)
            status, msg, final_url = await self.check_url(fixed_url)
            if 200 <= status < 400:
                logger.info(f"   ✅ Found working URL: {fixed_url}")
                return (final_url or fixed_url, status, f"fix_{i}")
            
            # Rate limiting
            await asyncio.sleep(0.2)
        
        return None
    
    async def check_and_fix_link(self, link: Dict[str, Any]) -> Dict[str, Any]:
        """Check a link and attempt to fix if broken"""
        url = link['url']
        link_id = link['id']
        
        logger.info(f"\n🔗 Checking: {url[:80]}...")
        
        result = {
            'id': link_id,
            'original_url': url,
            'status': 'unknown',
            'status_code': 0,
            'fixed_url': None,
            'needs_update': False,
            'error': None
        }
        
        try:
            # Check current URL
            status, msg, final_url = await self.check_url(url)
            result['status_code'] = status
            
            if 200 <= status < 400:
                # Link is working
                result['status'] = 'working'
                logger.info(f"   ✅ Working (Status: {status})")
                self.valid_count += 1
                
                # Check if redirected
                if final_url and final_url != url:
                    logger.info(f"   🔀 Redirects to: {final_url}")
                    result['fixed_url'] = final_url
                    result['needs_update'] = True
                
            else:
                # Link is broken
                result['status'] = 'broken'
                logger.warning(f"   ❌ Broken (Status: {status}, {msg})")
                self.broken_count += 1
                
                if not self.check_only:
                    # Try to fix
                    logger.info("   🔧 Attempting to fix...")
                    working = await self.find_working_url(url)
                    
                    if working:
                        fixed_url, new_status, method = working
                        result['fixed_url'] = fixed_url
                        result['status_code'] = new_status
                        result['status'] = 'fixed'
                        result['needs_update'] = True
                        logger.info(f"   ✅ Fixed! New URL: {fixed_url}")
                        self.fixed_count += 1
                    else:
                        logger.warning(f"   ⚠️  Could not fix link")
            
            self.checked_count += 1
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            logger.error(f"   ❌ Error: {e}")
            self.error_count += 1
        
        return result
    
    async def update_link(self, link_id: str, new_url: str, old_url: str):
        """Update link in database"""
        try:
            supabase.table('links').update({
                'url': new_url,
                'metadata': {
                    'fixed_at': datetime.utcnow().isoformat(),
                    'original_url': old_url,
                    'fixed_by': 'link_checker_script'
                }
            }).eq('id', link_id).execute()
            
            logger.info(f"   💾 Database updated")
            
        except Exception as e:
            logger.error(f"   ❌ Failed to update database: {e}")
    
    async def deactivate_link(self, link_id: str):
        """Mark link as inactive"""
        try:
            supabase.table('links').update({
                'is_active': False,
                'metadata': {
                    'deactivated_at': datetime.utcnow().isoformat(),
                    'reason': 'broken_link_404'
                }
            }).eq('id', link_id).execute()
            
            logger.info(f"   💾 Link marked as inactive")
            
        except Exception as e:
            logger.error(f"   ❌ Failed to deactivate link: {e}")
    
    async def process_links(self, limit: Optional[int] = None, check_inactive: bool = False):
        """Process all links"""
        logger.info("🔍 Finding links to check...")
        
        try:
            # Query links
            query = supabase.table('links').select('id,url,link_type,is_active')
            
            # Note: is_active might be NULL (default), so we include NULL and TRUE
            # PostgREST doesn't have OR directly, so we use 'or' filter syntax
            if not check_inactive:
                # Include links where is_active is NULL or TRUE (exclude only FALSE)
                query = query.or_('is_active.is.null,is_active.eq.true')
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            links = response.data
            
            logger.info(f"📊 Query returned {len(links) if links else 0} links")
            
            if not links:
                logger.info("✅ No links found to check!")
                logger.info("ℹ️  Try: --inactive flag to check all links")
                return
            
            logger.info(f"🔗 Found {len(links)} links to check")
            
            results = []
            
            for i, link in enumerate(links, 1):
                logger.info(f"\n{'='*80}")
                logger.info(f"[{i}/{len(links)}]")
                
                result = await self.check_and_fix_link(link)
                results.append(result)
                
                # Update database if needed
                if result['needs_update'] and not self.check_only:
                    await self.update_link(
                        result['id'],
                        result['fixed_url'],
                        result['original_url']
                    )
                
                # Deactivate if permanently broken
                if result['status'] == 'broken' and result['status_code'] == 404:
                    if not self.check_only:
                        await self.deactivate_link(result['id'])
                
                # Rate limiting
                await asyncio.sleep(0.5)
            
            # Summary
            logger.info(f"\n{'='*80}")
            logger.info(f"📊 SUMMARY")
            logger.info(f"{'='*80}")
            logger.info(f"   Total checked: {self.checked_count}")
            logger.info(f"   ✅ Working: {self.valid_count}")
            logger.info(f"   ❌ Broken: {self.broken_count}")
            logger.info(f"   🔧 Fixed: {self.fixed_count}")
            logger.info(f"   ⚠️  Errors: {self.error_count}")
            logger.info(f"{'='*80}")
            
            # Show broken links
            broken = [r for r in results if r['status'] == 'broken']
            if broken:
                logger.info(f"\n❌ BROKEN LINKS ({len(broken)}):")
                for r in broken:
                    logger.info(f"   [{r['status_code']}] {r['original_url']}")
            
        except Exception as e:
            logger.error(f"Error processing links: {e}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check and fix broken links')
    parser.add_argument('--check-only', action='store_true', help='Only check, do not fix')
    parser.add_argument('--limit', type=int, help='Limit number of links to check')
    parser.add_argument('--inactive', action='store_true', help='Also check inactive links')
    args = parser.parse_args()
    
    if args.check_only:
        logger.info("ℹ️  Running in CHECK ONLY mode (no fixes will be applied)")
    
    checker = LinkChecker(check_only=args.check_only)
    
    try:
        await checker.process_links(limit=args.limit, check_inactive=args.inactive)
    finally:
        await checker.close()


if __name__ == '__main__':
    asyncio.run(main())
