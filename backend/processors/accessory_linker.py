"""
Accessory Linker - Automatically link accessories to products
Links accessories mentioned in documents to the main products in those documents
"""
import logging
from typing import List, Dict, Optional, Set
from uuid import UUID
from supabase import Client

from backend.utils.accessory_detector import detect_konica_minolta_accessory

logger = logging.getLogger(__name__)


class AccessoryLinker:
    """Links accessories to products based on document co-occurrence"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.logger = logging.getLogger(__name__)
    
    def link_accessories_for_document(self, document_id: UUID) -> Dict[str, int]:
        """
        Link all accessories to main products in a document
        
        Strategy:
        - If accessory mentioned in document → link to document's main products
        - Main products = non-accessory products
        
        Args:
            document_id: Document UUID
            
        Returns:
            Dict with statistics: {
                'main_products': int,
                'accessories': int,
                'links_created': int,
                'links_skipped': int
            }
        """
        stats = {
            'main_products': 0,
            'accessories': 0,
            'links_created': 0,
            'links_skipped': 0,
            'errors': 0
        }
        
        try:
            # Get all products from this document
            products = self._get_products_from_document(document_id)
            
            if not products:
                self.logger.info(f"No products found in document {document_id}")
                return stats
            
            # Separate main products from accessories
            main_products = []
            accessories = []
            
            for product in products:
                if self._is_accessory(product):
                    accessories.append(product)
                else:
                    main_products.append(product)
            
            stats['main_products'] = len(main_products)
            stats['accessories'] = len(accessories)
            
            self.logger.info(
                f"📦 Document {document_id}: "
                f"{len(main_products)} main products, {len(accessories)} accessories"
            )
            
            if not main_products:
                self.logger.info("No main products to link accessories to")
                return stats
            
            if not accessories:
                self.logger.info("No accessories to link")
                return stats
            
            # Link each accessory to all main products
            for accessory in accessories:
                for main_product in main_products:
                    result = self._create_link(
                        product_id=main_product['id'],
                        accessory_id=accessory['id'],
                        is_standard=False,  # Default: optional accessory
                        compatibility_notes=f"Found together in document"
                    )
                    
                    if result == 'created':
                        stats['links_created'] += 1
                    elif result == 'exists':
                        stats['links_skipped'] += 1
                    elif result == 'error':
                        stats['errors'] += 1
            
            self.logger.info(
                f"✅ Linked accessories: "
                f"{stats['links_created']} created, "
                f"{stats['links_skipped']} skipped, "
                f"{stats['errors']} errors"
            )
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error linking accessories for document {document_id}: {e}")
            stats['errors'] += 1
            return stats
    
    def _get_products_from_document(self, document_id: UUID) -> List[Dict]:
        """Get all products mentioned in a document"""
        try:
            # Query document_products junction table
            response = self.supabase.schema('krai_core').table('document_products').select(
                'product_id'
            ).eq('document_id', str(document_id)).execute()
            
            if not response.data:
                return []
            
            product_ids = [row['product_id'] for row in response.data]
            
            # Get product details
            products_response = self.supabase.schema('krai_core').table('products').select(
                'id, model_number, manufacturer_id, product_type'
            ).in_('id', product_ids).execute()
            
            return products_response.data if products_response.data else []
            
        except Exception as e:
            self.logger.error(f"Error getting products from document: {e}")
            return []
    
    def _is_accessory(self, product: Dict) -> bool:
        """
        Determine if a product is an accessory
        
        Uses:
        1. Product type (if it's an accessory/consumable type)
        2. Accessory detector (model number patterns)
        """
        # Check product_type first
        product_type = product.get('product_type', '').lower()
        
        # Accessory types from database
        accessory_types = {
            'finisher', 'stapler_finisher', 'booklet_finisher', 'punch_finisher',
            'folder', 'trimmer', 'stacker',
            'feeder', 'paper_feeder', 'envelope_feeder', 'large_capacity_feeder',
            'document_feeder',
            'accessory', 'cabinet', 'work_table', 'caster_base', 'bridge_unit',
            'interface_kit', 'memory_upgrade', 'hard_drive', 'controller',
            'fax_kit', 'wireless_kit', 'keyboard', 'card_reader', 'coin_kit',
            'option', 'duplex_unit', 'output_tray', 'mailbox', 'job_separator',
            'consumable', 'toner_cartridge', 'ink_cartridge', 'drum_unit',
            'developer_unit', 'fuser_unit', 'transfer_belt', 'waste_toner_box',
            'maintenance_kit', 'staple_cartridge', 'punch_kit', 'print_head',
            'ink_tank', 'paper'
        }
        
        if product_type in accessory_types:
            return True
        
        # Check model number with accessory detector
        model_number = product.get('model_number', '')
        if model_number:
            # Try Konica Minolta detector
            accessory_match = detect_konica_minolta_accessory(model_number)
            if accessory_match:
                return True
        
        return False
    
    def _create_link(
        self,
        product_id: str,
        accessory_id: str,
        is_standard: bool = False,
        compatibility_notes: Optional[str] = None
    ) -> str:
        """
        Create a link between product and accessory
        
        Returns:
            'created' if new link created
            'exists' if link already exists
            'error' if error occurred
        """
        try:
            # Check if link already exists
            existing = self.supabase.schema('krai_core').table('product_accessories').select(
                'id'
            ).eq('product_id', product_id).eq('accessory_id', accessory_id).execute()
            
            if existing.data:
                return 'exists'
            
            # Create new link
            link_data = {
                'product_id': product_id,
                'accessory_id': accessory_id,
                'is_standard': is_standard,
                'compatibility_notes': compatibility_notes
            }
            
            self.supabase.schema('krai_core').table('product_accessories').insert(
                link_data
            ).execute()
            
            return 'created'
            
        except Exception as e:
            self.logger.error(
                f"Error creating link {product_id} -> {accessory_id}: {e}"
            )
            return 'error'
    
    def get_accessories_for_product(self, product_id: UUID) -> List[Dict]:
        """Get all accessories linked to a product"""
        try:
            response = self.supabase.schema('krai_core').table('product_accessories').select(
                'accessory_id, is_standard, compatibility_notes'
            ).eq('product_id', str(product_id)).execute()
            
            if not response.data:
                return []
            
            accessory_ids = [row['accessory_id'] for row in response.data]
            
            # Get accessory details
            accessories_response = self.supabase.schema('krai_core').table('products').select(
                'id, model_number, product_type'
            ).in_('id', accessory_ids).execute()
            
            return accessories_response.data if accessories_response.data else []
            
        except Exception as e:
            self.logger.error(f"Error getting accessories for product: {e}")
            return []
    
    def get_products_for_accessory(self, accessory_id: UUID) -> List[Dict]:
        """Get all products that an accessory is compatible with"""
        try:
            response = self.supabase.schema('krai_core').table('product_accessories').select(
                'product_id, is_standard, compatibility_notes'
            ).eq('accessory_id', str(accessory_id)).execute()
            
            if not response.data:
                return []
            
            product_ids = [row['product_id'] for row in response.data]
            
            # Get product details
            products_response = self.supabase.schema('krai_core').table('products').select(
                'id, model_number, product_type'
            ).in_('id', product_ids).execute()
            
            return products_response.data if products_response.data else []
            
        except Exception as e:
            self.logger.error(f"Error getting products for accessory: {e}")
            return []
