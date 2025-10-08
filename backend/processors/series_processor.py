"""Series Processor

Detects and creates product series, links products to series.
Stage 7 in the processing pipeline.
"""

from typing import Dict, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .logger import get_logger
from utils.series_detector import detect_series

logger = get_logger()


class SeriesProcessor:
    
    def __init__(self):
        """Initialize series processor"""
        from .imports import get_supabase_client
        self.supabase = get_supabase_client()
        self.logger = get_logger()
        
    def process_all_products(self) -> Dict:
        """
        Process all products to detect and link series
        
        Returns:
            Dict with statistics
        """
        self.logger.info("Starting series detection for all products")
        
        stats = {
            'products_processed': 0,
            'series_detected': 0,
            'series_created': 0,
            'products_linked': 0,
            'errors': 0
        }
        
        try:
            # Get all products without series_id
            products_result = self.supabase.table('products').select(
                '*'
            ).is_('series_id', 'null').execute()
            
            products = products_result.data
            self.logger.info(f"Processing {len(products)} products without series")
            
            for product in products:
                stats['products_processed'] += 1
                
                try:
                    result = self._process_product(product)
                    if result:
                        stats['series_detected'] += 1
                        if result['series_created']:
                            stats['series_created'] += 1
                        if result['product_linked']:
                            stats['products_linked'] += 1
                except Exception as e:
                    self.logger.error(f"Error processing product {product['id']}: {e}")
                    stats['errors'] += 1
            
            self.logger.info(f"Series processing complete: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error in series processing: {e}")
            stats['errors'] += 1
            return stats
    
    def process_product(self, product_id: str) -> Optional[Dict]:
        """
        Process a single product to detect and link series
        
        Args:
            product_id: UUID of product
            
        Returns:
            Dict with result or None
        """
        try:
            # Get product
            product_result = self.supabase.table('products').select(
                '*'
            ).eq('id', product_id).execute()
            
            if not product_result.data:
                self.logger.warning(f"Product {product_id} not found")
                return None
            
            product = product_result.data[0]
            return self._process_product(product)
            
        except Exception as e:
            self.logger.error(f"Error processing product {product_id}: {e}")
            return None
    
    def _process_product(self, product: Dict) -> Optional[Dict]:
        """
        Process a product to detect and link series
        
        Args:
            product: Product data with manufacturer
            
        Returns:
            Dict with series_id, series_created, product_linked
        """
        model_number = product.get('model_number')
        manufacturer_id = product.get('manufacturer_id')
        
        if not model_number or not manufacturer_id:
            return None
        
        # Get manufacturer name from manufacturers table
        try:
            mfr_result = self.supabase.table('manufacturers').select('name').eq('id', manufacturer_id).single().execute()
            manufacturer_name = mfr_result.data.get('name', '') if mfr_result.data else ''
        except:
            manufacturer_name = ''
        
        # Detect series
        series_data = detect_series(model_number, manufacturer_name)
        if not series_data:
            self.logger.debug(f"No series detected for {manufacturer_name} {model_number}")
            return None
        
        self.logger.info(f"Detected series for {model_number}: {series_data['series_name']}")
        
        # Get or create series
        series_id, series_created = self._get_or_create_series(
            manufacturer_id=manufacturer_id,
            series_data=series_data
        )
        
        if not series_id:
            return None
        
        # Link product to series
        product_linked = self._link_product_to_series(
            product_id=product['id'],
            series_id=series_id
        )
        
        return {
            'series_id': series_id,
            'series_name': series_data['series_name'],
            'series_created': series_created,
            'product_linked': product_linked
        }
    
    def _get_or_create_series(
        self, 
        manufacturer_id: str, 
        series_data: Dict
    ) -> tuple[Optional[str], bool]:
        """
        Get existing series or create new one
        
        Args:
            manufacturer_id: Manufacturer UUID
            series_data: Series information from detector
            
        Returns:
            Tuple of (series_id, was_created)
        """
        series_name = series_data['series_name']
        
        try:
            # Check if series exists (by series_name + model_pattern)
            model_pattern = series_data.get('model_pattern')
            existing = self.supabase.table('product_series').select('id').eq(
                'manufacturer_id', manufacturer_id
            ).eq(
                'series_name', series_name
            ).eq(
                'model_pattern', model_pattern
            ).execute()
            
            if existing.data:
                self.logger.debug(f"Series '{series_name}' ({model_pattern}) already exists")
                return existing.data[0]['id'], False
            
            # Create new series
            new_series = {
                'manufacturer_id': manufacturer_id,
                'series_name': series_name,  # Marketing name (e.g., "LaserJet")
                'model_pattern': series_data.get('model_pattern'),  # Technical pattern (e.g., "M4xx")
                'series_description': series_data.get('series_description')
            }
            
            result = self.supabase.table('product_series').insert(new_series).execute()
            
            if result.data:
                series_id = result.data[0]['id']
                self.logger.info(f"Created series '{series_name}' with ID {series_id}")
                return series_id, True
            
            return None, False
            
        except Exception as e:
            error_str = str(e)
            # If duplicate key error, try to get existing series
            if '23505' in error_str or 'duplicate key' in error_str.lower():
                self.logger.debug(f"Series '{series_name}' already exists (duplicate key), fetching existing...")
                try:
                    existing = self.supabase.table('product_series').select('id').eq(
                        'manufacturer_id', manufacturer_id
                    ).eq(
                        'series_name', series_name
                    ).limit(1).execute()
                    
                    if existing.data:
                        return existing.data[0]['id'], False
                except:
                    pass
            
            self.logger.error(f"Error creating series '{series_name}': {e}")
            return None, False
    
    def _link_product_to_series(self, product_id: str, series_id: str) -> bool:
        """
        Link product to series
        
        Args:
            product_id: Product UUID
            series_id: Series UUID
            
        Returns:
            True if successful
        """
        try:
            self.supabase.table('products').update({
                'series_id': series_id
            }).eq('id', product_id).execute()
            
            self.logger.debug(f"Linked product {product_id} to series {series_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error linking product {product_id} to series: {e}")
            return False
    
    def get_series_products(self, series_id: str) -> list:
        """
        Get all products in a series
        
        Args:
            series_id: Series UUID
            
        Returns:
            List of products
        """
        try:
            result = self.supabase.table('products').select('*').eq(
                'series_id', series_id
            ).execute()
            
            return result.data
            
        except Exception as e:
            self.logger.error(f"Error getting products for series {series_id}: {e}")
            return []
    
    def get_manufacturer_series(self, manufacturer_id: str) -> list:
        """
        Get all series for a manufacturer
        
        Args:
            manufacturer_id: Manufacturer UUID
            
        Returns:
            List of series with product counts
        """
        try:
            # Get series
            series_result = self.supabase.table('product_series').select('*').eq(
                'manufacturer_id', manufacturer_id
            ).execute()
            
            series_list = series_result.data
            
            # Add product count to each series
            for series in series_list:
                products = self.get_series_products(series['id'])
                series['product_count'] = len(products)
            
            return series_list
            
        except Exception as e:
            self.logger.error(f"Error getting series for manufacturer {manufacturer_id}: {e}")
            return []


def main():
    """Test series processor"""
    import sys
    
    processor = SeriesProcessor()
    
    if len(sys.argv) > 1:
        # Process specific product
        product_id = sys.argv[1]
        result = processor.process_product(product_id)
        
        if result:
            print(f"\nSeries Detection Complete!")
            print(f"Series: {result['series_name']}")
            print(f"Series ID: {result['series_id']}")
            print(f"Series Created: {result['series_created']}")
            print(f"Product Linked: {result['product_linked']}")
        else:
            print("No series detected for this product")
    else:
        # Process all products
        stats = processor.process_all_products()
        
        print(f"\nSeries Processing Complete!")
        print(f"Products processed: {stats['products_processed']}")
        print(f"Series detected: {stats['series_detected']}")
        print(f"Series created: {stats['series_created']}")
        print(f"Products linked: {stats['products_linked']}")
        print(f"Errors: {stats['errors']}")


if __name__ == '__main__':
    main()
