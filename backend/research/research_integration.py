"""
Research Integration Helper
============================

Integrates ProductResearcher into existing pipeline
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID

from research.product_researcher import ProductResearcher


logger = logging.getLogger(__name__)


class ResearchIntegration:
    """
    Helper class to integrate research into product processing
    """
    
    def __init__(self, supabase, enabled: bool = True):
        """
        Initialize integration
        
        Args:
            supabase: Supabase client
            enabled: Enable/disable research (can be controlled via env var)
        """
        self.supabase = supabase
        self.enabled = enabled
        self.researcher = ProductResearcher(supabase=supabase) if enabled else None
        
        logger.info(f"ResearchIntegration initialized (enabled: {enabled})")
    
    def enrich_product(
        self,
        product_id: UUID,
        manufacturer_name: str,
        model_number: str,
        current_confidence: float = 0.0
    ) -> bool:
        """
        Enrich product with online research
        
        Triggers research if:
        - Product has low confidence (< 0.7)
        - Product has no series
        - Product has no specs
        
        Args:
            product_id: Product UUID
            manufacturer_name: Manufacturer name
            model_number: Model number
            current_confidence: Current extraction confidence
            
        Returns:
            True if enriched, False otherwise
        """
        if not self.enabled or not self.researcher:
            return False
        
        # Get current product data
        try:
            product = self.supabase.table('products').select(
                'id,series_id,specifications,oem_manufacturer'
            ).eq('id', str(product_id)).single().execute()
            
            if not product.data:
                return False
            
            product_data = product.data
            
            # Decide if research is needed
            needs_research = (
                current_confidence < 0.7 or  # Low confidence
                not product_data.get('series_id') or  # No series
                not product_data.get('specifications') or  # No specs
                not product_data.get('oem_manufacturer')  # No OEM
            )
            
            if not needs_research:
                logger.debug(f"Product {model_number} doesn't need research")
                return False
            
            logger.info(f"🔍 Researching product: {manufacturer_name} {model_number}")
            
            # Perform research
            research = self.researcher.research_product(
                manufacturer=manufacturer_name,
                model_number=model_number
            )
            
            if not research:
                logger.warning(f"Research failed for {manufacturer_name} {model_number}")
                return False
            
            # Update product with research results
            self._apply_research_to_product(product_id, research)
            
            logger.info(f"✅ Product enriched with research (confidence: {research.get('confidence', 0):.2f})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enrich product: {e}")
            return False
    
    def _apply_research_to_product(self, product_id: UUID, research: Dict[str, Any]):
        """
        Apply research results to product
        
        Updates:
        - specifications (JSONB)
        - oem_manufacturer
        - oem_notes
        - series (if found)
        """
        try:
            update_data = {}
            
            # Specifications
            if research.get('specifications'):
                update_data['specifications'] = research['specifications']
            
            # Physical specs (merge into specifications)
            if research.get('physical_specs'):
                if 'specifications' not in update_data:
                    update_data['specifications'] = {}
                update_data['specifications']['physical'] = research['physical_specs']
            
            # OEM info
            if research.get('oem_manufacturer'):
                update_data['oem_manufacturer'] = research['oem_manufacturer']
                update_data['oem_relationship_type'] = 'engine'
                update_data['oem_notes'] = research.get('oem_notes', '')
            
            # Product type (if more specific)
            if research.get('product_type'):
                update_data['product_type'] = research['product_type']
            
            # Update product
            if update_data:
                self.supabase.table('products').update(update_data).eq(
                    'id', str(product_id)
                ).execute()
                
                logger.debug(f"Updated product {product_id} with {len(update_data)} fields")
            
            # Try to link series (if series_name found)
            if research.get('series_name'):
                self._link_series(product_id, research['series_name'])
            
        except Exception as e:
            logger.error(f"Failed to apply research: {e}")
    
    def _link_series(self, product_id: UUID, series_name: str):
        """
        Try to link product to series
        
        Creates series if it doesn't exist
        """
        try:
            # Check if series exists
            series_result = self.supabase.table('product_series').select('id').eq(
                'series_name', series_name
            ).limit(1).execute()
            
            if series_result.data:
                # Link to existing series
                series_id = series_result.data[0]['id']
                self.supabase.table('products').update({
                    'series_id': series_id
                }).eq('id', str(product_id)).execute()
                
                logger.debug(f"Linked product to existing series: {series_name}")
            else:
                # Create new series
                new_series = self.supabase.table('product_series').insert({
                    'series_name': series_name,
                    'source': 'online_research'
                }).execute()
                
                if new_series.data:
                    series_id = new_series.data[0]['id']
                    self.supabase.table('products').update({
                        'series_id': series_id
                    }).eq('id', str(product_id)).execute()
                    
                    logger.info(f"Created new series: {series_name}")
        
        except Exception as e:
            logger.debug(f"Could not link series: {e}")
    
    def batch_enrich_products(self, limit: int = 100) -> Dict[str, int]:
        """
        Batch enrich products that need research
        
        Args:
            limit: Maximum number of products to process
            
        Returns:
            Statistics dictionary
        """
        if not self.enabled or not self.researcher:
            return {'enriched': 0, 'skipped': 0, 'failed': 0}
        
        stats = {'enriched': 0, 'skipped': 0, 'failed': 0}
        
        try:
            # Find products that need research
            # (no specs, no series, or low confidence)
            products = self.supabase.table('products').select(
                'id,model_number,manufacturer_id,specifications,series_id'
            ).is_('specifications', 'null').limit(limit).execute()
            
            if not products.data:
                logger.info("No products need research")
                return stats
            
            logger.info(f"Found {len(products.data)} products that need research")
            
            # Get manufacturer names
            manufacturer_ids = list(set(p['manufacturer_id'] for p in products.data if p.get('manufacturer_id')))
            manufacturers = {}
            
            for mfr_id in manufacturer_ids:
                mfr_result = self.supabase.table('manufacturers').select('id,name').eq(
                    'id', mfr_id
                ).execute()
                if mfr_result.data:
                    manufacturers[mfr_id] = mfr_result.data[0]['name']
            
            # Process each product
            for product in products.data:
                manufacturer_name = manufacturers.get(product.get('manufacturer_id'))
                if not manufacturer_name:
                    stats['skipped'] += 1
                    continue
                
                success = self.enrich_product(
                    product_id=product['id'],
                    manufacturer_name=manufacturer_name,
                    model_number=product['model_number'],
                    current_confidence=0.5
                )
                
                if success:
                    stats['enriched'] += 1
                else:
                    stats['failed'] += 1
            
            logger.info(f"Batch enrichment complete: {stats}")
            
        except Exception as e:
            logger.error(f"Batch enrichment failed: {e}")
        
        return stats


if __name__ == '__main__':
    # Test mode
    import os
    from supabase import create_client
    from dotenv import load_dotenv
    
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase = create_client(supabase_url, supabase_key)
    
    integration = ResearchIntegration(supabase=supabase, enabled=True)
    
    # Batch enrich products
    print("Starting batch enrichment...")
    stats = integration.batch_enrich_products(limit=10)
    
    print(f"\n✅ Batch enrichment complete:")
    print(f"   Enriched: {stats['enriched']}")
    print(f"   Skipped: {stats['skipped']}")
    print(f"   Failed: {stats['failed']}")
