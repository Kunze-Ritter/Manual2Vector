"""
SVG Processor - Extract and convert vector graphics from PDFs

Stage 3a of the processing pipeline. Extracts SVG vector graphics (Explosionszeichnungen) 
and converts them to PNG for Vision AI analysis.
"""

import os
import json
import logging
import base64
import io
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

import fitz
from PIL import Image
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

from backend.core.base_processor import BaseProcessor, Stage, ProcessingResult, ProcessingStatus, ProcessingError, ProcessingContext


class SVGProcessor(BaseProcessor):
    """
    SVG Processor for vector graphics extraction and conversion
    
    Extracts SVG vector graphics from PDFs using PyMuPDF, converts them to PNG
    using svglib + reportlab, and queues them for Vision AI analysis.
    """
    
    def __init__(
        self,
        database_service,
        storage_service,
        ai_service=None,
        dpi: int = 300,
        max_dimension: int = 2048
    ):
        """
        Initialize SVG Processor
        
        Args:
            database_service: Database service for queuing images
            storage_service: Storage service (not used directly, but required for interface)
            ai_service: AI service for Vision AI analysis (optional)
            dpi: DPI for SVG to PNG conversion (default: 300)
            max_dimension: Maximum width/height for converted PNGs (default: 2048)
        """
        super().__init__("svg_processor")
        self.database_service = database_service
        self.storage_service = storage_service
        self.ai_service = ai_service
        self.dpi = dpi
        self.max_dimension = max_dimension
        
        self.logger.info(f"SVGProcessor initialized (DPI: {dpi}, max_dimension: {max_dimension})")
    
    def get_stage(self) -> Stage:
        """Return the processing stage"""
        return Stage.SVG_PROCESSING
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Main processing method for SVG extraction and conversion
        
        Args:
            context: Processing context with document information
            
        Returns:
            ProcessingResult with SVG extraction statistics
        """
        import asyncio
        loop = asyncio.get_event_loop()
        
        try:
            # Extract document information
            document_id = UUID(context.document_id)
            pdf_path = context.pdf_path
            
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Process document in thread pool
            result_data = await loop.run_in_executor(
                None, 
                self.process_document, 
                document_id, 
                pdf_path, 
                context
            )
            
            return self.create_success_result(
                data=result_data,
                metadata={
                    "document_id": str(document_id),
                    "stage": self.get_stage().value,
                    "svgs_extracted": result_data.get("svgs_extracted", 0),
                    "svgs_converted": result_data.get("svgs_converted", 0),
                    "images_queued": result_data.get("images_queued", 0)
                }
            )
            
        except Exception as e:
            error = ProcessingError(
                f"SVG processing failed: {str(e)}",
                self.name,
                "SVG_PROCESSING_ERROR"
            )
            return self.create_error_result(error)
    
    def process_document(self, document_id: UUID, pdf_path: str, context) -> Dict[str, Any]:
        """
        Process document to extract and convert SVGs
        
        Args:
            document_id: Document UUID
            pdf_path: Path to PDF file
            context: Processing context
            
        Returns:
            Dictionary with processing statistics
        """
        self.logger.info(f"Starting SVG processing for document {document_id}")
        
        # Open PDF document
        doc = fitz.open(pdf_path)
        
        # Extract SVGs from all pages
        all_svgs = []
        for page_num, page in enumerate(doc):
            page_svgs = self._extract_page_svgs(page, page_num + 1)
            if page_svgs:
                all_svgs.extend(page_svgs)
                self.logger.debug(f"Extracted {len(page_svgs)} SVGs from page {page_num + 1}")
        
        # Convert SVGs to PNG
        converted_count = 0
        for svg_data in all_svgs:
            try:
                png_bytes = self._convert_svg_to_png(svg_data['svg_content'])
                if png_bytes:
                    svg_data['png_bytes'] = png_bytes
                    svg_data['image_type'] = 'vector_graphic'
                    converted_count += 1
                else:
                    self.logger.warning(f"Failed to convert SVG: {svg_data['filename']}")
            except Exception as e:
                self.logger.error(f"Error converting SVG {svg_data['filename']}: {e}")
        
        # Queue converted SVGs for storage
        queued_count = 0
        if converted_count > 0:
            queued_count = self._queue_svg_images(document_id, all_svgs, context)
        
        doc.close()
        
        result_data = {
            'svgs_extracted': len(all_svgs),
            'svgs_converted': converted_count,
            'images_queued': queued_count,
            'conversion_success_rate': converted_count / len(all_svgs) if all_svgs else 0
        }
        
        self.logger.success(
            f"SVG processing completed: {len(all_svgs)} extracted, "
            f"{converted_count} converted, {queued_count} queued"
        )
        
        return result_data
    
    def _extract_page_svgs(self, page, page_number: int) -> List[Dict[str, Any]]:
        """
        Extract SVG graphics from a PDF page with enhanced multi-graphic support
        
        Args:
            page: PyMuPDF page object
            page_number: Page number (1-based)
            
        Returns:
            List of SVG data dictionaries with bounding box information
        """
        svgs = []
        
        try:
            # Get page dimensions for bounding box calculations
            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height
            
            # Method 1: Try to extract individual vector graphics through display list analysis
            try:
                # Get the page's display list to analyze individual drawing operations
                dl = page.get_drawings()
                
                if dl and len(dl) > 1:
                    # Multiple drawing operations detected - extract individual graphics
                    self.logger.debug(f"Page {page_number}: Found {len(dl)} drawing operations")
                    
                    for i, drawing in enumerate(dl):
                        # Extract bounding box for this drawing
                        bbox = drawing['rect']  # PyMuPDF provides bounding box
                        
                        # Create a clip area for this specific graphic
                        clip_area = fitz.Rect(bbox)
                        
                        # Extract SVG for this specific area
                        try:
                            # Create a temporary page with clipping to isolate this graphic
                            svg_content = page.get_svg_image(clip=clip_area)
                            
                            if svg_content and len(svg_content.strip()) > 0:
                                svg_data = {
                                    'id': str(uuid4()),
                                    'page_number': page_number,
                                    'graphic_index': i,
                                    'svg_content': svg_content,
                                    'svg_size': len(svg_content),
                                    'filename': f'page_{page_number}_graphic_{i+1:02d}.svg',
                                    'bounding_box': {
                                        'x0': bbox.x0,
                                        'y0': bbox.y0,
                                        'x1': bbox.x1,
                                        'y1': bbox.y1,
                                        'width': bbox.width,
                                        'height': bbox.height,
                                        'normalized': {
                                            'x0': bbox.x0 / page_width,
                                            'y0': bbox.y0 / page_height,
                                            'x1': bbox.x1 / page_width,
                                            'y1': bbox.y1 / page_height,
                                            'width': bbox.width / page_width,
                                            'height': bbox.height / page_height
                                        }
                                    },
                                    'extraction_method': 'display_list'
                                }
                                svgs.append(svg_data)
                                
                        except Exception as e:
                            self.logger.debug(f"Failed to extract graphic {i} from page {page_number}: {e}")
                            continue
                else:
                    # Single graphic or no display list - use traditional method
                    pass
                    
            except Exception as e:
                self.logger.debug(f"Display list analysis failed for page {page_number}: {e}")
            
            # Method 2: Fallback to traditional page-level SVG extraction
            if not svgs:
                # Extract full page SVG content
                svg_content = page.get_svg_image()
                
                if svg_content and len(svg_content.strip()) > 0:
                    # Create SVG record with page-level bounding box
                    svg_data = {
                        'id': str(uuid4()),
                        'page_number': page_number,
                        'graphic_index': 0,
                        'svg_content': svg_content,
                        'svg_size': len(svg_content),
                        'filename': f'page_{page_number}_vector.svg',
                        'bounding_box': {
                            'x0': 0,
                            'y0': 0,
                            'x1': page_width,
                            'y1': page_height,
                            'width': page_width,
                            'height': page_height,
                            'normalized': {
                                'x0': 0.0,
                                'y0': 0.0,
                                'x1': 1.0,
                                'y1': 1.0,
                                'width': 1.0,
                                'height': 1.0
                            }
                        },
                        'extraction_method': 'page_level'
                    }
                    svgs.append(svg_data)
                
                self.logger.debug(f"Extracted page-level SVG from page {page_number} ({len(svg_content)} bytes)")
            
            # Method 3: Try to identify vector segments through xobject inspection
            if not svgs or len(svgs) == 1:
                try:
                    # Get page's xobjects (embedded graphics)
                    xobjects = page.get_xobjects()
                    
                    if xobjects:
                        self.logger.debug(f"Page {page_number}: Found {len(xobjects)} xobjects")
                        
                        for i, xref in enumerate(xobjects):
                            try:
                                # Extract individual xobject as SVG
                                xobject = page.parent.extract_image(xref)
                                
                                # Check if this is a vector graphic
                                if xobject and 'ext' in xobject and xobject['ext'] in ['svg', 'pdf']:
                                    # For vector xobjects, we can extract them directly
                                    svg_data = {
                                        'id': str(uuid4()),
                                        'page_number': page_number,
                                        'graphic_index': len(svgs),
                                        'svg_content': xobject.get('image', ''),
                                        'svg_size': len(xobject.get('image', '')),
                                        'filename': f'page_{page_number}_xobject_{i+1:02d}.svg',
                                        'bounding_box': {
                                            'x0': 0, 'y0': 0, 'x1': page_width, 'y1': page_height,
                                            'width': page_width, 'height': page_height,
                                            'normalized': {'x0': 0.0, 'y0': 0.0, 'x1': 1.0, 'y1': 1.0, 'width': 1.0, 'height': 1.0}
                                        },
                                        'extraction_method': 'xobject',
                                        'xref': xref
                                    }
                                    svgs.append(svg_data)
                                    
                            except Exception as e:
                                self.logger.debug(f"Failed to extract xobject {i} from page {page_number}: {e}")
                                continue
                                
                except Exception as e:
                    self.logger.debug(f"Xobject inspection failed for page {page_number}: {e}")
            
            # Log extraction summary
            if svgs:
                methods = [s['extraction_method'] for s in svgs]
                method_counts = {m: methods.count(m) for m in set(methods)}
                self.logger.info(
                    f"Page {page_number}: Extracted {len(svgs)} SVGs using methods: {method_counts}"
                )
                
                # Log bounding box information for debugging
                for i, svg in enumerate(svgs):
                    bbox = svg['bounding_box']
                    self.logger.debug(
                        f"  SVG {i+1}: {bbox['width']:.1f}x{bbox['height']:.1f} at "
                        f"({bbox['x0']:.1f},{bbox['y0']:.1f}) - {svg['extraction_method']}"
                    )
            
        except Exception as e:
            self.logger.warning(f"Failed to extract SVGs from page {page_number}: {e}")
        
        return svgs
    
    def _convert_svg_to_png(self, svg_content: str) -> Optional[bytes]:
        """
        Convert SVG content to PNG bytes
        
        Args:
            svg_content: SVG content as string
            
        Returns:
            PNG bytes or None if conversion failed
        """
        try:
            # Convert string to bytes
            svg_bytes = svg_content.encode('utf-8')
            
            # Create SVG drawing
            drawing = svg2rlg(io.BytesIO(svg_bytes))
            
            if drawing is None:
                self.logger.warning("Failed to parse SVG content")
                return None
            
            # Render to PNG bytes directly
            png_bytes = renderPM.drawToString(drawing, fmt='PNG', dpi=self.dpi)
            
            # Scale if needed
            if self.max_dimension > 0:
                png_bytes = self._scale_png_if_needed(png_bytes)
            
            self.logger.debug(f"Converted SVG to PNG ({len(png_bytes)} bytes)")
            return png_bytes
            
        except Exception as e:
            self.logger.error(f"SVG to PNG conversion failed: {e}")
            return None
    
    def _scale_png_if_needed(self, png_bytes: bytes) -> bytes:
        """
        Scale PNG if it exceeds maximum dimensions
        
        Args:
            png_bytes: Original PNG bytes
            
        Returns:
            Scaled PNG bytes
        """
        try:
            # Open image to check dimensions
            with Image.open(io.BytesIO(png_bytes)) as img:
                width, height = img.size
                
                # Check if scaling is needed
                if width <= self.max_dimension and height <= self.max_dimension:
                    return png_bytes
                
                # Calculate scaling factor
                scale_factor = min(self.max_dimension / width, self.max_dimension / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                
                # Scale image
                scaled_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert back to bytes
                buffer = io.BytesIO()
                scaled_img.save(buffer, format='PNG', dpi=(self.dpi, self.dpi))
                scaled_bytes = buffer.getvalue()
                buffer.close()
                
                self.logger.debug(
                    f"Scaled PNG from {width}x{height} to {new_width}x{new_height} "
                    f"({len(scaled_bytes)} bytes)"
                )
                
                return scaled_bytes
                
        except Exception as e:
            self.logger.warning(f"Failed to scale PNG: {e}")
            return png_bytes
    
    def _queue_svg_images(self, document_id: UUID, svgs: List[Dict[str, Any]], context) -> int:
        """
        Queue converted SVG images for storage
        
        Args:
            document_id: Document UUID
            svgs: List of SVG data with converted PNG bytes
            context: Processing context
            
        Returns:
            Number of images queued
        """
        queued_count = 0
        
        for svg_data in svgs:
            if 'png_bytes' not in svg_data:
                continue
            
            try:
                # Create payload for processing queue
                payload = {
                    'artifact_type': 'image',
                    'document_id': str(document_id),
                    'filename': svg_data['filename'].replace('.svg', '.png'),
                    'page_number': svg_data['page_number'],
                    'image_type': 'vector_graphic',
                    'content': base64.b64encode(svg_data['png_bytes']).decode('utf-8'),
                    'metadata': {
                        'svg_size': svg_data['svg_size'],
                        'original_format': 'svg',
                        'conversion_dpi': self.dpi,
                        'extracted_from_page': svg_data['page_number']
                    }
                }
                
                # Insert into processing queue using adapter method
                stage_payload = {
                    "document_id": str(document_id),
                    "stage": "storage",
                    "artifact_type": "image",
                    "status": "pending",
                    "payload": payload
                }
                
                # Use adapter method if available. Run in new event loop because
                # _queue_svg_images runs in a worker thread (via run_in_executor)
                # and has no access to the main event loop.
                if hasattr(self.database_service, 'create_svg_queue_entry'):
                    import asyncio
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(
                                self.database_service.create_svg_queue_entry(stage_payload)
                            )
                            queued_count += 1
                            self.logger.debug(f"Queued SVG image: {svg_data['filename']}")
                        finally:
                            loop.close()
                    except Exception as loop_exc:
                        self.logger.error(
                            "Failed to enqueue SVG image %s: %s",
                            svg_data['filename'],
                            loop_exc,
                        )
                else:
                    self.logger.warning("Database service does not support SVG queuing")
                
            except Exception as e:
                self.logger.error(f"Failed to queue SVG image {svg_data['filename']}: {e}")
        
        self.logger.info(f"Queued {queued_count} SVG images for storage")
        return queued_count
    
    def get_required_inputs(self) -> List[str]:
        """Get required inputs for SVG processing"""
        return ['pdf_path']
    
    def get_outputs(self) -> List[str]:
        """Get outputs produced by SVG processing"""
        return ['svg_images_queued']
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        """Get resource requirements"""
        return {
            'cpu_intensive': True,  # SVG conversion can be CPU intensive
            'memory_intensive': True,  # Large SVGs require memory
            'gpu_required': False,
            'estimated_ram_gb': 2.0,
            'estimated_gpu_gb': 0.0,
            'parallel_safe': False  # Sequential processing is better for consistency
        }
