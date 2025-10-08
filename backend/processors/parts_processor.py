"""Parts Processor

Extracts part numbers and descriptions from document chunks.
Stage 6 in the processing pipeline.
"""

import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.supabase_client import get_supabase_client
from processors.logger import get_logger
from utils.parts_extractor import extract_parts, extract_parts_with_context

logger = get_logger()


class PartsProcessor:
    """Extract and store parts from document chunks"""
    
    def __init__(self):
        """Initialize parts processor"""
        self.supabase = get_supabase_client()
        self.logger = get_logger()
        
    def process_document(self, document_id: str) -> Dict:
        """
        Process all chunks of a document to extract parts
        
        Args:
            document_id: UUID of document to process
            
        Returns:
            Dict with statistics
        """
        self.logger.info(f"Starting parts extraction for document {document_id}")
        
        stats = {
            'chunks_processed': 0,
            'parts_found': 0,
            'parts_created': 0,
            'parts_updated': 0,
            'errors': 0
        }
        
        try:
            # Get document info
            doc_result = self.supabase.table('documents').select('*').eq('id', document_id).execute()
            if not doc_result.data:
                raise ValueError(f"Document {document_id} not found")
            
            document = doc_result.data[0]
            manufacturer_id = document.get('manufacturer_id')
            
            if not manufacturer_id:
                self.logger.warning(f"Document {document_id} has no manufacturer_id, skipping parts extraction")
                return stats
            
            # Get all chunks for this document
            chunks_result = self.supabase.table('chunks').select('*').eq('document_id', document_id).execute()
            chunks = chunks_result.data
            
            self.logger.info(f"Processing {len(chunks)} chunks for parts extraction")
            
            for chunk in chunks:
                stats['chunks_processed'] += 1
                
                try:
                    # Extract parts from chunk text
                    parts_found = self._extract_parts_from_chunk(
                        chunk=chunk,
                        manufacturer_id=manufacturer_id,
                        document_id=document_id
                    )
                    
                    stats['parts_found'] += len(parts_found)
                    
                    # Store parts in database
                    for part_data in parts_found:
                        result = self._store_part(part_data)
                        if result == 'created':
                            stats['parts_created'] += 1
                        elif result == 'updated':
                            stats['parts_updated'] += 1
                            
                except Exception as e:
                    self.logger.error(f"Error processing chunk {chunk['id']}: {e}")
                    stats['errors'] += 1
            
            self.logger.info(f"Parts extraction complete: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error in parts processing: {e}")
            stats['errors'] += 1
            return stats
    
    def _extract_parts_from_chunk(
        self, 
        chunk: Dict, 
        manufacturer_id: str,
        document_id: str
    ) -> List[Dict]:
        """
        Extract parts with context from a chunk
        
        Args:
            chunk: Chunk data
            manufacturer_id: Manufacturer UUID
            document_id: Document UUID
            
        Returns:
            List of part data dicts
        """
        text = chunk.get('text', '')
        if not text:
            return []
        
        # Extract parts with context
        parts_with_ctx = extract_parts_with_context(text, max_parts=20)
        
        parts_data = []
        for item in parts_with_ctx:
            part_number = item['part']
            context = item['context']
            
            # Extract description and category from context
            description, category = self._extract_description_and_category(context, part_number)
            
            parts_data.append({
                'part_number': part_number,
                'manufacturer_id': manufacturer_id,
                'part_name': self._extract_part_name(context, part_number),
                'part_description': description,
                'part_category': category,
                'document_id': document_id,
                'chunk_id': chunk['id'],
                'context': context
            })
        
        return parts_data
    
    def _extract_part_name(self, context: str, part_number: str) -> Optional[str]:
        """
        Extract short part name from context
        
        Args:
            context: Text around part number
            part_number: The part number
            
        Returns:
            Part name or None
        """
        # Look for common patterns before part number
        patterns = [
            r'(?:replace|install|use|order)\s+(?:the\s+)?([a-z\s]{5,40}?)\s*[-–—:]\s*' + re.escape(part_number),
            r'([A-Z][a-z\s]{5,40}?)\s*[-–—:]\s*' + re.escape(part_number),
            r'(?:part|component|assembly)\s*[:]\s*([a-z\s]{5,40}?)\s*[-–—]?\s*' + re.escape(part_number),
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up
                name = re.sub(r'\s+', ' ', name)
                return name[:100]  # Limit length
        
        return None
    
    def _extract_description_and_category(
        self, 
        context: str, 
        part_number: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract description and category from context
        
        Args:
            context: Text around part number
            part_number: The part number
            
        Returns:
            Tuple of (description, category)
        """
        context_lower = context.lower()
        
        # Determine category based on keywords
        category = None
        if any(word in context_lower for word in ['toner', 'cartridge', 'ink', 'drum']):
            category = 'consumable'
        elif any(word in context_lower for word in ['assembly', 'unit', 'module']):
            category = 'assembly'
        elif any(word in context_lower for word in ['sensor', 'motor', 'switch', 'board', 'pcb']):
            category = 'component'
        elif any(word in context_lower for word in ['roller', 'gear', 'belt', 'spring']):
            category = 'mechanical'
        elif any(word in context_lower for word in ['cable', 'harness', 'connector']):
            category = 'electrical'
        
        # Description is the context, cleaned up
        description = context.strip()
        description = re.sub(r'\s+', ' ', description)
        
        return description[:500], category  # Limit length
    
    def _store_part(self, part_data: Dict) -> str:
        """
        Store or update part in database
        
        Args:
            part_data: Part information
            
        Returns:
            'created', 'updated', or 'error'
        """
        try:
            # Check if part already exists
            existing = self.supabase.table('parts_catalog').select('*').eq(
                'part_number', part_data['part_number']
            ).eq(
                'manufacturer_id', part_data['manufacturer_id']
            ).execute()
            
            # Prepare data for storage
            store_data = {
                'part_number': part_data['part_number'],
                'manufacturer_id': part_data['manufacturer_id'],
                'part_name': part_data.get('part_name'),
                'part_description': part_data.get('part_description'),
                'part_category': part_data.get('part_category')
            }
            
            if existing.data:
                # Update existing part if new description is better
                part_id = existing.data[0]['id']
                old_desc = existing.data[0].get('part_description', '')
                new_desc = store_data.get('part_description', '')
                
                # Update if new description is longer/better
                if len(new_desc) > len(old_desc):
                    self.supabase.table('parts_catalog').update(store_data).eq('id', part_id).execute()
                    self.logger.debug(f"Updated part {part_data['part_number']}")
                    return 'updated'
                return 'exists'
            else:
                # Create new part
                self.supabase.table('parts_catalog').insert(store_data).execute()
                self.logger.debug(f"Created part {part_data['part_number']}")
                return 'created'
                
        except Exception as e:
            self.logger.error(f"Error storing part {part_data['part_number']}: {e}")
            return 'error'


def main():
    """Test parts processor"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python parts_processor.py <document_id>")
        sys.exit(1)
    
    document_id = sys.argv[1]
    
    processor = PartsProcessor()
    stats = processor.process_document(document_id)
    
    print(f"\nParts Processing Complete!")
    print(f"Chunks processed: {stats['chunks_processed']}")
    print(f"Parts found: {stats['parts_found']}")
    print(f"Parts created: {stats['parts_created']}")
    print(f"Parts updated: {stats['parts_updated']}")
    print(f"Errors: {stats['errors']}")


if __name__ == '__main__':
    main()
