"""
Manufacturer Utilities
======================
Centralized manufacturer management functions
"""

from typing import Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


def ensure_manufacturer_exists(manufacturer_name: str, supabase) -> Optional[UUID]:
    """
    Ensure manufacturer exists in database, create if needed
    
    This function is used across all stages to auto-create manufacturers
    when they are detected but not yet in the database.
    
    Args:
        manufacturer_name: Name of manufacturer (e.g., "HP", "Lexmark", "Konica Minolta")
        supabase: Supabase client instance
        
    Returns:
        manufacturer_id (UUID) if found/created, None if failed
        
    Raises:
        Exception: If manufacturer cannot be created
    """
    if not manufacturer_name or manufacturer_name == "AUTO":
        return None
    
    try:
        # 1. Try exact match first
        result = supabase.table('manufacturers') \
            .select('id,name') \
            .eq('name', manufacturer_name) \
            .limit(1) \
            .execute()
        
        if result.data:
            manufacturer_id = result.data[0]['id']
            logger.debug(f"✅ Found manufacturer: {manufacturer_name} (ID: {manufacturer_id})")
            return manufacturer_id
        
        # 2. Try case-insensitive match
        result = supabase.table('manufacturers') \
            .select('id,name') \
            .ilike('name', manufacturer_name) \
            .limit(1) \
            .execute()
        
        if result.data:
            manufacturer_id = result.data[0]['id']
            logger.debug(f"✅ Found manufacturer (ilike): {result.data[0]['name']} (ID: {manufacturer_id})")
            return manufacturer_id
        
        # 3. Try partial match
        result = supabase.table('manufacturers') \
            .select('id,name') \
            .ilike('name', f'%{manufacturer_name}%') \
            .limit(1) \
            .execute()
        
        if result.data:
            manufacturer_id = result.data[0]['id']
            logger.debug(f"✅ Found manufacturer (partial): {result.data[0]['name']} (ID: {manufacturer_id})")
            return manufacturer_id
        
        # 4. Manufacturer not found - create new entry
        logger.info(f"🔨 Creating new manufacturer: {manufacturer_name}")
        
        create_result = supabase.table('manufacturers') \
            .insert({
                'name': manufacturer_name,
                'is_active': True
            }) \
            .execute()
        
        if create_result.data:
            manufacturer_id = create_result.data[0]['id']
            logger.info(f"✅ Created manufacturer: {manufacturer_name} (ID: {manufacturer_id})")
            return manufacturer_id
        else:
            logger.error(f"❌ Failed to create manufacturer: {manufacturer_name}")
            return None
    
    except Exception as e:
        logger.error(f"❌ Error ensuring manufacturer exists: {e}")
        return None


def detect_manufacturer_from_domain(domain: str, supabase) -> Optional[UUID]:
    """
    Detect manufacturer from URL domain and ensure it exists
    
    Args:
        domain: Domain name (e.g., 'publications.lexmark.com')
        supabase: Supabase client instance
        
    Returns:
        manufacturer_id (UUID) or None
    """
    # Domain to manufacturer mapping
    domain_mapping = {
        'lexmark.com': 'Lexmark',
        'publications.lexmark.com': 'Lexmark',
        'hp.com': 'HP',
        'support.hp.com': 'HP',
        'kyoceradocumentsolutions.com': 'Kyocera',
        'kyocera.com': 'Kyocera',
        'ricoh.com': 'Ricoh',
        'brother.com': 'Brother',
        'canon.com': 'Canon',
        'epson.com': 'Epson',
        'xerox.com': 'Xerox',
        'konica-minolta.com': 'Konica Minolta',
        'konicaminolta.com': 'Konica Minolta',
        'sharp.com': 'Sharp',
        'toshiba.com': 'Toshiba',
        'oki.com': 'OKI',
        'samsung.com': 'Samsung',
        'dell.com': 'Dell'
    }
    
    domain_lower = domain.lower()
    
    # Check for domain match
    for domain_key, manufacturer_name in domain_mapping.items():
        if domain_key in domain_lower:
            logger.info(f"🔍 Domain matched: {domain_key} → {manufacturer_name}")
            return ensure_manufacturer_exists(manufacturer_name, supabase)
    
    logger.debug(f"ℹ️ No manufacturer detected from domain: {domain}")
    return None
