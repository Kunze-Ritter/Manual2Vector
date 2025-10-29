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
import json
import time
import random
import threading
import statistics
import sys
from collections import deque
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Deque
import asyncio
from uuid import UUID
import io
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import base64

import requests
from requests.adapters import HTTPAdapter
from requests import exceptions as requests_exceptions
from urllib3.util.retry import Retry
from PIL import Image, ImageOps
import fitz  # PyMuPDF
from datetime import datetime

from backend.core.base_processor import BaseProcessor, Stage
from .stage_tracker import StageTracker
from backend.pipeline.metrics import metrics
from backend.processors.logger import sanitize_document_name, text_stats


class ImageProcessor(BaseProcessor):
    """
    Stage 3: Image Processor
    
    Extracts and analyzes images from service manuals.
    """
    
    def __init__(
        self,
        supabase_client=None,
        storage_service=None,
        ai_service=None,
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
        super().__init__(name="image_processor")
        self.stage = Stage.IMAGE_PROCESSING
        self.min_image_size = min_image_size
        self.max_images_per_doc = max_images_per_doc
        self.enable_ocr = enable_ocr
        self.enable_vision = enable_vision
        self.storage_service = storage_service
        self.ai_service = ai_service
        self.database_service = None
        supabase_client_obj = None

        if supabase_client:
            # Supabase client may be provided directly or as service wrapper
            if hasattr(supabase_client, "client") and getattr(supabase_client, "client"):
                self.database_service = supabase_client
                supabase_client_obj = supabase_client.client
            else:
                supabase_client_obj = supabase_client
        self.cleanup_temp_images = os.getenv('IMAGE_PROCESSOR_CLEANUP', '1') != '0'
        
        # Stage tracker
        if supabase_client_obj:
            self.stage_tracker = StageTracker(supabase_client_obj)
        else:
            self.stage_tracker = None
        
        # HTTP session configuration
        self.request_timeout = float(os.getenv('VISION_REQUEST_TIMEOUT', '60'))
        self.max_retries = int(os.getenv('VISION_REQUEST_MAX_RETRIES', '4'))
        self.retry_base_delay = float(os.getenv('VISION_RETRY_BASE_DELAY', '1.5'))
        self.retry_jitter = float(os.getenv('VISION_RETRY_JITTER', '0.5'))
        self.session = self._create_session()
        
        # OCR threading configuration
        cpu_count = os.cpu_count() or 4
        max_workers_config = int(os.getenv('OCR_MAX_WORKERS', max(1, cpu_count // 2)))
        self.ocr_executor = ThreadPoolExecutor(max_workers=max_workers_config)
        self.ocr_latency_window: Deque[float] = deque(maxlen=200)
        
        # Preprocessing configuration
        self.preprocess_enabled = os.getenv('OCR_PREPROCESSING_ENABLED', '1') != '0'
        self.preprocess_grayscale = os.getenv('OCR_PREPROCESS_GRAYSCALE', '1') != '0'
        self.preprocess_binarize = os.getenv('OCR_PREPROCESS_BINARIZE', '1') != '0'
        self.preprocess_upscale = int(os.getenv('OCR_PREPROCESS_UPSCALE', '1'))  # scale factor
        
        # Vision guardrails
        self.max_image_mb = float(os.getenv('VISION_MAX_IMAGE_MB', '12.0'))
        self.max_images_per_document = int(os.getenv('VISION_MAX_IMAGES_PER_DOCUMENT', '80'))
        self.circuit_breaker_threshold = int(os.getenv('VISION_FAILURE_THRESHOLD', '5'))
        self.circuit_breaker_timeout = float(os.getenv('VISION_BREAKER_TIMEOUT', '120'))
        self._vision_failure_count = 0
        self._vision_breaker_until: Optional[float] = None
        self.global_vision_limit = int(os.getenv('VISION_GLOBAL_LIMIT', '500'))
        self.global_vision_window = float(os.getenv('VISION_GLOBAL_WINDOW_SECONDS', '3600'))
        self._vision_usage: Deque[float] = deque()
        self._vision_model_cache: Optional[str] = None
        self._vision_model_checked_at: float = 0.0
        self.vision_model_cache_ttl = float(os.getenv('VISION_MODEL_CACHE_TTL_SECONDS', '300'))

        # Check OCR availability
        if self.enable_ocr:
            try:
                import pytesseract
                
                # Configure Tesseract path (Windows) - BEFORE testing version
                if sys.platform == "win32":
                    possible_paths = [
                        r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
                        r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
                    ]
                    
                    # Try to find Tesseract
                    for path in possible_paths:
                        if os.path.exists(path):
                            pytesseract.pytesseract.tesseract_cmd = path
                            self.logger.debug(f"Configured Tesseract: {path}")
                            break
                
                # Test if Tesseract binary is actually installed
                version = pytesseract.get_tesseract_version()
                self.ocr_available = True
                self.logger.info(f"✅ OCR (Tesseract) available - v{version}")
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

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        adapter_retries = max(0, self.max_retries - 1)
        retry = Retry(
            total=adapter_retries,
            read=adapter_retries,
            connect=adapter_retries,
            backoff_factor=self.retry_base_delay,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=int(os.getenv('VISION_HTTP_POOL_CONNECTIONS', '10')),
            pool_maxsize=int(os.getenv('VISION_HTTP_POOL_MAXSIZE', '20'))
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _apply_preprocessing(self, pil_image: Image.Image) -> Image.Image:
        if not self.preprocess_enabled:
            return pil_image

        processed = pil_image
        if self.preprocess_grayscale:
            processed = ImageOps.grayscale(processed)

        if self.preprocess_upscale > 1:
            new_size = (
                max(1, processed.width * self.preprocess_upscale),
                max(1, processed.height * self.preprocess_upscale),
            )
            processed = processed.resize(new_size, Image.BICUBIC)

        if self.preprocess_binarize:
            processed = processed.convert('L')
            processed = processed.point(lambda x: 255 if x > 180 else 0, '1')

        return processed

    def _vision_guard_allows(self, image: Dict[str, Any], processed_count: int) -> bool:
        if processed_count >= self.max_images_per_document:
            self.logger.info(
                "Vision guardrails dropping %s - document limit %d reached",
                image['filename'],
                self.max_images_per_document,
            )
            return False

        size_mb = image.get('size_bytes', 0) / (1024 * 1024)
        if size_mb > self.max_image_mb:
            self.logger.warning(
                "Vision guardrails dropping %s - size %.2fMB exceeds cap %.2fMB",
                image['filename'],
                size_mb,
                self.max_image_mb,
            )
            return False

        if self._vision_breaker_until and time.time() < self._vision_breaker_until:
            self.logger.warning(
                "Vision circuit breaker open (until %.0f) - skipping %s",
                self._vision_breaker_until,
                image['filename'],
            )
            return False

        return True

    def _record_ocr_latency(self, latency: float) -> None:
        self.ocr_latency_window.append(latency)
        while len(self.ocr_latency_window) > self.ocr_latency_window.maxlen:
            self.ocr_latency_window.popleft()

    @staticmethod
    def _calculate_percentiles(samples: List[float]) -> Tuple[float, float]:
        if len(samples) < 5:
            return 0.0, 0.0
        try:
            p95 = statistics.quantiles(samples, n=100)[94]
            p99 = statistics.quantiles(samples, n=100)[98]
            return p95, p99
        except Exception:
            return 0.0, 0.0

    def _vision_quota_allows(self) -> bool:
        now = time.time()
        while self._vision_usage and (now - self._vision_usage[0]) > self.global_vision_window:
            self._vision_usage.popleft()
        allowed = len(self._vision_usage) < self.global_vision_limit
        if not allowed:
            self.logger.warning(
                "Vision guardrails global limit reached (%d in %.0fs window)",
                self.global_vision_limit,
                self.global_vision_window,
            )
        return allowed

    def _record_vision_usage(self) -> None:
        now = time.time()
        self._vision_usage.append(now)

    def _reset_vision_failures(self) -> None:
        if self._vision_failure_count:
            self.logger.debug("Vision circuit breaker reset after successful request")
        self._vision_failure_count = 0
        self._vision_breaker_until = None

    def _record_vision_failure(self, reason: str) -> None:
        self._vision_failure_count += 1
        self.logger.warning(
            "Vision request failed (%s) - failure count %d/%d",
            reason,
            self._vision_failure_count,
            self.circuit_breaker_threshold,
        )
        if self._vision_failure_count >= self.circuit_breaker_threshold:
            self._vision_breaker_until = time.time() + self.circuit_breaker_timeout
            self.logger.error(
                "Vision circuit breaker OPEN for %.0fs after %d consecutive failures",
                self.circuit_breaker_timeout,
                self._vision_failure_count,
            )

    def _get_vision_model_name(self) -> Optional[str]:
        now = time.time()
        if (
            self._vision_model_cache
            and (now - self._vision_model_checked_at) < self.vision_model_cache_ttl
        ):
            return self._vision_model_cache

        ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        try:
            response = self.session.get(
                f"{ollama_url}/api/tags",
                timeout=self.request_timeout,
            )
            if response.status_code == 200:
                models = response.json().get('models', [])
                vision_models = [
                    m for m in models
                    if 'llava' in m.get('name', '').lower()
                    or 'bakllava' in m.get('name', '').lower()
                ]
                if vision_models:
                    self._vision_model_cache = vision_models[0]['name']
                    self._vision_model_checked_at = now
                    self.logger.debug(
                        "Cached vision model '%s' (ttl %.0fs)",
                        self._vision_model_cache,
                        self.vision_model_cache_ttl,
                    )
                    return self._vision_model_cache
                self.logger.warning("No vision models found in Ollama")
            else:
                self.logger.warning(
                    "Vision model discovery failed with status %s",
                    response.status_code,
                )
        except Exception as exc:
            self.logger.warning("Vision model discovery error: %s", exc)

        self._vision_model_cache = None
        self._vision_model_checked_at = now
        return None

    def _check_vision_availability(self) -> bool:
        """Check if Vision AI (LLaVA) is available via Ollama"""
        try:
            model_name = self._get_vision_model_name()
            if model_name:
                self.logger.success(f"Vision AI available: {model_name}")
                return True
            self.logger.warning("Vision AI unavailable - no suitable models discovered")
            return False

        except Exception as e:
            self.logger.warning(f"Vision AI check failed: {e}")
            return False
    
    async def process(self, context) -> Dict[str, Any]:
        """Async pipeline entrypoint wrapping `process_document`."""
        if not hasattr(context, 'document_id') or not hasattr(context, 'file_path'):
            raise ValueError("Processing context must include 'document_id' and 'file_path'")

        document_id = getattr(context, 'document_id')
        pdf_path = Path(context.file_path)
        output_dir = getattr(context, 'output_dir', None)

        loop = asyncio.get_running_loop()
        manufacturer = getattr(context, 'manufacturer', None) or getattr(context, 'processing_config', {}).get('manufacturer')
        document_type = getattr(context, 'document_type', None) or getattr(context, 'processing_config', {}).get('document_type')

        with metrics.stage_timer(
            stage=self.stage.value,
            manufacturer=manufacturer or 'unknown',
            document_type=document_type or 'unknown'
        ) as timer:
            try:
                result = await loop.run_in_executor(
                    None,
                    self.process_document,
                    document_id,
                    pdf_path,
                    output_dir
                )
            except Exception as exc:
                timer.stop(success=False, error_label=str(exc))
                raise
            else:
                timer.stop(
                    success=bool(result.get('success')),
                    error_label=str(result.get('error')) if result.get('error') else None
                )

        return result

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
            self.stage_tracker.start_stage(str(document_id), self.stage.value)
        
        with self.logger_context(document_id=document_id, stage=self.stage) as adapter:
            try:
                safe_pdf_name = sanitize_document_name(pdf_path.name)
                adapter.info("Processing images from: %s", safe_pdf_name)
            
                # Create output directory
                if output_dir is None:
                    output_dir = Path("temp_images") / str(document_id)

                output_dir.mkdir(parents=True, exist_ok=True)

                # Extract images
                extracted_images = self._extract_images(pdf_path, output_dir)

                if not extracted_images:
                    if self.stage_tracker:
                        self.stage_tracker.skip_stage(
                            str(document_id),
                            self.stage.value,
                            reason='No images found in document'
                        )
                    return {
                        'success': True,
                        'images_processed': 0,
                        'images': [],
                        'vision_enabled': self.enable_vision and self.vision_available,
                        'ocr_enabled': self.enable_ocr and self.ocr_available,
                        'message': 'No images found in document'
                    }

                adapter.info("Extracted %d images", len(extracted_images))

                # Filter images (skip logos, headers, etc.)
                filtered_images = self._filter_images(extracted_images)

                adapter.info(
                    "Filtered to %d relevant images (removed %d logos/headers)",
                    len(filtered_images),
                    len(extracted_images) - len(filtered_images)
                )

                # Classify images
                classified_images = self._classify_images(filtered_images)

                # OCR if enabled
                if self.ocr_available and self.enable_ocr:
                    adapter.info("Running OCR on images...")
                    classified_images = self._run_ocr(classified_images)

                # Vision AI if enabled
                if self.vision_available and self.enable_vision:
                    adapter.info("Running Vision AI analysis...")
                    classified_images = self._run_vision_ai(classified_images)

                # Queue storage uploads
                storage_task_count = self._queue_storage_tasks(
                    document_id=document_id,
                    images=classified_images,
                    adapter=adapter,
                )

                # Complete stage tracking
                if self.stage_tracker:
                    self.stage_tracker.complete_stage(
                        str(document_id),
                        self.stage.value,
                        metadata={
                            'images_extracted': len(extracted_images),
                            'images_filtered': len(filtered_images),
                            'images_classified': len(classified_images),
                            'storage_tasks_created': storage_task_count,
                        }
                    )

                # Clean up temporary images if configured and queued successfully
                if self.cleanup_temp_images and storage_task_count > 0:
                    self._cleanup_output_dir(output_dir, adapter)

                result = {
                    'success': True,
                    'images': classified_images,
                    'total_extracted': len(extracted_images),
                    'total_filtered': len(filtered_images),
                    'output_dir': str(output_dir) if output_dir else None,
                    'storage_tasks_created': storage_task_count,
                }
                self.logger.success(
                    f"Processed {len(classified_images)} images (extracted {len(extracted_images)})"
                )
                return result

            except Exception as e:
                error_msg = f"Image processing failed: {e}"
                adapter.error("Image processing failed: %s", e)

                if self.stage_tracker:
                    self.stage_tracker.fail_stage(
                        str(document_id),
                        self.stage.value,
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

    def _queue_storage_tasks(
        self,
        document_id: UUID,
        images: List[Dict[str, Any]],
        adapter
    ) -> int:
        if not images:
            return 0

        if not self.database_service or not getattr(self.database_service, "client", None):
            adapter.debug("Database service unavailable - skipping storage queue")
            return 0

        stage_payloads = []
        for image in images:
            try:
                image_path = Path(image.get('path', ''))
                if not image_path.exists():
                    continue

                with open(image_path, 'rb') as img_file:
                    content_bytes = img_file.read()

                encoded_content = base64.b64encode(content_bytes).decode('utf-8')

                payload = {
                    "document_id": str(document_id),
                    "filename": image.get('filename'),
                    "page_number": image.get('page_num'),
                    "image_type": image.get('type', 'unknown'),
                    "content": encoded_content,
                    "content_encoding": "base64",
                    "metadata": {
                        "width": image.get('width'),
                        "height": image.get('height'),
                        "format": image.get('format'),
                        "extracted_at": image.get('extracted_at')
                    }
                }

                stage_payloads.append({
                    "document_id": str(document_id),
                    "stage": "storage",
                    "artifact_type": "image",
                    "status": "pending",
                    "payload": payload
                })
            except Exception as exc:
                adapter.debug("Failed to queue image %s for storage: %s", image.get('filename'), exc)

        if not stage_payloads or not self.database_service:
            return 0

        try:
            self.database_service.client.table("vw_processing_queue").insert(stage_payloads).execute()
            adapter.info("Queued %d image artifacts for storage", len(stage_payloads))
            return len(stage_payloads)
        except Exception as exc:
            adapter.warning("Failed to queue image storage tasks: %s", exc)
            return 0

    def _cleanup_output_dir(self, output_dir: Path, adapter) -> None:
        try:
            if not output_dir or not output_dir.exists():
                return

            for item in output_dir.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                except Exception as exc:
                    adapter.debug("Failed to cleanup %s: %s", item, exc)

            output_dir.rmdir()
        except Exception as exc:
            adapter.debug("Failed to cleanup output directory %s: %s", output_dir, exc)
    
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
            futures = []
            start_time = time.perf_counter()

            def ocr_task(img: Dict[str, Any]) -> Tuple[Dict[str, Any], bool, float]:
                try:
                    pil_image = Image.open(img['path'])
                    pil_image = self._apply_preprocessing(pil_image)

                    task_start = time.perf_counter()
                    ocr_data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
                    latency = time.perf_counter() - task_start

                    text_parts = [word for word in ocr_data['text'] if word.strip()]
                    ocr_text = ' '.join(text_parts)

                    confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

                    img['ocr_text'] = ocr_text.strip()
                    img['ocr_confidence'] = round(avg_confidence / 100, 2)
                    img['contains_text'] = len(ocr_text.strip()) > 0

                    return img, bool(ocr_text.strip()), latency
                except Exception as exc:  # pragma: no cover - best effort
                    self.logger.debug("OCR failed for %s: %s", img.get('filename'), exc)
                    img['ocr_text'] = ''
                    img['ocr_confidence'] = 0.0
                    img['contains_text'] = False
                    return img, False, 0.0

            with self.logger.progress_bar(images, "Running OCR") as progress:
                task = progress.add_task("OCR processing", total=len(images))

                for img in images:
                    futures.append(self.ocr_executor.submit(ocr_task, img))

                for future in as_completed(futures):
                    processed_img, has_text, latency = future.result()
                    if latency > 0:
                        self._record_ocr_latency(latency)
                        p95, p99 = self._calculate_percentiles(list(self.ocr_latency_window))
                        if p95 or p99:
                            self.logger.debug(
                                "OCR latency percentiles: p95=%.3fs p99=%.3fs", p95, p99
                            )
                    if has_text:
                        success_count += 1
                    progress.update(task, advance=1, description=f"OCR: {success_count} images with text")

            duration = time.perf_counter() - start_time
            self.logger.success(
                "✅ OCR processed %d/%d images with text (%.2fs)",
                success_count,
                len(images),
                duration,
            )

            return images

        except Exception as e:
            self.logger.error(f"OCR processing failed: {e}")
            return images
    
    def _run_vision_ai(
        self,
        images: List[Dict[str, Any]],
        max_images: int = 50  # Increased from 20 to process more diagrams/technical drawings
    ) -> List[Dict[str, Any]]:
        """
        Run Vision AI (LLaVA) on images
        
        Args:
            images: List of images
            max_images: Maximum images to process (default: 50, ~10-15 min processing time)
            
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
            if not self._vision_quota_allows():
                self.logger.warning("Global vision quota exceeded - skipping vision analysis")
                return images

            model_name = self._get_vision_model_name()
            if not model_name:
                return images

            ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')

            success_count = 0
            processed_count = 0

            for img in images_to_process:
                if not self._vision_guard_allows(img, processed_count):
                    continue

                if not self._vision_quota_allows():
                    self.logger.warning("Vision quota reached mid-run - stopping vision analysis")
                    break

                processed_count += 1
                try:
                    with open(img['path'], 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode('utf-8')

                    prompt = (
                        "Analyze this technical diagram or image from a service manual.\n"
                        "Describe what you see in 2-3 sentences. Focus on:\n"
                        "- Type of component or diagram (e.g., circuit board, exploded view, flowchart)\n"
                        "- Key parts or elements visible\n"
                        "- Any labels or numbers you can read\n\n"
                        "Keep it concise and technical."
                    )

                    max_attempts = max(1, self.max_retries)
                    last_error = None
                    succeeded = False

                    for attempt in range(1, max_attempts + 1):
                        try:
                            self._record_vision_usage()
                            response = self.session.post(
                                f"{ollama_url}/api/generate",
                                json={
                                    "model": model_name,
                                    "prompt": prompt,
                                    "images": [image_data],
                                    "stream": False,
                                },
                                timeout=self.request_timeout,
                            )

                            if response.status_code == 200:
                                result = response.json()
                                description = result.get('response', '').strip()
                                img['ai_description'] = description
                                img['ai_confidence'] = 0.8
                                img['contains_text'] = any(
                                    keyword in description.lower()
                                    for keyword in ['label', 'text', 'number', 'code']
                                )
                                success_count += 1
                                self._reset_vision_failures()
                                metrics.record_vision_result(model_name, True)
                                desc_stats = text_stats(description)
                                self.logger.debug(
                                    "Vision analysis stats for %s: %s",
                                    img.get('filename'),
                                    desc_stats,
                                )
                                succeeded = True
                                break

                            last_error = f"status_{response.status_code}"
                            if response.status_code >= 500 and attempt < max_attempts:
                                delay = self.retry_base_delay * (2 ** (attempt - 1)) + random.uniform(0, self.retry_jitter)
                                self.logger.warning(
                                    "Vision API transient error %s on attempt %d/%d for %s - retrying in %.2fs",
                                    response.status_code,
                                    attempt,
                                    max_attempts,
                                    img['filename'],
                                    delay,
                                )
                                time.sleep(delay)
                                continue

                            if response.status_code >= 500:
                                self.logger.error(
                                    "Vision API persistent server error %s for %s after %d attempts",
                                    response.status_code,
                                    img['filename'],
                                    attempt,
                                )
                            else:
                                self.logger.warning(
                                    "Vision API returned HTTP %s for %s (attempt %d/%d) - not retrying",
                                    response.status_code,
                                    img['filename'],
                                    attempt,
                                    max_attempts,
                                )

                            self._record_vision_failure(last_error or "unexpected_status")
                            img['ai_description'] = ''
                            img['ai_confidence'] = 0.0
                            break

                        except (requests_exceptions.Timeout, requests_exceptions.ConnectionError) as exc:
                            last_error = str(exc)
                            if attempt < max_attempts:
                                delay = self.retry_base_delay * (2 ** (attempt - 1)) + random.uniform(0, self.retry_jitter)
                                self.logger.warning(
                                    "Vision request error on attempt %d/%d for %s: %s - retrying in %.2fs",
                                    attempt,
                                    max_attempts,
                                    img['filename'],
                                    exc,
                                    delay,
                                )
                                time.sleep(delay)
                                continue
                            self.logger.error(
                                "Vision request failed for %s after %d attempts due to connection issues: %s",
                                img['filename'],
                                attempt,
                                exc,
                            )
                            self._record_vision_failure("connection_error")
                            img['ai_description'] = ''
                            img['ai_confidence'] = 0.0
                            break
                        except Exception as exc:
                            last_error = str(exc)
                            self._record_vision_failure("exception")
                            img['ai_description'] = ''
                            img['ai_confidence'] = 0.0
                            self.logger.debug(
                                "Vision AI failed for %s: %s",
                                img.get('filename'),
                                exc,
                            )
                            break
                    else:  # pragma: no cover - defensive
                        self._record_vision_failure(last_error or "unknown")

                    if not succeeded:
                        metrics.record_vision_result(model_name, False, error_label=last_error or "failed")

                except Exception as exc:
                    self._record_vision_failure("read_error")
                    self.logger.debug("Vision preprocessing failed for %s: %s", img.get('filename'), exc)
                    img['ai_description'] = ''
                    img['ai_confidence'] = 0.0
                    metrics.record_vision_result(model_name, False, error_label="read_error")

                if self._vision_breaker_until and time.time() < self._vision_breaker_until:
                    self.logger.warning("Vision circuit breaker triggered mid-run - stopping analysis")
                    break

            self.logger.success(
                "✅ Vision AI analyzed %d/%d permitted images",
                success_count,
                processed_count,
            )

            return images

        except Exception as e:
            self.logger.error(f"Vision AI processing failed: {e}")
            return images
    
    def analyze_page(
        self,
        pdf_path: Path,
        page_number: int,
        prompt: str
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a specific PDF page with Vision AI
        
        Args:
            pdf_path: Path to PDF file
            page_number: Page number to analyze (0-indexed)
            prompt: Custom prompt for Vision AI
            
        Returns:
            Dict with analysis results or None if failed
        """
        try:
            if not self.vision_available:
                self.logger.warning("Vision AI not available")
                return None
            
            # Extract page as image
            doc = fitz.open(pdf_path)
            if page_number >= len(doc):
                self.logger.warning(f"Page {page_number} out of range (doc has {len(doc)} pages)")
                return None
            
            page = doc[page_number]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
            img_data = pix.tobytes("png")
            doc.close()
            
            # Analyze with Vision AI
            img_base64 = base64.b64encode(img_data).decode('utf-8')

            if self._vision_breaker_until and time.time() < self._vision_breaker_until:
                self.logger.warning("Vision circuit breaker open - analyze_page aborted")
                return None

            if not self._vision_quota_allows():
                self.logger.warning("Vision quota reached - analyze_page aborted")
                return None

            self._record_vision_usage()

            model_name = self._get_vision_model_name() or "llava:latest"
            response = self.session.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "images": [img_base64],
                    "stream": False
                },
                timeout=self.request_timeout
            )

            if response.status_code == 200:
                result_text = response.json().get('response', '')
                metrics.record_vision_result(model_name, True)
                
                # Try to parse as JSON
                try:
                    # Extract JSON from response (might have extra text)
                    import re
                    json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        return result
                    else:
                        return {"found": False, "raw_response": result_text}
                except json.JSONDecodeError:
                    return {"found": False, "raw_response": result_text}
            else:
                self.logger.warning(f"Vision API error: {response.status_code}")
                metrics.record_vision_result(model_name, False, error_label=f"status_{response.status_code}")
                return None
                
        except Exception as e:
            metrics.record_vision_result(model_name if 'model_name' in locals() else None, False, error_label=str(e))
            self.logger.error(f"analyze_page failed: {e}")
            return None


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
