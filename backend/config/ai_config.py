"""
AI Model Configuration with Hardware Auto-Detection
Intelligente Modell-Auswahl basierend auf verfügbarer Hardware
"""

import os
import psutil
import platform
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ModelTier(Enum):
    """Model Performance Tiers"""
    CONSERVATIVE = "conservative"  # 7B Models
    BALANCED = "balanced"          # 13B Models  
    HIGH_PERFORMANCE = "high_performance"  # 70B Models

@dataclass
class HardwareSpecs:
    """Hardware specifications"""
    total_ram_gb: float
    available_ram_gb: float
    cpu_cores: int
    cpu_threads: int
    cpu_frequency_mhz: float
    gpu_available: bool
    gpu_memory_gb: Optional[float] = None
    gpu_name: Optional[str] = None
    gpu_driver_version: Optional[str] = None

@dataclass
class ModelConfig:
    """AI Model configuration"""
    text_classification: str
    embeddings: str
    vision: str
    tier: ModelTier
    estimated_ram_usage_gb: float
    parallel_processing: bool
    gpu_acceleration: bool = True
    estimated_gpu_usage_gb: float = 0.0

class HardwareDetector:
    """Hardware detection and model recommendation"""
    
    def __init__(self):
        self.specs = self._detect_hardware()
    
    def _detect_hardware(self) -> HardwareSpecs:
        """Detect system hardware specifications"""
        # RAM Detection
        total_ram_bytes = psutil.virtual_memory().total
        available_ram_bytes = psutil.virtual_memory().available
        total_ram_gb = total_ram_bytes / (1024**3)
        available_ram_gb = available_ram_bytes / (1024**3)
        
        # CPU Detection
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)
        cpu_frequency = psutil.cpu_freq()
        cpu_frequency_mhz = cpu_frequency.max if cpu_frequency else 0
        
        # GPU Detection (enhanced)
        gpu_available = self._detect_gpu()
        gpu_memory_gb = self._get_gpu_memory() if gpu_available else None
        gpu_name = self._get_gpu_name() if gpu_available else None
        gpu_driver_version = self._get_gpu_driver_version() if gpu_available else None
        
        return HardwareSpecs(
            total_ram_gb=total_ram_gb,
            available_ram_gb=available_ram_gb,
            cpu_cores=cpu_cores,
            cpu_threads=cpu_threads,
            cpu_frequency_mhz=cpu_frequency_mhz,
            gpu_available=gpu_available,
            gpu_memory_gb=gpu_memory_gb,
            gpu_name=gpu_name,
            gpu_driver_version=gpu_driver_version
        )
    
    def _detect_gpu(self) -> bool:
        """Detect if GPU is available"""
        gpu_found = False
        
        # Method 1: Check CUDA (NVIDIA)
        try:
            import torch
            if torch.cuda.is_available():
                print(f"   [OK] CUDA GPU detected: {torch.cuda.get_device_name(0)}")
                gpu_found = True
        except ImportError:
            pass
        
        # Method 2: Check nvidia-smi (NVIDIA)
        if not gpu_found:
            try:
                import subprocess
                result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"   [OK] NVIDIA GPU detected via nvidia-smi")
                    gpu_found = True
            except:
                pass
        
        # Method 3: Check Intel GPU (Windows)
        if not gpu_found:
            try:
                import subprocess
                result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and 'Intel' in result.stdout:
                    print(f"   [OK] Intel GPU detected via wmic")
                    gpu_found = True
            except:
                pass
        
        # Method 4: Check AMD GPU (Windows)
        if not gpu_found:
            try:
                import subprocess
                result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and any(keyword in result.stdout for keyword in ['AMD', 'Radeon']):
                    print(f"   [OK] AMD GPU detected via wmic")
                    gpu_found = True
            except:
                pass
        
        # Method 5: Generic GPU detection (Windows)
        if not gpu_found:
            try:
                import subprocess
                result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    gpu_lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and line.strip() != 'Name']
                    if gpu_lines:
                        print(f"   [OK] GPU detected via wmic: {gpu_lines[0]}")
                        gpu_found = True
            except:
                pass
        
        if not gpu_found:
            print(f"   [NO] No GPU detected")
        
        return gpu_found
    
    def _get_gpu_memory(self) -> Optional[float]:
        """Get GPU memory in GB"""
        # Method 1: CUDA
        try:
            import torch
            if torch.cuda.is_available():
                memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                print(f"   [MEM] GPU Memory: {memory_gb:.1f} GB (CUDA)")
                return memory_gb
        except:
            pass
        
        # Method 2: nvidia-smi
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                memory_mb = int(result.stdout.strip())
                memory_gb = memory_mb / 1024
                print(f"   [MEM] GPU Memory: {memory_gb:.1f} GB (nvidia-smi)")
                return memory_gb
        except:
            pass
        
        # Method 3: wmic (Windows) - estimate based on GPU name
        try:
            import subprocess
            result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name,AdapterRAM'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                for line in lines:
                    if 'Name' not in line and 'Intel' in line:
                        print(f"   [MEM] GPU Memory: ~2.0 GB (Intel GPU estimate)")
                        return 2.0
                    elif 'Name' not in line and any(keyword in line for keyword in ['AMD', 'Radeon']):
                        print(f"   [MEM] GPU Memory: ~4.0 GB (AMD GPU estimate)")
                        return 4.0
        except:
            pass
        
        print(f"   [MEM] GPU Memory: Unknown")
        return None
    
    def _get_gpu_name(self) -> Optional[str]:
        """Get GPU name"""
        # Method 1: CUDA
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                print(f"   [GPU] GPU Name: {gpu_name} (CUDA)")
                return gpu_name
        except:
            pass
        
        # Method 2: nvidia-smi
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                gpu_name = result.stdout.strip()
                print(f"   [GPU] GPU Name: {gpu_name} (nvidia-smi)")
                return gpu_name
        except:
            pass
        
        # Method 3: wmic (Windows)
        try:
            import subprocess
            result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and line.strip() != 'Name']
                if lines:
                    gpu_name = lines[0]
                    print(f"   [GPU] GPU Name: {gpu_name} (wmic)")
                    return gpu_name
        except:
            pass
        
        print(f"   [GPU] GPU Name: Unknown")
        return None
    
    def _get_gpu_driver_version(self) -> Optional[str]:
        """Get GPU driver version"""
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def recommend_model_tier(self) -> ModelTier:
        """Recommend model tier based on hardware"""
        ram_gb = self.specs.total_ram_gb
        cores = self.specs.cpu_cores
        gpu_available = self.specs.gpu_available
        gpu_memory_gb = self.specs.gpu_memory_gb or 0
        
        # High Performance: 32+ GB RAM, 8+ cores, OR 8+ GB GPU VRAM
        if (ram_gb >= 32 and cores >= 8) or (gpu_available and gpu_memory_gb >= 8):
            return ModelTier.HIGH_PERFORMANCE
        
        # Balanced: 16-32 GB RAM, 4+ cores, OR 4+ GB GPU VRAM
        elif (ram_gb >= 16 and cores >= 4) or (gpu_available and gpu_memory_gb >= 4):
            return ModelTier.BALANCED
        
        # Conservative: <16 GB RAM or <4 cores, OR <4 GB GPU VRAM
        else:
            return ModelTier.CONSERVATIVE
    
    def get_model_config(self, tier: Optional[ModelTier] = None) -> ModelConfig:
        """Get model configuration for specified tier"""
        if tier is None:
            tier = self.recommend_model_tier()
        
        # GPU-optimized configurations
        gpu_available = self.specs.gpu_available
        gpu_memory_gb = self.specs.gpu_memory_gb or 0
        
        # Read embedding model from env
        embedding_model = os.getenv('OLLAMA_MODEL_EMBEDDING', 'nomic-embed-text:latest')
        
        configs = {
            ModelTier.CONSERVATIVE: ModelConfig(
                text_classification="llama3.2:3b",
                embeddings=embedding_model, 
                vision="llava:7b",
                tier=ModelTier.CONSERVATIVE,
                estimated_ram_usage_gb=8.0,
                parallel_processing=True,
                gpu_acceleration=gpu_available,
                estimated_gpu_usage_gb=4.0 if gpu_available else 0.0
            ),
            ModelTier.BALANCED: ModelConfig(
                text_classification="llama3.2:latest",
                embeddings=embedding_model,
                vision="llava:latest", 
                tier=ModelTier.BALANCED,
                estimated_ram_usage_gb=16.0,
                parallel_processing=True,
                gpu_acceleration=gpu_available,
                estimated_gpu_usage_gb=6.0 if gpu_available else 0.0
            ),
                   ModelTier.HIGH_PERFORMANCE: ModelConfig(
                       text_classification="llama3.2:latest",
                       embeddings=embedding_model,
                       vision="llava:latest",
                       tier=ModelTier.HIGH_PERFORMANCE,
                       estimated_ram_usage_gb=16.0,
                       parallel_processing=True,
                       gpu_acceleration=gpu_available,
                       estimated_gpu_usage_gb=6.0 if gpu_available else 0.0
                   )
        }
        
        return configs[tier]

