# CUDA GPU Setup für KRAI Engine

## 🚀 Voraussetzungen

### 1. NVIDIA Container Toolkit
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### 2. NVIDIA-Treiber (Windows/Linux)
- **Windows**: NVIDIA GeForce Experience oder NVIDIA Driver Downloads
- **Linux**: `nvidia-driver-535` oder neuer
- Überprüfen mit `nvidia-smi`

## 🐳 CUDA Deployment

### 1. GPU-fähigen Container bauen
```bash
# CUDA-fähigen KRAI Engine bauen
docker-compose -f docker-compose.cuda.yml build krai-engine

# Oder manuell
docker build -f Dockerfile.cuda -t krai-engine:cuda .
```

### 2. GPU-Container starten
```bash
# Vollständigen CUDA-Stack starten
docker-compose -f docker-compose.cuda.yml up -d

# Nur KRAI Engine mit GPU
docker-compose -f docker-compose.cuda.yml up -d krai-engine krai-ollama
```

### 3. GPU-Status überprüfen
```bash
# GPU-Status im Container prüfen
docker exec krai-engine-cuda nvidia-smi

# PyTorch CUDA-Test
docker exec krai-engine-cuda python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}')"
```

## 📊 Performance-Vorteile

### Ohne GPU (aktuell)
- **Tier**: Conservative
- **Models**: llama3.2:3b (CPU-only)
- **Performance**: Langsamer, CPU-beschränkt
- **Memory**: 7.8 GB RAM genutzt

### Mit CUDA
- **Tier**: High Performance
- **Models**: llama3.2:3b, llava:7b (GPU-beschleunigt)
- **Performance**: 10-50x schneller für AI-Inference
- **Memory**: GPU RAM + 7.8 GB System-RAM

## 🔧 Konfiguration

### Umgebungsvariablen
```bash
# .env Datei ergänzen
GPU_ENABLED=true
CUDA_VISIBLE_DEVICES=0
TORCH_CUDA_ARCH_LIST="8.6;8.9;9.0"  # Passend zur GPU
```

### Model-Optimierung
```bash
# Größere Models mit GPU
docker exec krai-ollama-cuda ollama pull llama3.2:7b
docker exec krai-ollama-cuda ollama pull llava:7b
docker exec krai-ollama-cuda ollama pull nomic-embed-text:latest
```

## 🐛 Fehlerbehebung

### 1. "No GPU detected"
```bash
# NVIDIA-Treiber prüfen
nvidia-smi

# Docker GPU-Support prüfen
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
```

### 2. CUDA-Laufzeitfehler
```bash
# CUDA-Version prüfen
docker exec krai-engine-cuda nvcc --version

# PyTorch CUDA-Installation prüfen
docker exec krai-engine-cuda python -c "import torch; print(torch.version.cuda)"
```

### 3. Memory-Probleme
```bash
# GPU-Memory überwachen
watch -n 1 nvidia-smi

# Container-Limits anpassen
docker-compose -f docker-compose.cuda.yml down
# docker-compose.cuda.yml editieren
docker-compose -f docker-compose.cuda.yml up -d
```

## 📈 Monitoring

### GPU-Monitoring
```bash
# Live GPU-Status
docker exec krai-engine-cuda nvidia-smi -l 1

# GPU-Auslastung in Logs
docker logs krai-engine-cuda | grep -i gpu
```

### Performance-Test
```bash
# AI-Inference Benchmark
curl -X POST http://localhost:8000/health
# Antwortzeit sollte mit GPU deutlich schneller sein
```

## 🔄 Wechsel zwischen CPU/GPU

### Zu GPU wechseln
```bash
# Stoppen
docker-compose down

# GPU-Start
docker-compose -f docker-compose.cuda.yml up -d
```

### Zu CPU zurückkehren
```bash
# Stoppen
docker-compose -f docker-compose.cuda.yml down

# CPU-Start
docker-compose up -d
```

## 🎯 Empfohlene Models mit GPU

```bash
# Große Language Models
docker exec krai-ollama-cuda ollama pull llama3.2:7b
docker exec krai-ollama-cuda ollama pull llama3.2:13b

# Vision Models
docker exec krai-ollama-cuda ollama pull llava:7b
docker exec krai-ollama-cuda ollama pull llava:13b

# Embedding Models
docker exec krai-ollama-cuda ollama pull nomic-embed-text:latest
docker exec krai-ollama-cuda ollama pull mxbai-embed-large
```

## ⚡ Erwartete Performance-Verbesserung

| Task | CPU-only | With GPU | Verbesserung |
|------|----------|----------|-------------|
| Text Generation | 10-30 sec | 0.5-2 sec | 15-60x |
| Image Analysis | 60-120 sec | 2-5 sec | 20-60x |
| Embeddings | 5-15 sec | 0.2-1 sec | 5-75x |
| Document Processing | 30-60 sec | 2-8 sec | 4-30x |

## 🔒 Sicherheitshinweise

- GPU-Container benötigen elevated privileges
- NVIDIA-Treiber müssen aktuell sein
- GPU-Memory sollte überwacht werden
- Nur vertrauenswürdige Code auf GPU ausführen
