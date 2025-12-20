"""Parts Processor

Extracts part numbers and descriptions from document chunks.
Stage 6 in the processing pipeline.
"""

import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys

from backend.core.base_processor import BaseProcessor, Stage
from .stage_tracker import StageTracker
from .imports import get_database_adapter, extract_parts_with_context


class PartsProcessor(BaseProcessor):
    """Extract and store parts from document chunks"""
    
    def __init__(self, database_adapter=None, stage_tracker: Optional[StageTracker] = None):
        """Initialize parts processor"""
        super().__init__(name="parts_processor")
        self.stage = Stage.PARTS_EXTRACTION
        self.adapter = database_adapter or get_database_adapter()
        self.stage_tracker = None  # Temporarily disabled due to Supabase dependency
        self.logger.info("PartsProcessor initialized")
        
    async def process_document(self, document_id: str) -> Dict:
        """
        Process all chunks of a document to extract parts
        
        Args:
            document_id: UUID of document to process
            
        Returns:
            Dict with statistics
        """
        stats = {
            'chunks_processed': 0,
            'parts_found': 0,
            'parts_created': 0,
            'parts_updated': 0,
            'parts_linked_to_error_codes': 0,
            'errors': 0
        }

        with self.logger_context(document_id=document_id, stage=self.stage) as adapter:
            if self.stage_tracker:
                await self.stage_tracker.start_stage(document_id, self.stage)

            try:
                document = await self.adapter.get_document(document_id)
                if not document:
                    adapter.error("Document %s not found", document_id)
                    stats['errors'] += 1
                    if self.stage_tracker:
                        await self.stage_tracker.fail_stage(document_id, self.stage, error="Document not found")
                    return stats

                manufacturer_id = document.get('manufacturer_id')
                manufacturer_name = (document.get('manufacturer') or '').lower().replace(' ', '_')

                if not manufacturer_id:
                    adapter.warning("No manufacturer_id available, skipping parts extraction")
                    if self.stage_tracker:
                        await self.stage_tracker.skip_stage(document_id, self.stage, reason="Missing manufacturer_id")
                    return stats

                adapter.info("Extracting parts for manufacturer: %s", manufacturer_name)

                chunks = await self.adapter.get_chunks_by_document(document_id)
                adapter.info("Processing %s chunks for parts extraction", len(chunks))

                for chunk in chunks:
                    stats['chunks_processed'] += 1

                    try:
                        parts_found = self._extract_parts_from_chunk(
                            chunk=chunk,
                            manufacturer_id=manufacturer_id,
                            manufacturer_key=manufacturer_name,
                            document_id=document_id
                        )

                        stats['parts_found'] += len(parts_found)

                        for part_data in parts_found:
                            result = await self._store_part(part_data, adapter)
                            if result == 'created':
                                stats['parts_created'] += 1
                            elif result == 'updated':
                                stats['parts_updated'] += 1

                    except Exception as e:
                        adapter.error("Error processing chunk %s: %s", chunk.get('id'), e)
                        stats['errors'] += 1

                adapter.info("Linking parts to error codes...")
                linked_count = await self._link_parts_to_error_codes(document_id, adapter)
                stats['parts_linked_to_error_codes'] = linked_count

                adapter.info("Parts extraction complete: %s", stats)

                if self.stage_tracker:
                    await self.stage_tracker.complete_stage(
                        document_id,
                        self.stage,
                        metadata={
                            'parts_found': stats['parts_found'],
                            'parts_created': stats['parts_created'],
                            'parts_updated': stats['parts_updated'],
                            'chunks_processed': stats['chunks_processed']
                        }
                    )

                return stats

            except Exception as e:
                adapter.error("Error in parts processing: %s", e)
                stats['errors'] += 1
                if self.stage_tracker:
                    await self.stage_tracker.fail_stage(document_id, self.stage, error=str(e))
                return stats

    async def process(self, context) -> Dict:
        """Async wrapper to support BaseProcessor interface."""
        document_id = getattr(context, "document_id", None)
        if not document_id:
            raise ValueError("Processing context must include 'document_id'")

        stats = await self.process_document(str(document_id))
        metadata = {
            "document_id": str(document_id),
            "stage": self.stage.value,
            "parts_found": stats.get("parts_found", 0),
        }
        result = self.create_success_result(stats, metadata=metadata)
        return result
    
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
        # Normalize chunk text across different sources:
        # - content chunks use 'content'
        # - intelligence chunks use 'text_chunk'
        # - some in-memory flows may still provide 'text'
        text = (
            chunk.get('text')
            or chunk.get('content')
            or chunk.get('text_chunk')
            or ''
        )
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
    
    async def _store_part(self, part_data: Dict, adapter) -> str:
        """
        Store or update part in database
        
        Args:
            part_data: Part information
            
        Returns:
            'created', 'updated', or 'error'
        """
        try:
            # Check if part already exists
            existing = await self.adapter.get_part_by_number_and_manufacturer(
                part_data['part_number'], 
                part_data['manufacturer_id']
            )
            
            # Prepare data for storage
            store_data = {
                'part_number': part_data['part_number'],
                'manufacturer_id': part_data['manufacturer_id'],
                'part_name': part_data.get('part_name'),
                'part_description': part_data.get('part_description'),
                'part_category': part_data.get('part_category')
            }
            
            if existing:
                # Update existing part if new description is better
                part_id = existing['id']
                old_desc = existing.get('part_description', '')
                new_desc = store_data.get('part_description', '')
                
                # Update if new description is longer/better
                if len(new_desc) > len(old_desc):
                    await self.adapter.update_part(part_id, store_data)
                    adapter.debug("Updated part %s", part_data['part_number'])
                    return 'updated'
                return 'exists'
            else:
                # Create new part
                await self.adapter.create_part(store_data)
                adapter.debug("Created part %s", part_data['part_number'])
                return 'created'
                
        except Exception as e:
            adapter.error("Error storing part %s: %s", part_data['part_number'], e)
            return 'error'
    
    async def _link_parts_to_error_codes(self, document_id: str, adapter) -> int:
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
            error_codes = await self.adapter.get_error_codes_by_document(document_id)
            
            for error_code in error_codes:
                ec_id = error_code['id']
                solution_text = error_code.get('solution_text', '')
                chunk_id = error_code.get('chunk_id')
                
                # Extract parts from solution text
                if solution_text:
                    parts_in_solution = await self._extract_and_link_parts_from_text(
                        text=solution_text,
                        error_code_id=ec_id,
                        source='solution_text',
                        adapter=adapter,
                    )
                    linked_count += parts_in_solution
                
                # Also check the chunk where error code was found
                if chunk_id:
                    chunk = await self.adapter.get_chunk(chunk_id)
                    if chunk:
                        chunk_text = (
                            chunk.get('text')
                            or chunk.get('content')
                            or chunk.get('text_chunk')
                            or ''
                        )
                        parts_in_chunk = await self._extract_and_link_parts_from_text(
                            text=chunk_text,
                            error_code_id=ec_id,
                            source='chunk',
                            adapter=adapter,
                        )
                        linked_count += parts_in_chunk
            
            adapter.info("Linked %s parts to error codes", linked_count)
            return linked_count
            
        except Exception as e:
            adapter.error("Error linking parts to error codes: %s", e)
            return linked_count
    
    async def _extract_and_link_parts_from_text(
        self, 
        text: str, 
        error_code_id: str, 
        source: str,
        adapter
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
                part = await self.adapter.get_part_by_number(part_number)
                
                if not part:
                    continue
                
                part_id = part['id']
                
                # Create link (ignore if already exists)
                try:
                    await self.adapter.create_error_code_part_link({
                        'error_code_id': error_code_id,
                        'part_id': part_id,
                        'relevance_score': confidence,
                        'extraction_source': source
                    })
                    
                    linked_count += 1
                    adapter.debug("Linked part %s to error code %s", part_number, error_code_id)
                    
                except Exception:
                    # Link probably already exists, ignore
                    pass
            
            return linked_count
            
        except Exception as e:
            adapter.error("Error extracting and linking parts: %s", e)
            return linked_count


import asyncio


def main():
    """Test parts processor"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python parts_processor.py <document_id>")
        sys.exit(1)
    
    document_id = sys.argv[1]
    
    async def run():
        processor = PartsProcessor()
        stats = await processor.process_document(document_id)
        
        print(f"\nParts Processing Complete!")
        print(f"Chunks processed: {stats['chunks_processed']}")
        print(f"Parts found: {stats['parts_found']}")
        print(f"Parts created: {stats['parts_created']}")
        print(f"Parts updated: {stats['parts_updated']}")
        print(f"Errors: {stats['errors']}")
    
    asyncio.run(run())


if __name__ == '__main__':
    main()