class AIConfigManager:
    """AI Configuration Manager with auto-detection"""
    
    def __init__(self):
        self.detector = HardwareDetector()
        self.config = None
        self._load_config()
    
    def _load_config(self):
        """Load AI configuration based on hardware detection"""
        tier = self.detector.recommend_model_tier()
        self.config = self.detector.get_model_config(tier)
        
        print(f"Hardware Detection:")
        print(f"   RAM: {self.detector.specs.total_ram_gb:.1f} GB")
        print(f"   CPU: {self.detector.specs.cpu_cores} cores, {self.detector.specs.cpu_threads} threads")
        if self.detector.specs.gpu_available:
            print(f"   GPU: {self.detector.specs.gpu_name} ({self.detector.specs.gpu_memory_gb:.1f} GB VRAM)")
            print(f"   GPU Driver: {self.detector.specs.gpu_driver_version}")
        else:
            print(f"   GPU: Not Available")
        print(f"   Recommended Tier: {tier.value}")
        print(f"   GPU Acceleration: {'Enabled' if self.config.gpu_acceleration else 'Disabled'}")
        print(f"   Selected Models: {self.config.text_classification}, {self.config.embeddings}, {self.config.vision}")
    
    def get_config(self) -> ModelConfig:
        """Get current model configuration"""
        return self.config
    
    def get_ollama_models(self) -> Dict[str, str]:
        """Get Ollama model names for different tasks"""
        return {
            'text_classification': self.config.text_classification,
            'embeddings': self.config.embeddings,
            'vision': self.config.vision
        }
    
    def get_model_requirements(self) -> Dict[str, any]:
        """Get model requirements for resource management"""
        return {
            'estimated_ram_gb': self.config.estimated_ram_usage_gb,
            'parallel_processing': self.config.parallel_processing,
            'tier': self.config.tier.value,
            'hardware_specs': {
                'total_ram_gb': self.detector.specs.total_ram_gb,
                'cpu_cores': self.detector.specs.cpu_cores,
                'gpu_available': self.detector.specs.gpu_available
            }
        }

