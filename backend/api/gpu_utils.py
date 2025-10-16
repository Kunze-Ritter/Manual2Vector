"""
GPU Utilities for KRAI
======================
Automatic GPU/CPU detection and configuration for OpenCV and ML models.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GPUManager:
    """Manage GPU/CPU usage based on environment variables"""
    
    def __init__(self):
        self.use_gpu = os.getenv("USE_GPU", "false").lower() == "true"
        self.cuda_device = os.getenv("CUDA_VISIBLE_DEVICES", "0")
        self._gpu_available = None
        self._opencv_cuda_available = None
        
        logger.info(f"GPU Manager initialized: USE_GPU={self.use_gpu}")
    
    def is_gpu_available(self) -> bool:
        """Check if GPU is available for general use"""
        if self._gpu_available is not None:
            return self._gpu_available
        
        if not self.use_gpu:
            self._gpu_available = False
            logger.info("GPU disabled via USE_GPU=false")
            return False
        
        # Try to detect CUDA
        try:
            import torch
            self._gpu_available = torch.cuda.is_available()
            if self._gpu_available:
                logger.info(f"CUDA GPU detected: {torch.cuda.get_device_name(0)}")
            else:
                logger.warning("CUDA not available, falling back to CPU")
        except ImportError:
            logger.warning("PyTorch not installed, cannot detect CUDA")
            self._gpu_available = False
        
        return self._gpu_available
    
    def is_opencv_cuda_available(self) -> bool:
        """Check if OpenCV was built with CUDA support"""
        if self._opencv_cuda_available is not None:
            return self._opencv_cuda_available
        
        if not self.use_gpu:
            self._opencv_cuda_available = False
            return False
        
        try:
            import cv2
            self._opencv_cuda_available = cv2.cuda.getCudaEnabledDeviceCount() > 0
            if self._opencv_cuda_available:
                logger.info(f"OpenCV CUDA available: {cv2.cuda.getCudaEnabledDeviceCount()} devices")
            else:
                logger.warning("OpenCV not built with CUDA support")
        except Exception as e:
            logger.warning(f"OpenCV CUDA check failed: {e}")
            self._opencv_cuda_available = False
        
        return self._opencv_cuda_available
    
    def get_device(self) -> str:
        """Get device string for ML frameworks (cuda or cpu)"""
        return "cuda" if self.is_gpu_available() else "cpu"
    
    def get_opencv_backend(self) -> str:
        """Get OpenCV backend (CUDA or CPU)"""
        return "cuda" if self.is_opencv_cuda_available() else "cpu"
    
    def configure_opencv(self):
        """Configure OpenCV for optimal performance"""
        try:
            import cv2
            
            if self.is_opencv_cuda_available():
                logger.info("Configuring OpenCV for CUDA")
                cv2.cuda.setDevice(int(self.cuda_device))
            else:
                logger.info("Configuring OpenCV for CPU")
                # Optimize CPU performance
                cv2.setNumThreads(os.cpu_count() or 4)
        except Exception as e:
            logger.error(f"Failed to configure OpenCV: {e}")
    
    def get_info(self) -> dict:
        """Get GPU/CPU configuration info"""
        info = {
            "use_gpu": self.use_gpu,
            "gpu_available": self.is_gpu_available(),
            "opencv_cuda_available": self.is_opencv_cuda_available(),
            "device": self.get_device(),
            "opencv_backend": self.get_opencv_backend()
        }
        
        if self.is_gpu_available():
            try:
                import torch
                info["cuda_device"] = self.cuda_device
                info["cuda_device_name"] = torch.cuda.get_device_name(0)
                info["cuda_version"] = torch.version.cuda
            except:
                pass
        
        return info


# Global GPU manager instance
_gpu_manager: Optional[GPUManager] = None


def get_gpu_manager() -> GPUManager:
    """Get or create GPU manager singleton"""
    global _gpu_manager
    if _gpu_manager is None:
        _gpu_manager = GPUManager()
        _gpu_manager.configure_opencv()
    return _gpu_manager


def is_gpu_enabled() -> bool:
    """Quick check if GPU is enabled and available"""
    return get_gpu_manager().is_gpu_available()


def get_device() -> str:
    """Get device string (cuda or cpu)"""
    return get_gpu_manager().get_device()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    manager = get_gpu_manager()
    info = manager.get_info()
    
    print("\n" + "="*60)
    print("GPU/CPU Configuration")
    print("="*60)
    for key, value in info.items():
        print(f"{key:25s}: {value}")
    print("="*60)
