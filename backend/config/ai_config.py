"""
AI Model Configuration with Hardware Auto-Detection
Intelligente Modell-Auswahl basierend auf verfügbarer Hardware
"""

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
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            # Fallback: Check nvidia-smi
            try:
                import subprocess
                result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
                return result.returncode == 0
            except:
                return False
    
    def _get_gpu_memory(self) -> Optional[float]:
        """Get GPU memory in GB"""
        try:
            import torch
            if torch.cuda.is_available():
                return torch.cuda.get_device_properties(0).total_memory / (1024**3)
        except:
            pass
        
        # Fallback: Parse nvidia-smi output
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                memory_mb = int(result.stdout.strip())
                return memory_mb / 1024  # Convert MB to GB
        except:
            pass
        return None
    
    def _get_gpu_name(self) -> Optional[str]:
        """Get GPU name"""
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
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
        
        configs = {
            ModelTier.CONSERVATIVE: ModelConfig(
                text_classification="llama3.2:7b",
                embeddings="embeddinggemma:2b", 
                vision="llava:7b",
                tier=ModelTier.CONSERVATIVE,
                estimated_ram_usage_gb=8.0,
                parallel_processing=True,
                gpu_acceleration=gpu_available,
                estimated_gpu_usage_gb=4.0 if gpu_available else 0.0
            ),
            ModelTier.BALANCED: ModelConfig(
                text_classification="llama3.2:13b",
                embeddings="embeddinggemma:2b",
                vision="llava:13b", 
                tier=ModelTier.BALANCED,
                estimated_ram_usage_gb=16.0,
                parallel_processing=True,
                gpu_acceleration=gpu_available,
                estimated_gpu_usage_gb=6.0 if gpu_available else 0.0
            ),
                   ModelTier.HIGH_PERFORMANCE: ModelConfig(
                       text_classification="llama3.2:latest",
                       embeddings="embeddinggemma:latest",
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
        
        print(f"🔍 Hardware Detection:")
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
        'llama3.2:13b': {
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
        'embeddinggemma:2b': {
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
        'llava:13b': {
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