# Global AI Configuration
ai_config = AIConfigManager()

# Export for easy access
def get_ai_config() -> ModelConfig:
    """Get current AI configuration"""
    return ai_config.get_config()

def get_ollama_models() -> Dict[str, str]:
    """Get Ollama model names"""
    return ai_config.get_ollama_models()

def get_model_requirements() -> Dict[str, any]:
    """Get model requirements"""
    return ai_config.get_model_requirements()

# Model-specific configurations
OLLAMA_MODELS = {
    'text_classification': {
        'llama3.2:7b': {
            'ram_usage_gb': 4.0,
            'context_length': 8192,
            'languages': ['en', 'de'],
            'specialization': 'general'
        },
        'llama3.2:latest': {
            'ram_usage_gb': 8.0,
            'context_length': 8192,
            'languages': ['en', 'de'],
            'specialization': 'general'
        },
        'llama3.2:70b': {
            'ram_usage_gb': 40.0,
            'context_length': 8192,
            'languages': ['en', 'de'],
            'specialization': 'general'
        }
    },
    'embeddings': {
        'embeddinggemma:latest': {
            'ram_usage_gb': 2.0,
            'embedding_dimensions': 768,
            'languages': ['en', 'de'],
            'specialization': 'multilingual'
        }
    },
    'vision': {
        'llava:7b': {
            'ram_usage_gb': 4.0,
            'image_resolution': '336x336',
            'languages': ['en', 'de'],
            'specialization': 'general_vision'
        },
        'llava:latest': {
            'ram_usage_gb': 8.0,
            'image_resolution': '336x336',
            'languages': ['en', 'de'],
            'specialization': 'general_vision'
        },
        'llava:34b': {
            'ram_usage_gb': 20.0,
            'image_resolution': '336x336',
            'languages': ['en', 'de'],
            'specialization': 'general_vision'
        }
    }
}

# Task-specific model assignments
TASK_MODELS = {
    'document_classification': 'text_classification',
    'manufacturer_detection': 'text_classification',
    'model_extraction': 'text_classification',
    'features_extraction': 'text_classification',
    'error_code_extraction': 'text_classification',
    'version_extraction': 'text_classification',
    'text_chunking': 'text_classification',
    'semantic_search': 'embeddings',
    'image_ocr': 'vision',
    'image_classification': 'vision',
    'defect_detection': 'vision'
}
