"""Parts Processor

Extracts part numbers and descriptions from document chunks.
Stage 6 in the processing pipeline.
"""

import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys

# Use centralized imports
from .imports import get_supabase_client, get_logger, extract_parts_with_context

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
            'parts_linked_to_error_codes': 0,
            'errors': 0
        }
        
        try:
            # Get document info with manufacturer
            doc_result = self.supabase.table('documents').select('*, manufacturer:manufacturer_id(name)').eq('id', document_id).execute()
            if not doc_result.data:
                raise ValueError(f"Document {document_id} not found")
            
            document = doc_result.data[0]
            manufacturer_id = document.get('manufacturer_id')
            manufacturer_name = document.get('manufacturer', {}).get('name', '').lower().replace(' ', '_')
            
            if not manufacturer_id:
                self.logger.warning(f"Document {document_id} has no manufacturer_id, skipping parts extraction")
                return stats
            
            self.logger.info(f"Extracting parts for manufacturer: {manufacturer_name}")
            
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
                        manufacturer_key=manufacturer_name,
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
            
            # Link parts to error codes
            self.logger.info("Linking parts to error codes...")
            linked_count = self._link_parts_to_error_codes(document_id)
            stats['parts_linked_to_error_codes'] = linked_count
            
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
        manufacturer_key: str,
        document_id: str
    ) -> List[Dict]:
        """
        Extract parts with context from a chunk
        
        Args:
            chunk: Chunk data
            manufacturer_id: Manufacturer UUID
            manufacturer_key: Manufacturer key for patterns (e.g., 'hp', 'konica_minolta')
            document_id: Document UUID
            
        Returns:
            List of part data dicts
        """
        text = chunk.get('text', '')
        if not text:
            return []
        
        # Extract parts with context using manufacturer-specific patterns
        parts_with_ctx = extract_parts_with_context(text, manufacturer_key=manufacturer_key, max_parts=20)
        
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
    
    def _link_parts_to_error_codes(self, document_id: str) -> int:
        """
        Link parts to error codes based on chunk proximity and solution text
        
        Args:
            document_id: Document UUID
            
        Returns:
            Number of links created
        """
        linked_count = 0
        
        try:
            # Get all error codes for this document
            error_codes_result = self.supabase.table('error_codes').select(
                'id, error_code, solution_text, chunk_id'
            ).eq('document_id', document_id).execute()
            
            error_codes = error_codes_result.data
            
            for error_code in error_codes:
                ec_id = error_code['id']
                solution_text = error_code.get('solution_text', '')
                chunk_id = error_code.get('chunk_id')
                
                # Extract parts from solution text
                if solution_text:
                    parts_in_solution = self._extract_and_link_parts_from_text(
                        text=solution_text,
                        error_code_id=ec_id,
                        source='solution_text'
                    )
                    linked_count += parts_in_solution
                
                # Also check the chunk where error code was found
                if chunk_id:
                    chunk_result = self.supabase.table('chunks').select('text').eq('id', chunk_id).execute()
                    if chunk_result.data:
                        chunk_text = chunk_result.data[0].get('text', '')
                        parts_in_chunk = self._extract_and_link_parts_from_text(
                            text=chunk_text,
                            error_code_id=ec_id,
                            source='chunk'
                        )
                        linked_count += parts_in_chunk
            
            self.logger.info(f"Linked {linked_count} parts to error codes")
            return linked_count
            
        except Exception as e:
            self.logger.error(f"Error linking parts to error codes: {e}")
            return linked_count
    
    def _extract_and_link_parts_from_text(
        self, 
        text: str, 
        error_code_id: str, 
        source: str
    ) -> int:
        """
        Extract parts from text and link to error code
        
        Args:
            text: Text to extract from
            error_code_id: Error code UUID
            source: Where the text came from
            
        Returns:
            Number of parts linked
        """
        linked_count = 0
        
        try:
            # Extract parts
            parts_found = extract_parts_with_context(text, max_parts=10)
            
            for part_item in parts_found:
                part_number = part_item['part']
                confidence = part_item.get('confidence', 0.8)
                
                # Find part in database
                part_result = self.supabase.table('parts_catalog').select('id').eq(
                    'part_number', part_number
                ).execute()
                
                if not part_result.data:
                    continue
                
                part_id = part_result.data[0]['id']
                
                # Create link (ignore if already exists)
                try:
                    self.supabase.table('error_code_parts').insert({
                        'error_code_id': error_code_id,
                        'part_id': part_id,
                        'relevance_score': confidence,
                        'extraction_source': source
                    }).execute()
                    
                    linked_count += 1
                    self.logger.debug(f"Linked part {part_number} to error code {error_code_id}")
                    
                except Exception:
                    # Link probably already exists, ignore
                    pass
            
            return linked_count
            
        except Exception as e:
            self.logger.error(f"Error extracting and linking parts: {e}")
            return linked_count


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
