"""
OEM Relationships Sync Utility
===============================

Syncs OEM mappings from oem_mappings.py to the database.
Also updates products table with OEM information.

Usage:
    from backend.utils.oem_sync import sync_oem_relationships_to_db
    
    sync_oem_relationships_to_db(supabase)
"""

import re
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from config.oem_mappings import OEM_MAPPINGS, get_oem_manufacturer, get_oem_info

logger = logging.getLogger(__name__)


def sync_oem_relationships_to_db(supabase) -> Dict[str, int]:
    """
    Sync OEM mappings from oem_mappings.py to database
    
    Args:
        supabase: Supabase client instance
        
    Returns:
        Dictionary with sync statistics
    """
    stats = {
        'total_mappings': len(OEM_MAPPINGS),
        'inserted': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    
    logger.info(f"Syncing {stats['total_mappings']} OEM mappings to database...")
    
    for (brand, pattern), mapping in OEM_MAPPINGS.items():
        try:
            # Check if mapping already exists
            existing = supabase.table('oem_relationships') \
                .select('id') \
                .eq('brand_manufacturer', brand) \
                .eq('brand_series_pattern', pattern) \
                .eq('oem_manufacturer', mapping['oem_manufacturer']) \
                .execute()
            
            data = {
                'brand_manufacturer': brand,
                'brand_series_pattern': pattern,
                'oem_manufacturer': mapping['oem_manufacturer'],
                'relationship_type': 'engine',  # Default type
                'applies_to': mapping.get('applies_to', ['error_codes', 'parts']),
                'notes': mapping.get('notes', ''),
                'confidence': 1.0,  # High confidence for manually curated mappings
                'source': 'oem_mappings.py',
                'verified': True
            }
            
            if existing.data:
                # Update existing
                supabase.table('oem_relationships') \
                    .update(data) \
                    .eq('id', existing.data[0]['id']) \
                    .execute()
                stats['updated'] += 1
                logger.debug(f"Updated: {brand} {pattern} → {mapping['oem_manufacturer']}")
            else:
                # Insert new
                supabase.table('oem_relationships') \
                    .insert(data) \
                    .execute()
                stats['inserted'] += 1
                logger.debug(f"Inserted: {brand} {pattern} → {mapping['oem_manufacturer']}")
        
        except Exception as e:
            stats['errors'] += 1
            logger.error(f"Error syncing {brand} {pattern}: {e}")
    
    logger.info(f"Sync complete: {stats['inserted']} inserted, {stats['updated']} updated, {stats['errors']} errors")
    return stats


def update_product_oem_info(supabase, product_id: UUID, manufacturer: str, model_or_series: str) -> bool:
    """
    Update a product with OEM information
    
    Args:
        supabase: Supabase client instance
        product_id: UUID of product to update
        manufacturer: Brand manufacturer name
        model_or_series: Model or series name
        
    Returns:
        True if updated, False otherwise
    """
    try:
        # Get OEM info
        oem_info = get_oem_info(manufacturer, model_or_series)
        
        if not oem_info:
            # No OEM relationship
            return False
        
        # Update product using direct SQL via postgrest (bypasses schema cache issues)
        # Use parameterized query for safety
        from supabase._sync.client import SyncClient
        import requests
        
        # Get Supabase URL and key from client
        url = supabase.supabase_url
        key = supabase.supabase_key
        
        # Direct REST API call with proper headers
        response = requests.patch(
            f"{url}/rest/v1/products",
            params={"id": f"eq.{str(product_id)}"},
            json={
                "oem_manufacturer": oem_info['oem_manufacturer'],
                "oem_relationship_type": "engine",
                "oem_notes": oem_info['notes']
            },
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
        )
        
        if response.status_code not in [200, 204]:
            raise Exception(f"Update failed: {response.text}")
        
        logger.info(f"Updated product {product_id} with OEM: {oem_info['oem_manufacturer']}")
        return True
    
    except Exception as e:
        logger.error(f"Error updating product {product_id} OEM info: {e}")
        return False


def batch_update_products_oem_info(supabase, limit: int = 1000) -> Dict[str, int]:
    """
    Batch update all products with OEM information
    
    Args:
        supabase: Supabase client instance
        limit: Maximum number of products to process
        
    Returns:
        Dictionary with update statistics
    """
    stats = {
        'total_products': 0,
        'updated': 0,
        'no_oem': 0,
        'errors': 0
    }
    
    logger.info("Batch updating products with OEM information...")
    
    try:
        # Get all products
        result = supabase.table('products') \
            .select('id,manufacturer_id,model_name,series_name') \
            .limit(limit) \
            .execute()
        
        if not result.data:
            logger.info("No products found")
            return stats
        
        stats['total_products'] = len(result.data)
        
        # Get manufacturer names
        manufacturer_ids = list(set(p['manufacturer_id'] for p in result.data if p.get('manufacturer_id')))
        manufacturers = {}
        
        for mfr_id in manufacturer_ids:
            mfr_result = supabase.table('manufacturers') \
                .select('id,name') \
                .eq('id', mfr_id) \
                .execute()
            if mfr_result.data:
                manufacturers[mfr_id] = mfr_result.data[0]['name']
        
        # Update each product
        for product in result.data:
            try:
                manufacturer_name = manufacturers.get(product.get('manufacturer_id'))
                if not manufacturer_name:
                    stats['no_oem'] += 1
                    continue
                
                model_or_series = product.get('series_name') or product.get('model_name')
                if not model_or_series:
                    stats['no_oem'] += 1
                    continue
                
                # Update OEM info
                if update_product_oem_info(supabase, product['id'], manufacturer_name, model_or_series):
                    stats['updated'] += 1
                else:
                    stats['no_oem'] += 1
            
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error processing product {product.get('id')}: {e}")
        
        logger.info(f"Batch update complete: {stats['updated']}/{stats['total_products']} products updated")
    
    except Exception as e:
        logger.error(f"Error in batch update: {e}")
        stats['errors'] += 1
    
    return stats


def get_oem_equivalent_manufacturers(manufacturer: str, model_or_series: str) -> List[str]:
    """
    Get list of equivalent manufacturers for cross-OEM search
    
    Args:
        manufacturer: Brand manufacturer name
        model_or_series: Model or series name
        
    Returns:
        List of manufacturer names to search (includes original + OEM)
        
    Example:
        >>> get_oem_equivalent_manufacturers("Konica Minolta", "5000i")
        ["Konica Minolta", "Brother"]
    """
    manufacturers = [manufacturer]  # Always include original
    
    # Get OEM manufacturer
    oem = get_oem_manufacturer(manufacturer, model_or_series, for_purpose='error_codes')
    if oem and oem != manufacturer:
        manufacturers.append(oem)
    
    return manufacturers


def expand_search_query_with_oem(
    manufacturer: str, 
    model_or_series: str, 
    search_query: str
) -> List[str]:
    """
    Expand search query to include OEM equivalents
    
    Args:
        manufacturer: Brand manufacturer name
        model_or_series: Model or series name
        search_query: Original search query
        
    Returns:
        List of expanded search queries
        
    Example:
        >>> expand_search_query_with_oem("Konica Minolta", "5000i", "error C4080")
        [
            "Konica Minolta 5000i error C4080",
            "Brother 5000i error C4080",
            "Brother error C4080"
        ]
    """
    queries = [search_query]  # Original query
    
    # Get OEM manufacturer
    oem = get_oem_manufacturer(manufacturer, model_or_series, for_purpose='error_codes')
    
    if oem and oem != manufacturer:
        # Add OEM-specific queries
        queries.append(search_query.replace(manufacturer, oem))
        
        # Add query without model (just OEM + search terms)
        if model_or_series in search_query:
            oem_query = search_query.replace(manufacturer, oem).replace(model_or_series, '').strip()
            queries.append(oem_query)
    
    return queries


if __name__ == '__main__':
    # Test/demo mode
    print("=" * 80)
    print("OEM Relationships Sync Utility")
    print("=" * 80)
    
    # Test get_oem_equivalent_manufacturers
    test_cases = [
        ("Konica Minolta", "5000i"),
        ("Lexmark", "CS943"),
        ("UTAX", "P-4020"),
        ("Xerox", "Versant 280"),
    ]
    
    print("\nTest: get_oem_equivalent_manufacturers()")
    print("-" * 80)
    for brand, model in test_cases:
        manufacturers = get_oem_equivalent_manufacturers(brand, model)
        print(f"{brand} {model}:")
        print(f"  → Search manufacturers: {manufacturers}")
    
    # Test expand_search_query_with_oem
    print("\nTest: expand_search_query_with_oem()")
    print("-" * 80)
    query = "error code C4080 solution"
    for brand, model in test_cases:
        queries = expand_search_query_with_oem(brand, model, f"{brand} {model} {query}")
        print(f"\n{brand} {model} {query}:")
        for i, q in enumerate(queries, 1):
            print(f"  {i}. {q}")
