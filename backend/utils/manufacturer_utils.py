"""
Manufacturer Utilities
======================
Centralized manufacturer, product, and series management functions
Auto-creates entities when detected but not in database
"""

from typing import Optional, List, Dict, Any
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


def ensure_series_exists(
    series_name: str, 
    manufacturer_id: UUID, 
    supabase
) -> Optional[UUID]:
    """
    Ensure product series exists in database, create if needed
    
    Args:
        series_name: Name of series (e.g., "LaserJet Pro", "CS900")
        manufacturer_id: UUID of manufacturer
        supabase: Supabase client instance
        
    Returns:
        series_id (UUID) or None
    """
    if not series_name or not manufacturer_id:
        return None
    
    try:
        # 1. Try to find existing series
        result = supabase.table('product_series') \
            .select('id,name') \
            .eq('manufacturer_id', str(manufacturer_id)) \
            .ilike('name', series_name) \
            .limit(1) \
            .execute()
        
        if result.data:
            series_id = result.data[0]['id']
            logger.debug(f"✅ Found series: {series_name} (ID: {series_id})")
            return series_id
        
        # 2. Series not found - create new entry
        logger.info(f"🔨 Creating new series: {series_name}")
        
        create_result = supabase.table('product_series') \
            .insert({
                'name': series_name,
                'manufacturer_id': str(manufacturer_id),
                'is_active': True
            }) \
            .execute()
        
        if create_result.data:
            series_id = create_result.data[0]['id']
            logger.info(f"✅ Created series: {series_name} (ID: {series_id})")
            return series_id
        else:
            logger.error(f"❌ Failed to create series: {series_name}")
            return None
    
    except Exception as e:
        logger.error(f"❌ Error ensuring series exists: {e}")
        return None


def ensure_product_exists(
    model_name: str,
    manufacturer_id: UUID,
    series_id: Optional[UUID] = None,
    supabase = None
) -> Optional[UUID]:
    """
    Ensure product exists in database, create if needed
    
    Args:
        model_name: Model name (e.g., "CS943", "CX94X")
        manufacturer_id: UUID of manufacturer
        series_id: Optional UUID of series
        supabase: Supabase client instance
        
    Returns:
        product_id (UUID) or None
    """
    if not model_name or not manufacturer_id:
        return None
    
    try:
        # 1. Try to find existing product
        result = supabase.table('products') \
            .select('id,model_name') \
            .eq('manufacturer_id', str(manufacturer_id)) \
            .ilike('model_name', model_name) \
            .limit(1) \
            .execute()
        
        if result.data:
            product_id = result.data[0]['id']
            logger.debug(f"✅ Found product: {model_name} (ID: {product_id})")
            return product_id
        
        # 2. Product not found - create new entry
        logger.info(f"🔨 Creating new product: {model_name}")
        
        product_data = {
            'model_name': model_name,
            'manufacturer_id': str(manufacturer_id),
            'is_active': True
        }
        
        if series_id:
            product_data['series_id'] = str(series_id)
        
        create_result = supabase.table('products') \
            .insert(product_data) \
            .execute()
        
        if create_result.data:
            product_id = create_result.data[0]['id']
            logger.info(f"✅ Created product: {model_name} (ID: {product_id})")
            return product_id
        else:
            logger.error(f"❌ Failed to create product: {model_name}")
            return None
    
    except Exception as e:
        logger.error(f"❌ Error ensuring product exists: {e}")
        return None


def link_video_to_products(
    video_id: UUID,
    model_names: List[str],
    manufacturer_id: UUID,
    supabase
) -> List[UUID]:
    """
    Link video to products, auto-creating products if needed
    
    Args:
        video_id: UUID of video
        model_names: List of model names (e.g., ['CS943', 'CX94X'])
        manufacturer_id: UUID of manufacturer
        supabase: Supabase client instance
        
    Returns:
        List of product IDs that were linked
    """
    if not video_id or not model_names or not manufacturer_id:
        return []
    
    linked_products = []
    
    for model_name in model_names:
        try:
            # Ensure product exists
            product_id = ensure_product_exists(model_name, manufacturer_id, None, supabase)
            
            if product_id:
                # Check if link already exists
                existing = supabase.table('video_products') \
                    .select('id') \
                    .eq('video_id', str(video_id)) \
                    .eq('product_id', str(product_id)) \
                    .limit(1) \
                    .execute()
                
                if not existing.data:
                    # Create link
                    supabase.table('video_products') \
                        .insert({
                            'video_id': str(video_id),
                            'product_id': str(product_id)
                        }) \
                        .execute()
                    
                    logger.info(f"🔗 Linked video to product: {model_name}")
                
                linked_products.append(product_id)
        
        except Exception as e:
            logger.error(f"❌ Error linking video to product {model_name}: {e}")
    
    return linked_products
