"""
Image Processor for KR-AI-Engine
Stage 3: Image extraction, OCR, and classification (Object Storage)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import io

try:
    import PyMuPDF as fitz
    from PIL import Image
    import pytesseract
except ImportError:
    fitz = None
    Image = None
    pytesseract = None

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
            
            # Process each image
            processed_images = []
            all_ocr_text = []
            ai_descriptions = []
            
            for i, image_data in enumerate(images_data):
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
                    
                    # Perform OCR
                    ocr_text = await self._perform_ocr(image_data['content'])
                    if ocr_text:
                        all_ocr_text.append(ocr_text)
                    
                    # AI image analysis
                    ai_analysis = await self.ai_service.analyze_image(
                        image=image_data['content'],
                        description=f"Technical image from page {image_data['page_number']}"
                    )
                    ai_descriptions.append(ai_analysis)
                    
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
                        contains_text=ai_analysis['contains_text'],
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
                    'total_images': len(processed_images),
                    'successful_images': len(processed_images),
                    'failed_images': len(images_data) - len(processed_images),
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
            if fitz is None:
                # Mock mode for testing
                self.logger.info("Using mock image extraction for testing")
                return [
                    {
                        'content': b'mock_image_data',
                        'filename': 'mock_image_1.png',
                        'format': 'png',
                        'width': 800,
                        'height': 600,
                        'page_number': 1,
                        'image_index': 1
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
                        
                        # Convert to PNG if needed
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                        else:  # CMYK
                            pix1 = fitz.Pixmap(fitz.csRGB, pix)
                            img_data = pix1.tobytes("png")
                            pix1 = None
                        
                        # Generate filename
                        filename = f"page_{page_num + 1}_img_{img_index + 1}.png"
                        
                        image_data = {
                            'content': img_data,
                            'filename': filename,
                            'format': 'png',
                            'width': pix.width,
                            'height': pix.height,
                            'page_number': page_num + 1,
                            'image_index': img_index + 1
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
        Perform OCR on image
        
        Args:
            image_content: Image content as bytes
            
        Returns:
            Extracted text
        """
        try:
            if pytesseract is None:
                self.logger.warning("Tesseract not available. OCR skipped.")
                return ""
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_content))
            
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
