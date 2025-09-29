#!/usr/bin/env python3
"""
Hardware Detection Test
Test der automatischen Hardware-Erkennung und Modell-Auswahl
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.ai_config import AIConfigManager, get_ai_config, get_ollama_models, get_model_requirements

def test_hardware_detection():
    """Test hardware detection and model selection"""
    print("🔍 KR-AI-Engine Hardware Detection Test")
    print("=" * 50)
    
    # Initialize AI Config Manager
    ai_manager = AIConfigManager()
    
    # Get configuration
    config = get_ai_config()
    models = get_ollama_models()
    requirements = get_model_requirements()
    
    print(f"\n📊 Hardware Analysis:")
    print(f"   Total RAM: {requirements['hardware_specs']['total_ram_gb']:.1f} GB")
    print(f"   CPU Cores: {requirements['hardware_specs']['cpu_cores']}")
    print(f"   GPU Available: {requirements['hardware_specs']['gpu_available']}")
    
    print(f"\n🤖 Selected Model Configuration:")
    print(f"   Tier: {config.tier.value}")
    print(f"   Text Classification: {config.text_classification}")
    print(f"   Embeddings: {config.embeddings}")
    print(f"   Vision: {config.vision}")
    print(f"   Estimated RAM Usage: {config.estimated_ram_usage_gb} GB")
    print(f"   Parallel Processing: {config.parallel_processing}")
    
    print(f"\n📋 Ollama Models to Download:")
    for task, model in models.items():
        print(f"   {task}: {model}")
    
    print(f"\n✅ Hardware Detection Complete!")
    print(f"   Recommended for your system: {config.tier.value.upper()} tier")
    
    return config, models, requirements

if __name__ == "__main__":
    test_hardware_detection()
