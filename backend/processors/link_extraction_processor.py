"""
Link Extraction Processor - Extract and categorize links from documents
"""

import re
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass

from core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult
from core.data_models import DocumentModel

@dataclass
class ExtractedLink:
    """Represents an extracted link from a document"""
    url: str
    text: str
    link_type: str  # 'internal', 'external', 'email', 'phone', 'file'
    page_number: Optional[int] = None
    section: Optional[str] = None
    context: Optional[str] = None
    is_valid: bool = True
    domain: Optional[str] = None

class LinkExtractionProcessor(BaseProcessor):
    """
    Processor for extracting and categorizing links from documents
    """
    
    def __init__(self, database_service):
        super().__init__("link_extraction_processor")
        self.database_service = database_service
        
        # Link patterns
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        self.phone_pattern = re.compile(
            r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        )
        self.file_pattern = re.compile(
            r'\b\w+\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|csv|zip|rar|exe|msi)\b',
            re.IGNORECASE
        )
        
        # Known domains for categorization
        self.internal_domains = {
            'hp.com', 'hewlett-packard.com', 'hpe.com',
            'utax.com', 'utax.de', 'utax-europe.com',
            'canon.com', 'canon.de', 'canon-europe.com',
            'xerox.com', 'xerox.de', 'xerox-europe.com',
            'konica-minolta.com', 'konica-minolta.de',
            'kyocera.com', 'kyocera.de',
            'ricoh.com', 'ricoh.de', 'ricoh-europe.com'
        }
        
        # Service-related domains
        self.service_domains = {
            'support.hp.com', 'support.utax.com', 'support.canon.com',
            'www.hp.com/go/support', 'www.utax.com/support',
            'download.utax.com', 'download.hp.com'
        }
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'cpu_cores': 1,
            'ram_gb': 0.5,
            'estimated_duration_seconds': 30
        }
    
    def get_outputs(self) -> List[str]:
        """Get list of output field names"""
        return ['links_extracted', 'link_ids', 'link_types', 'external_domains']
    
    def get_required_inputs(self) -> List[str]:
        """Get list of required input field names"""
        return ['document_id', 'file_path', 'document_content']
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """Extract links from document content"""
        try:
            self.logger.info(f"Extracting links from document: {context.document_id}")
            
            # Get document content (this would come from previous processing stages)
            document_content = await self._get_document_content(context)
            if not document_content:
                return ProcessingResult(
                    success=False,
                    error="No document content available for link extraction"
                )
            
            # Extract links from content
            extracted_links = await self._extract_links_from_content(
                document_content, context
            )
            
            # Categorize and validate links
            categorized_links = await self._categorize_links(extracted_links)
            
            # Store links in database
            link_ids = await self._store_links_in_database(
                categorized_links, context.document_id
            )
            
            # Update document with link count
            await self._update_document_links_count(
                context.document_id, len(categorized_links)
            )
            
            self.logger.info(f"Extracted {len(categorized_links)} links from document")
            
            return ProcessingResult(
                success=True,
                data={
                    'links_extracted': len(categorized_links),
                    'link_ids': link_ids,
                    'link_types': self._get_link_type_summary(categorized_links),
                    'external_domains': self._get_external_domains(categorized_links)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Link extraction failed: {e}")
            return ProcessingResult(
                success=False,
                error=f"Link extraction failed: {str(e)}"
            )
    
    async def _get_document_content(self, context: ProcessingContext) -> Optional[str]:
        """Get document content for link extraction"""
        try:
            # This would typically get content from previous processing stages
            # For now, we'll extract from the file directly
            import os
            if os.path.exists(context.file_path):
                # Simple text extraction - in real implementation this would be
                # the processed text from previous stages
                return "Sample document content with links"  # Placeholder
            return None
        except Exception as e:
            self.logger.error(f"Failed to get document content: {e}")
            return None
    
    async def _extract_links_from_content(self, content: str, 
                                        context: ProcessingContext) -> List[ExtractedLink]:
        """Extract all types of links from document content"""
        links = []
        
        # Extract URLs
        urls = self.url_pattern.findall(content)
        for url in urls:
            links.append(ExtractedLink(
                url=url,
                text=url,
                link_type='url',
                context=self._get_link_context(content, url)
            ))
        
        # Extract email addresses
        emails = self.email_pattern.findall(content)
        for email in emails:
            links.append(ExtractedLink(
                url=f"mailto:{email}",
                text=email,
                link_type='email',
                context=self._get_link_context(content, email)
            ))
        
        # Extract phone numbers
        phones = self.phone_pattern.findall(content)
        for phone_match in phones:
            phone = f"tel:{phone_match[0]}-{phone_match[1]}-{phone_match[2]}"
            phone_text = f"{phone_match[0]}-{phone_match[1]}-{phone_match[2]}"
            links.append(ExtractedLink(
                url=phone,
                text=phone_text,
                link_type='phone',
                context=self._get_link_context(content, phone_text)
            ))
        
        # Extract file references
        files = self.file_pattern.findall(content)
        for file in files:
            links.append(ExtractedLink(
                url=f"file:{file}",
                text=file,
                link_type='file',
                context=self._get_link_context(content, file)
            ))
        
        return links
    
    def _get_link_context(self, content: str, link_text: str, context_length: int = 100) -> str:
        """Get context around a link"""
        try:
            index = content.find(link_text)
            if index == -1:
                return ""
            
            start = max(0, index - context_length // 2)
            end = min(len(content), index + len(link_text) + context_length // 2)
            
            context = content[start:end].strip()
            return context
        except Exception:
            return ""
    
    async def _categorize_links(self, links: List[ExtractedLink]) -> List[ExtractedLink]:
        """Categorize and validate links"""
        categorized_links = []
        
        for link in links:
            # Determine link type and domain
            if link.link_type == 'url':
                parsed_url = urlparse(link.url)
                domain = parsed_url.netloc.lower()
                
                if domain in self.internal_domains:
                    link.link_type = 'internal'
                elif domain in self.service_domains:
                    link.link_type = 'service'
                else:
                    link.link_type = 'external'
                
                link.domain = domain
            
            # Validate link
            link.is_valid = await self._validate_link(link)
            
            categorized_links.append(link)
        
        return categorized_links
    
    async def _validate_link(self, link: ExtractedLink) -> bool:
        """Validate if a link is accessible"""
        try:
            if link.link_type in ['email', 'phone']:
                return True  # These are always valid
            
            if link.link_type == 'url':
                # Basic URL validation
                parsed = urlparse(link.url)
                return bool(parsed.scheme and parsed.netloc)
            
            return True
        except Exception:
            return False
    
    async def _store_links_in_database(self, links: List[ExtractedLink], 
                                     document_id: str) -> List[str]:
        """Store extracted links in database"""
        link_ids = []
        
        for link in links:
            try:
                # Create link record in database
                link_data = {
                    'document_id': document_id,
                    'url': link.url,
                    'link_text': link.text,
                    'link_type': link.link_type,
                    'domain': link.domain,
                    'page_number': link.page_number,
                    'section': link.section,
                    'context': link.context,
                    'is_valid': link.is_valid
                }
                
                # Store in database (this would be implemented based on your DB schema)
                link_id = await self.database_service.create_document_link(link_data)
                if link_id:
                    link_ids.append(link_id)
                    
            except Exception as e:
                self.logger.error(f"Failed to store link: {e}")
        
        return link_ids
    
    async def _update_document_links_count(self, document_id: str, links_count: int):
        """Update document with extracted links count"""
        try:
            # Update document record with links count
            await self.database_service.update_document_field(
                document_id, 'links_count', links_count
            )
        except Exception as e:
            self.logger.error(f"Failed to update document links count: {e}")
    
    def _get_link_type_summary(self, links: List[ExtractedLink]) -> Dict[str, int]:
        """Get summary of link types"""
        summary = {}
        for link in links:
            summary[link.link_type] = summary.get(link.link_type, 0) + 1
        return summary
    
    def _get_external_domains(self, links: List[ExtractedLink]) -> List[str]:
        """Get list of external domains"""
        domains = set()
        for link in links:
            if link.link_type == 'external' and link.domain:
                domains.add(link.domain)
        return list(domains)
