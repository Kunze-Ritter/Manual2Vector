"""
Link Checker Service
Wraps the link checker script for use in the API
"""

import logging
import sys
import os
from typing import Optional, Dict, Any

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from check_and_fix_links import LinkChecker

logger = logging.getLogger(__name__)


class LinkCheckerService:
    """Service for checking and fixing broken links"""
    
    def __init__(self):
        """Initialize link checker service"""
        self.checker = None
        logger.info("✅ Link Checker Service initialized")
    
    async def check_links(
        self, 
        limit: Optional[int] = None, 
        check_only: bool = True,
        check_inactive: bool = False
    ) -> Dict[str, Any]:
        """
        Check links for validity and optionally fix broken ones
        
        Args:
            limit: Maximum number of links to check
            check_only: Only check without fixing (default: True)
            check_inactive: Also check inactive links (default: False)
            
        Returns:
            Dictionary with check results
        """
        try:
            logger.info(f"🔗 Starting link check (limit={limit}, check_only={check_only})")
            
            # Create checker instance
            checker = LinkChecker(check_only=check_only)
            
            # Process links
            await checker.process_links(limit=limit, check_inactive=check_inactive)
            
            # Get results
            result = {
                "checked": checker.checked_count,
                "working": checker.valid_count,
                "broken": checker.broken_count,
                "fixed": checker.fixed_count,
                "errors": checker.error_count
            }
            
            # Close checker
            await checker.close()
            
            logger.info(f"✅ Link check complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in link check: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for link checker service"""
        try:
            return {
                "status": "healthy",
                "features": {
                    "url_cleaning": True,
                    "redirect_following": True,
                    "auto_fixing": True,
                    "common_fixes": ["https/http", "www", "trailing_slash", "url_encoding"]
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
