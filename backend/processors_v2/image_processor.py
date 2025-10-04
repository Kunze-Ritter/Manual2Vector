"""
Image Processor - Extract and analyze images from PDFs

Stage 3 of the processing pipeline.

Features:
- Extract images from PDFs (PyMuPDF)
- Filter relevant images (skip logos, headers, etc.)
- OCR for text in images (Tesseract)
- Vision AI analysis (LLaVA via Ollama)
- Image classification (diagram, table, photo, etc.)
- Integration with Image Storage Processor
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import io
from PIL import Image
import fitz  # PyMuPDF
from datetime import datetime

from .logger import get_logger
from .stage_tracker import StageTracker


class ImageProcessor:
    """
    Stage 3: Image Processor
    
    Extracts and analyzes images from service manuals.
    """
    
    def __init__(
        self,
        supabase_client=None,
        min_image_size: int = 10000,  # Min 100x100px
        max_images_per_doc: int = 999999,  # Unlimited (user will check manually)
        enable_ocr: bool = True,
        enable_vision: bool = True
    ):
        """
        Initialize image processor
        
        Args:
            supabase_client: Supabase client for stage tracking
            min_image_size: Minimum image size in pixels (width * height)
            max_images_per_doc: Maximum images to extract per document (default: unlimited)
            enable_ocr: Enable OCR with Tesseract
            enable_vision: Enable Vision AI with LLaVA
        """
        self.logger = get_logger()
        self.min_image_size = min_image_size
        self.max_images_per_doc = max_images_per_doc
        self.enable_ocr = enable_ocr
        self.enable_vision = enable_vision
        
        # Stage tracker
        if supabase_client:
            self.stage_tracker = StageTracker(supabase_client)
        else:
            self.stage_tracker = None
        
        # Check OCR availability
        if self.enable_ocr:
            try:
                import pytesseract
                self.ocr_available = True
                self.logger.info("OCR (Tesseract) available")
            except ImportError:
                self.ocr_available = False
                self.logger.warning("OCR not available - install pytesseract")
        else:
            self.ocr_available = False
        
        # Check Vision AI availability
        if self.enable_vision:
            self.vision_available = self._check_vision_availability()
        else:
            self.vision_available = False
    
    def _check_vision_availability(self) -> bool:
        """Check if Vision AI (LLaVA) is available via Ollama"""
        try:
            import requests
            ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            
            # Check if Ollama is running
            response = requests.get(f"{ollama_url}/api/tags", timeout=2)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                
                # Check for vision models
                vision_models = [m for m in models if 'llava' in m.get('name', '').lower() 
                                or 'bakllava' in m.get('name', '').lower()]
                
                if vision_models:
                    self.logger.success(f"Vision AI available: {vision_models[0].get('name')}")
                    return True
                else:
                    self.logger.warning("No vision models found in Ollama")
                    return False
            else:
                self.logger.warning("Ollama not responding")
                return False
                
        except Exception as e:
            self.logger.warning(f"Vision AI check failed: {e}")
            return False
    
    def process_document(
        self,
        document_id: UUID,
        pdf_path: Path,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Process all images in a PDF document
        
        Args:
            document_id: Document UUID
            pdf_path: Path to PDF file
            output_dir: Directory to save extracted images (optional)
            
        Returns:
            Dict with processing results
        """
        if not pdf_path.exists():
            return {
                'success': False,
                'error': f'PDF not found: {pdf_path}',
                'images': []
            }
        
        # Start stage tracking
        if self.stage_tracker:
            self.stage_tracker.start_stage(str(document_id), 'image_processing')
        
        try:
            self.logger.info(f"Processing images from: {pdf_path.name}")
            
            # Create output directory
            if output_dir is None:
                output_dir = Path("temp_images") / str(document_id)
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract images
            extracted_images = self._extract_images(pdf_path, output_dir)
            
            self.logger.info(f"Extracted {len(extracted_images)} images")
            
            # Filter images (skip logos, headers, etc.)
            filtered_images = self._filter_images(extracted_images)
            
            self.logger.info(f"Filtered to {len(filtered_images)} relevant images")
            
            # Classify images
            classified_images = self._classify_images(filtered_images)
            
            # OCR if enabled
            if self.ocr_available and self.enable_ocr:
                self.logger.info("Running OCR on images...")
                classified_images = self._run_ocr(classified_images)
            
            # Vision AI if enabled
            if self.vision_available and self.enable_vision:
                self.logger.info("Running Vision AI analysis...")
                classified_images = self._run_vision_ai(classified_images)
            
            # Complete stage tracking
            if self.stage_tracker:
                self.stage_tracker.complete_stage(
                    str(document_id),
                    'image_processing',
                    metadata={
                        'images_extracted': len(extracted_images),
                        'images_filtered': len(filtered_images),
                        'images_classified': len(classified_images)
                    }
                )
            
            return {
                'success': True,
                'images': classified_images,
                'total_extracted': len(extracted_images),
                'total_filtered': len(filtered_images),
                'output_dir': str(output_dir)
            }
            
        except Exception as e:
            error_msg = f"Image processing failed: {e}"
            self.logger.error(error_msg)
            
            if self.stage_tracker:
                self.stage_tracker.fail_stage(
                    str(document_id),
                    'image_processing',
                    error_msg
                )
            
            return {
                'success': False,
                'error': error_msg,
                'images': []
            }
    
    def _extract_images(
        self,
        pdf_path: Path,
        output_dir: Path
    ) -> List[Dict[str, Any]]:
        """
        Extract all images from PDF using PyMuPDF
        
        Args:
            pdf_path: Path to PDF
            output_dir: Output directory for images
            
        Returns:
            List of extracted image info dicts
        """
        images = []
        
        try:
            # Open PDF
            pdf_document = fitz.open(str(pdf_path))
            
            image_counter = 0
            
            # Iterate through pages
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Get images on page
                image_list = page.get_images(full=True)
                
                for img_index, img_info in enumerate(image_list):
                    if image_counter >= self.max_images_per_doc:
                        self.logger.warning(f"Reached max images limit: {self.max_images_per_doc}")
                        break
                    
                    try:
                        # Extract image
                        xref = img_info[0]
                        base_image = pdf_document.extract_image(xref)
                        
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # Open with PIL to get dimensions
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        width, height = pil_image.size
                        
                        # Check minimum size
                        if width * height < self.min_image_size:
                            continue
                        
                        # Save image
                        image_filename = f"page_{page_num:04d}_img_{img_index:03d}.{image_ext}"
                        image_path = output_dir / image_filename
                        
                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)
                        
                        # Store image info
                        images.append({
                            'path': str(image_path),
                            'filename': image_filename,
                            'page_num': page_num + 1,  # 1-indexed
                            'width': width,
                            'height': height,
                            'format': image_ext,
                            'size_bytes': len(image_bytes),
                            'extracted_at': datetime.utcnow().isoformat()
                        })
                        
                        image_counter += 1
                        
                    except Exception as e:
                        self.logger.debug(f"Failed to extract image {img_index} from page {page_num}: {e}")
                        continue
                
                if image_counter >= self.max_images_per_doc:
                    break
            
            pdf_document.close()
            
            return images
            
        except Exception as e:
            self.logger.error(f"Image extraction failed: {e}")
            return []
    
    def _filter_images(
        self,
        images: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter out non-relevant images (logos, headers, etc.)
        
        Args:
            images: List of extracted images
            
        Returns:
            Filtered list of images
        """
        filtered = []
        
        for img in images:
            # Skip very small images (likely logos/icons)
            if img['width'] < 100 or img['height'] < 100:
                continue
            
            # Skip very large images (likely full-page scans)
            if img['width'] > 4000 or img['height'] > 4000:
                continue
            
            # Skip extreme aspect ratios (likely headers/footers)
            aspect_ratio = img['width'] / img['height']
            if aspect_ratio > 10 or aspect_ratio < 0.1:
                continue
            
            filtered.append(img)
        
        return filtered
    
    def _classify_images(
        self,
        images: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Classify images by type (diagram, table, photo, etc.)
        
        Simple heuristic-based classification.
        Vision AI will provide better classification later.
        
        Args:
            images: List of images
            
        Returns:
            Images with 'type' field added
        """
        for img in images:
            # Simple heuristic classification
            aspect_ratio = img['width'] / img['height']
            
            # Tables tend to be wide
            if aspect_ratio > 2.0:
                img['type'] = 'table'
            # Diagrams tend to be squarish
            elif 0.7 <= aspect_ratio <= 1.3:
                img['type'] = 'diagram'
            # Charts can be various shapes
            elif aspect_ratio > 1.3:
                img['type'] = 'chart'
            else:
                img['type'] = 'unknown'
            
            # This will be improved by Vision AI
            img['classification_method'] = 'heuristic'
        
        return images
    
    def _run_ocr(
        self,
        images: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Run OCR on images to extract text
        
        Args:
            images: List of images
            
        Returns:
            Images with 'ocr_text' field added
        """
        if not self.ocr_available:
            return images
        
        try:
            import pytesseract
            
            for img in images:
                try:
                    # Open image
                    pil_image = Image.open(img['path'])
                    
                    # Run OCR
                    ocr_text = pytesseract.image_to_string(pil_image)
                    
                    # Store result
                    img['ocr_text'] = ocr_text.strip()
                    img['ocr_available'] = True
                    
                except Exception as e:
                    self.logger.debug(f"OCR failed for {img['filename']}: {e}")
                    img['ocr_text'] = ''
                    img['ocr_available'] = False
            
            return images
            
        except Exception as e:
            self.logger.error(f"OCR processing failed: {e}")
            return images
    
    def _run_vision_ai(
        self,
        images: List[Dict[str, Any]],
        max_images: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Run Vision AI (LLaVA) on images
        
        Args:
            images: List of images
            max_images: Maximum images to process (to avoid overload)
            
        Returns:
            Images with 'vision_description' field added
        """
        if not self.vision_available:
            return images
        
        # Limit to max_images to avoid overwhelming the system
        images_to_process = images[:max_images]
        
        self.logger.info(f"Processing {len(images_to_process)} images with Vision AI...")
        
        # This will be implemented in detail
        # For now, placeholder
        for img in images_to_process:
            img['vision_processed'] = False
            img['vision_description'] = ''
        
        return images


# Example usage
if __name__ == "__main__":
    from uuid import uuid4
    
    processor = ImageProcessor()
    
    # Test with a PDF
    pdf_path = Path("../../AccurioPress_C4080_C4070_C84hc_C74hc_AccurioPrint_C4065_C4065P_SM_EN_20250127.pdf")
    
    if pdf_path.exists():
        print(f"Processing: {pdf_path.name}")
        
        result = processor.process_document(
            document_id=uuid4(),
            pdf_path=pdf_path
        )
        
        if result['success']:
            print(f"\n✅ Extracted {result['total_extracted']} images")
            print(f"✅ Filtered to {result['total_filtered']} relevant images")
            print(f"✅ Saved to: {result['output_dir']}")
        else:
            print(f"\n❌ Failed: {result['error']}")
    else:
        print("Test PDF not found")
