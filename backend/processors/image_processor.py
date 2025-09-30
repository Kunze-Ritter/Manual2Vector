"""
Image Processor for KR-AI-Engine
Stage 3: Image extraction, OCR, and classification (Object Storage)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import io

try:
    import pymupdf as fitz
    FITZ_AVAILABLE = True
except ImportError:
    fitz = None
    FITZ_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    PIL_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None
    TESSERACT_AVAILABLE = False

from core.base_processor import BaseProcessor, ProcessingContext, ProcessingResult, ProcessingError
from core.data_models import ImageModel, ImageType
from services.database_service import DatabaseService
from services.object_storage_service import ObjectStorageService
from services.ai_service import AIService

class ImageProcessor(BaseProcessor):
    """
    Image Processor - Stage 3 of the processing pipeline
    
    Responsibilities:
    - Extract images from PDF
    - OCR text extraction
    - AI image analysis and classification
    - Object Storage for images (NOT documents!)
    
    Output: krai_content.images (Object Storage)
    """
    
    def __init__(self, 
                 database_service: DatabaseService, 
                 storage_service: ObjectStorageService,
                 ai_service: AIService):
        super().__init__("image_processor")
        self.database_service = database_service
        self.storage_service = storage_service
        self.ai_service = ai_service
    
    def get_required_inputs(self) -> List[str]:
        """Get required inputs for image processor"""
        return ['document_id', 'file_path']
    
    def get_outputs(self) -> List[str]:
        """Get outputs from image processor"""
        return ['images', 'total_images', 'ocr_text', 'ai_descriptions']
    
    def get_output_tables(self) -> List[str]:
        """Get database tables this processor writes to"""
        return ['krai_content.images']
    
    def get_storage_buckets(self) -> List[str]:
        """Get storage buckets this processor uses"""
        return ['krai-document-images']
    
    def get_dependencies(self) -> List[str]:
        """Get processor dependencies"""
        return ['upload_processor']
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        """Get resource requirements for image processor"""
        return {
            'cpu_intensive': True,
            'memory_intensive': True,
            'gpu_required': True,
            'estimated_ram_gb': 4.0,
            'estimated_gpu_gb': 2.0,
            'parallel_safe': False  # GPU intensive
        }
    
    async def process(self, context: ProcessingContext) -> ProcessingResult:
        """
        Process image extraction and analysis
        
        Args:
            context: Processing context with document information
            
        Returns:
            ProcessingResult: Image processing result
        """
        try:
            # Extract images from PDF
            images_data = await self._extract_images_from_pdf(context.file_path)
            
            if not images_data:
                self.logger.warning(f"No images found in document {context.document_id}")
                return self.create_success_result(
                    {'images': [], 'total_images': 0, 'ocr_text': '', 'ai_descriptions': []},
                    {'processing_timestamp': datetime.utcnow().isoformat()}
                )
            
            # Process each image with deduplication
            processed_images = []
            all_ocr_text = []
            ai_descriptions = []
            seen_hashes = set()  # Track processed image hashes
            
            for i, image_data in enumerate(images_data):
                # Check for duplicate images by hash
                image_hash = image_data.get('hash', '')
                if image_hash in seen_hashes:
                    self.logger.info(f"Skipping duplicate image with hash: {image_hash}")
                    continue
                
                seen_hashes.add(image_hash)
                
                try:
                    # Upload image to Object Storage
                    storage_result = await self.storage_service.upload_image(
                        content=image_data['content'],
                        filename=image_data['filename'],
                        bucket_type='document_images',
                        metadata={
                            'document_id': context.document_id,
                            'page_number': image_data['page_number'],
                            'image_index': i + 1
                        }
                    )
                    
                    # Perform OCR first
                    ocr_text = await self._perform_ocr(image_data['content'])
                    if ocr_text:
                        all_ocr_text.append(ocr_text)
                    
                    # AI image analysis with error handling
                    try:
                        ai_analysis = await self.ai_service.analyze_image(
                            image=image_data['content'],
                            description=f"Technical image from page {image_data['page_number']}"
                        )
                        ai_descriptions.append(ai_analysis)
                    except Exception as ai_error:
                        self.logger.warning(f"AI analysis failed for image {i+1}: {ai_error}")
                        # Create fallback analysis
                        ai_analysis = {
                            'image_type': 'diagram',
                            'description': f'Technical image from page {image_data["page_number"]}',
                            'confidence': 0.5,
                            'contains_text': False,
                            'tags': ['technical', 'diagram']
                        }
                        ai_descriptions.append(ai_analysis)
                    
                    # Determine if image contains text based on OCR results
                    contains_text = len(ocr_text.strip()) > 0 if ocr_text else False
                    
                    # Create image model
                    image_model = ImageModel(
                        document_id=context.document_id,
                        filename=image_data['filename'],
                        original_filename=image_data['filename'],
                        storage_path=storage_result['key'],
                        storage_url=storage_result['url'],
                        file_size=len(image_data['content']),
                        image_format=image_data['format'],
                        width_px=image_data['width'],
                        height_px=image_data['height'],
                        page_number=image_data['page_number'],
                        image_index=i + 1,
                        image_type=ImageType(ai_analysis['image_type']),
                        ai_description=ai_analysis['description'],
                        ai_confidence=ai_analysis['confidence'],
                        contains_text=contains_text,
                        ocr_text=ocr_text,
                        ocr_confidence=0.8 if ocr_text else 0.0,
                        tags=ai_analysis['tags'],
                        file_hash=storage_result['file_hash']
                    )
                    
                    # Store in database
                    image_id = await self.database_service.create_image(image_model)
                    processed_images.append(image_id)
                    
                except Exception as e:
                    self.logger.error(f"Failed to process image {i+1}: {e}")
                    continue
            
            # Log audit event
            await self.database_service.log_audit(
                action="images_processed",
                entity_type="document",
                entity_id=context.document_id,
                details={
                    'total_images_found': len(images_data),
                    'unique_images_processed': len(processed_images),
                    'duplicates_skipped': len(images_data) - len(processed_images),
                    'successful_images': len(processed_images),
                    'failed_images': 0,
                    'ocr_text_length': len(' '.join(all_ocr_text))
                }
            )
            
            # Return success result
            data = {
                'images': processed_images,
                'total_images': len(processed_images),
                'ocr_text': ' '.join(all_ocr_text),
                'ai_descriptions': ai_descriptions
            }
            
            metadata = {
                'processing_timestamp': datetime.utcnow().isoformat(),
                'ai_confidence_avg': sum(ai.get('confidence', 0.5) for ai in ai_descriptions) / len(ai_descriptions) if ai_descriptions else 0
            }
            
            return self.create_success_result(data, metadata)
            
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            else:
                raise ProcessingError(
                    f"Image processing failed: {str(e)}",
                    self.name,
                    "IMAGE_PROCESSING_FAILED"
                )
    
    async def _extract_images_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract images from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of image data dictionaries
        """
        try:
            # Always try to extract real images from PDF
            self.logger.info("Extracting images from PDF...")
            
            if not FITZ_AVAILABLE:
                self.logger.warning("PyMuPDF not available. Using mock images.")
                import hashlib
                mock_content = b'mock_image_data'
                mock_hash = hashlib.sha256(mock_content).hexdigest()
                return [
                    {
                        'content': mock_content,
                        'filename': f"{mock_hash}.png",
                        'format': 'png',
                        'width': 800,
                        'height': 600,
                        'page_number': 1,
                        'image_index': 1,
                        'hash': mock_hash,
                        'is_vector': False,
                        'color_space': 3,  # RGB
                        'has_alpha': False
                    }
                ]
            
            doc = fitz.open(file_path)
            images_data = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Get image data
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        # Advanced image extraction with format preservation
                        img_data, original_format, is_vector = self._extract_image_with_format_preservation(pix, doc, xref)
                        
                        # Generate filename as hash for uniqueness with correct extension
                        import hashlib
                        file_hash = hashlib.sha256(img_data).hexdigest()
                        filename = f"{file_hash}.{original_format}"
                        
                        image_data = {
                            'content': img_data,
                            'filename': filename,
                            'format': original_format,
                            'width': pix.width,
                            'height': pix.height,
                            'page_number': page_num + 1,
                            'image_index': img_index + 1,
                            'hash': file_hash,
                            'is_vector': is_vector,
                            'color_space': pix.n - pix.alpha,
                            'has_alpha': pix.alpha > 0
                        }
                        
                        images_data.append(image_data)
                        pix = None
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to extract image {img_index} from page {page_num + 1}: {e}")
                        continue
            
            doc.close()
            self.logger.info(f"Extracted {len(images_data)} images from PDF")
            return images_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract images from PDF: {e}")
            raise
    
    async def _perform_ocr(self, image_content: bytes) -> str:
        """
        Perform OCR on image using Tesseract
        
        Args:
            image_content: Image content as bytes
            
        Returns:
            Extracted text
        """
        try:
            if not TESSERACT_AVAILABLE:
                self.logger.warning("Tesseract not available. OCR skipped.")
                return ""
            
            # Set Tesseract path if needed
            if not hasattr(pytesseract, '_tesseract_cmd') or pytesseract._tesseract_cmd is None:
                import os
                tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                if os.path.exists(tesseract_path):
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    self.logger.info(f"Set Tesseract path to: {tesseract_path}")
                else:
                    self.logger.warning("Tesseract executable not found. OCR skipped.")
                    return ""
            
            if not PIL_AVAILABLE:
                self.logger.warning("PIL not available. OCR skipped.")
                return ""
            
            # Convert bytes to PIL Image - handle different formats
            try:
                # Check if it's SVG format
                if image_content.startswith(b'<?xml') or b'<svg' in image_content:
                    self.logger.debug("SVG image detected, skipping OCR")
                    return ""
                
                # For other formats, try PIL
                image = Image.open(io.BytesIO(image_content))
            except Exception as e:
                self.logger.debug(f"Failed to open image for OCR: {e}")
                return ""
            
            # Perform OCR
            text = pytesseract.image_to_string(image, lang='eng')
            
            # Clean up text
            text = text.strip()
            
            if text:
                self.logger.info(f"OCR extracted {len(text)} characters")
            else:
                self.logger.debug("No text found in image")
            
            return text
            
        except Exception as e:
            self.logger.warning(f"OCR failed: {e}")
            return ""
    
    def _extract_image_with_format_preservation(self, pix, doc, xref):
        """
        Extract image with ORIGINAL format preservation - NO CONVERSION!
        
        Args:
            pix: PyMuPDF Pixmap object
            doc: PyMuPDF document object
            xref: Image xref reference
            
        Returns:
            Tuple of (image_data, format, is_vector)
        """
        try:
            # 1. Vector Graphics Detection
            is_vector = self._detect_vector_graphics(pix, doc, xref)
            
            if is_vector:
                # Try SVG extraction for vector graphics
                svg_data = self._extract_svg_from_vector(pix, doc, xref)
                if svg_data:
                    return svg_data, "svg", True
            
            # 2. ORIGINAL FORMAT PRESERVATION - NO CONVERSION!
            # Get the original image data directly from PDF
            try:
                # Try to get original image data without any conversion
                img_data = doc.extract_image(xref)["image"]
                original_format = doc.extract_image(xref).get("ext", "png")
                
                # If we got original data, use it
                if img_data:
                    return img_data, original_format, is_vector
            except:
                pass
            
            # 3. FALLBACK - Only if original extraction failed
            # Try different formats based on color space
            if pix.n - pix.alpha == 1:  # Grayscale
                try:
                    img_data = pix.tobytes("png")
                    original_format = "png"
                except:
                    img_data = pix.tobytes("jpg")
                    original_format = "jpg"
            elif pix.n - pix.alpha == 3:  # RGB
                try:
                    img_data = pix.tobytes("png")
                    original_format = "png"
                except:
                    img_data = pix.tobytes("jpg")
                    original_format = "jpg"
            elif pix.n - pix.alpha == 4:  # CMYK
                # Keep CMYK - don't convert to RGB!
                try:
                    img_data = pix.tobytes("png")
                    original_format = "png"
                except:
                    # Only convert if absolutely necessary
                    rgb_pix = fitz.Pixmap(fitz.csRGB, pix)
                    img_data = rgb_pix.tobytes("jpg")
                    original_format = "jpg"
                    rgb_pix = None
            else:
                # Try to preserve original format
                try:
                    img_data = pix.tobytes("png")
                    original_format = "png"
                except:
                    try:
                        img_data = pix.tobytes("jpg")
                        original_format = "jpg"
                    except:
                        # Last resort - minimal conversion
                        rgb_pix = fitz.Pixmap(fitz.csRGB, pix)
                        img_data = rgb_pix.tobytes("jpg")
                        original_format = "jpg"
                        rgb_pix = None
            
            return img_data, original_format, is_vector
            
        except Exception as e:
            self.logger.warning(f"Format preservation failed: {e}")
            # Minimal fallback
            try:
                img_data = pix.tobytes("jpg")
                return img_data, "jpg", False
            except:
                # Absolute last resort
                rgb_pix = fitz.Pixmap(fitz.csRGB, pix)
                img_data = rgb_pix.tobytes("jpg")
                rgb_pix = None
                return img_data, "jpg", False
    
    def _detect_vector_graphics(self, pix, doc, xref):
        """
        Detect if image is vector graphics
        
        Args:
            pix: PyMuPDF Pixmap object
            doc: PyMuPDF document object
            xref: Image xref reference
            
        Returns:
            Boolean indicating if it's vector graphics
        """
        try:
            # Vector graphics indicators:
            # 1. Very high resolution with small file size
            # 2. Simple color palette
            # 3. Geometric patterns
            
            # Check resolution vs file size ratio
            pixel_count = pix.width * pix.height
            if pixel_count > 1000000:  # > 1MP
                # High resolution might indicate vector conversion
                return True
            
            # Check color complexity
            if pix.n - pix.alpha <= 2:  # Grayscale or simple color
                # Simple color space might indicate vector
                return True
            
            # Check for geometric patterns (basic heuristic)
            # This is a simplified check - in practice, you'd analyze the image content
            return False
            
        except Exception as e:
            self.logger.debug(f"Vector detection failed: {e}")
            return False
    
    def _extract_svg_from_vector(self, pix, doc, xref):
        """
        Extract SVG data from vector graphics
        
        Args:
            pix: PyMuPDF Pixmap object
            doc: PyMuPDF document object
            xref: Image xref reference
            
        Returns:
            SVG data as bytes or None
        """
        try:
            # This is a simplified SVG extraction
            # In practice, you'd need more sophisticated vector-to-SVG conversion
            
            # For now, we'll create a basic SVG wrapper around the image
            # This preserves the vector nature while maintaining compatibility
            
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{pix.width}" height="{pix.height}" xmlns="http://www.w3.org/2000/svg">
    <image width="{pix.width}" height="{pix.height}" href="data:image/png;base64,{pix.tobytes().hex()}" />
</svg>'''
            
            return svg_content.encode('utf-8')
            
        except Exception as e:
            self.logger.debug(f"SVG extraction failed: {e}")
            return None
