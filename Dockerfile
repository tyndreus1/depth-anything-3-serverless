# RunPod PyTorch base image kullan
FROM runpod/pytorch:2.1.1-py3.10-cuda12.1.1-devel-ubuntu22.04

# Çalışma dizini
WORKDIR /app

# Sistem paketlerini güncelle
RUN apt-get update && apt-get install -y \
    git \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python requirements'ı kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# RunPod SDK'yı yükle
RUN pip install --no-cache-dir runpod

# Handler'ı kopyala
COPY handler.py .

# Model'i önceden indir (opsiyonel - cold start'ı azaltır)
RUN python -c "from depth_anything_3.api import DepthAnything3; \
               print('Model indiriliyor...'); \
               DepthAnything3.from_pretrained('depth-anything/DA3-LARGE'); \
               print('Model indirildi!')"

# Handler'ı çalıştır
CMD ["python", "-u", "handler.py"]