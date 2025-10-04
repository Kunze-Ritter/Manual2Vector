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
                
                # Configure Tesseract path (Windows)
                try:
                    from backend.config.tesseract_config import configure_tesseract
                    configure_tesseract()
                except:
                    pass  # Configuration not critical
                
                # Test if Tesseract binary is actually installed
                pytesseract.get_tesseract_version()
                self.ocr_available = True
                self.logger.info("✅ OCR (Tesseract) available")
            except ImportError:
                self.ocr_available = False
                self.logger.warning("⚠️  pytesseract not installed - run: pip install pytesseract")
            except Exception as e:
                self.ocr_available = False
                self.logger.warning(f"⚠️  Tesseract OCR not available: {e}")
                self.logger.info("   Install Tesseract OCR:")
                self.logger.info("   • Windows: https://github.com/UB-Mannheim/tesseract/wiki")
                self.logger.info("   • Linux: sudo apt install tesseract-ocr")
                self.logger.info("   • macOS: brew install tesseract")
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
            
            success_count = 0
            for img in images:
                try:
                    # Open image
                    pil_image = Image.open(img['path'])
                    
                    # Run OCR with confidence data
                    ocr_data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
                    
                    # Extract text
                    ocr_text = pytesseract.image_to_string(pil_image)
                    
                    # Calculate average confidence (filter out -1 which means no text)
                    confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    # Store results
                    img['ocr_text'] = ocr_text.strip()
                    img['ocr_confidence'] = round(avg_confidence / 100, 2)  # Convert to 0-1 scale
                    img['contains_text'] = len(ocr_text.strip()) > 0
                    
                    if ocr_text.strip():
                        success_count += 1
                        self.logger.debug(f"OCR extracted {len(ocr_text)} chars from {img['filename']}")
                    
                except Exception as e:
                    self.logger.debug(f"OCR failed for {img['filename']}: {e}")
                    img['ocr_text'] = ''
                    img['ocr_confidence'] = 0.0
                    img['contains_text'] = False
            
            self.logger.success(f"✅ OCR processed {success_count}/{len(images)} images with text")
            
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
            Images with 'ai_description' and 'ai_confidence' fields added
        """
        if not self.vision_available:
            self.logger.debug("Vision AI not available, skipping")
            return images
        
        # Limit to max_images to avoid overwhelming the system
        images_to_process = images[:max_images]
        skipped_count = len(images) - len(images_to_process)
        
        if skipped_count > 0:
            self.logger.info(f"Processing first {len(images_to_process)} images (skipping {skipped_count} to avoid overload)")
        else:
            self.logger.info(f"Processing {len(images_to_process)} images with Vision AI...")
        
        try:
            import requests
            import base64
            
            ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            
            # Find best vision model
            try:
                response = requests.get(f"{ollama_url}/api/tags", timeout=2)
                models = response.json().get('models', [])
                vision_models = [m for m in models if 'llava' in m.get('name', '').lower()]
                
                if not vision_models:
                    self.logger.warning("No LLaVA model found")
                    return images
                
                model_name = vision_models[0]['name']
                self.logger.debug(f"Using vision model: {model_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to get Ollama models: {e}")
                return images
            
            # Process each image
            success_count = 0
            for img in images_to_process:
                try:
                    # Read image and encode to base64
                    with open(img['path'], 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode('utf-8')
                    
                    # Prepare prompt
                    prompt = """Analyze this technical diagram or image from a service manual.
Describe what you see in 2-3 sentences. Focus on:
- Type of component or diagram (e.g., circuit board, exploded view, flowchart)
- Key parts or elements visible
- Any labels or numbers you can read

Keep it concise and technical."""
                    
                    # Call Ollama Vision API
                    response = requests.post(
                        f"{ollama_url}/api/generate",
                        json={
                            "model": model_name,
                            "prompt": prompt,
                            "images": [image_data],
                            "stream": False
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        description = result.get('response', '').strip()
                        
                        # Store results
                        img['ai_description'] = description
                        img['ai_confidence'] = 0.8  # LLaVA default confidence
                        img['contains_text'] = any(keyword in description.lower() 
                                                  for keyword in ['label', 'text', 'number', 'code'])
                        
                        success_count += 1
                        self.logger.debug(f"Analyzed {img['filename']}: {description[:50]}...")
                    else:
                        self.logger.warning(f"Vision API error for {img['filename']}: {response.status_code}")
                        img['ai_description'] = ''
                        img['ai_confidence'] = 0.0
                        
                except Exception as e:
                    self.logger.debug(f"Vision AI failed for {img['filename']}: {e}")
                    img['ai_description'] = ''
                    img['ai_confidence'] = 0.0
            
            self.logger.success(f"✅ Vision AI analyzed {success_count}/{len(images_to_process)} images")
            
            return images
            
        except Exception as e:
            self.logger.error(f"Vision AI processing failed: {e}")
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
