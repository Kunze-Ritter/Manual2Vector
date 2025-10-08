"""Link Cleaner

Cleans and validates extracted URLs.
"""

import re
from typing import Optional
from urllib.parse import urlparse


def clean_url(url: str) -> Optional[str]:
    """
    Clean and validate URL
    
    Args:
        url: Raw URL string
        
    Returns:
        Cleaned URL or None if invalid
    """
    if not url:
        return None
    
    # Remove whitespace
    url = url.strip()
    
    # Remove trailing punctuation (., ), ], }, etc.)
    url = re.sub(r'[.,;:)\]}]+$', '', url)
    
    # Remove leading punctuation
    url = re.sub(r'^[.,;:(\[{]+', '', url)
    
    # Fix common issues
    url = url.replace(' ', '')  # Remove spaces
    url = url.replace('\n', '')  # Remove newlines
    url = url.replace('\r', '')  # Remove carriage returns
    
    # Ensure it starts with http:// or https://
    if not url.startswith(('http://', 'https://')):
        if url.startswith('www.'):
            url = 'https://' + url
        else:
            # Might be a relative URL or invalid
            return None
    
    # Validate URL structure
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return None
        
        # Check for common invalid patterns
        if '..' in url:
            return None
        
        return url
    except:
        return None


def is_valid_video_url(url: str) -> bool:
    """
    Check if URL is a valid video URL
    
    Args:
        url: URL to check
        
    Returns:
        True if valid video URL
    """
    if not url:
        return False
    
    video_domains = [
        'youtube.com',
        'youtu.be',
        'vimeo.com',
        'dailymotion.com',
        'wistia.com',
        'brightcove.com',
        'kaltura.com'
    ]
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check if domain matches any video platform
        return any(vd in domain for vd in video_domains)
    except:
        return False


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from URL
    
    Args:
        url: Video URL
        
    Returns:
        Video ID or None
    """
    if not url:
        return None
    
    # YouTube
    youtube_patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in youtube_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Vimeo
    vimeo_match = re.search(r'vimeo\.com\/(\d+)', url)
    if vimeo_match:
        return vimeo_match.group(1)
    
    return None


def merge_multiline_url(line1: str, line2: str) -> Optional[str]:
    """
    Merge URL that spans multiple lines
    
    Args:
        line1: First line
        line2: Second line
        
    Returns:
        Merged URL or None
    """
    # Check if line1 looks like start of URL
    if not re.search(r'https?://', line1):
        return None
    
    # Merge and clean
    merged = line1.strip() + line2.strip()
    return clean_url(merged)


if __name__ == '__main__':
    # Test cases
    test_urls = [
        'https://www.hp.com/buy/parts.',
        'https://www.youtube.com/watch?v=abc123)',
        'www.example.com',
        'https://youtu.be/abc123]',
        'https://support.hp.com/us-en/document/c12345',
        'http://example.com/path/to/page.html.',
    ]
    
    print("URL Cleaning Tests:")
    print("=" * 80)
    for url in test_urls:
        cleaned = clean_url(url)
        print(f"Original: {url}")
        print(f"Cleaned:  {cleaned}")
        print()
