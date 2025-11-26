"""
Depth Anything 3 - RunPod Handler (Template Deployment)
Bu dosyayı GitHub'a yükleyip RunPod'dan direkt kullanacağız - Docker build'e gerek yok!
"""

import runpod
import torch
import base64
import io
import time
from PIL import Image
import numpy as np

# Model import
try:
    from depth_anything_3.api import DepthAnything3
    DEPTH_ANYTHING_AVAILABLE = True
except ImportError:
    print("⚠️ Depth Anything 3 henüz yüklenmedi, ilk çalıştırmada yüklenecek...")
    DEPTH_ANYTHING_AVAILABLE = False

# Global değişkenler
MODEL = None
DEVICE = None

def install_dependencies():
    """Gerekli paketleri yükle"""
    import subprocess
    import sys
    
    print("📦 Bağımlılıklar yükleniyor...")
    
    packages = [
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "pillow>=9.0.0",
        "numpy>=1.24.0",
        "opencv-python-headless>=4.8.0",
        "timm>=0.9.0",
        "transformers>=4.30.0",
        "huggingface_hub>=0.16.0",
        "einops>=0.7.0",
        "git+https://github.com/ByteDance-Seed/Depth-Anything-3.git"
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])
            print(f"✓ {package.split('>=')[0]} yüklendi")
        except:
            print(f"✗ {package} yüklenemedi, devam ediliyor...")

def load_model():
    """Model'i yükle"""
    global MODEL, DEVICE, DEPTH_ANYTHING_AVAILABLE
    
    if MODEL is None:
        print("🚀 Model yükleniyor...")
        start_time = time.time()
        
        # Eğer depth_anything_3 yüklü değilse, önce yükle
        if not DEPTH_ANYTHING_AVAILABLE:
            install_dependencies()
            from depth_anything_3.api import DepthAnything3
        
        DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"📍 Device: {DEVICE}")
        
        # Model'i indir ve yükle
        MODEL = DepthAnything3.from_pretrained("depth-anything/DA3-LARGE")
        MODEL = MODEL.to(device=DEVICE)
        MODEL.eval()
        
        elapsed = time.time() - start_time
        print(f"✅ Model yüklendi ({elapsed:.2f} saniye)")
    
    return MODEL

def image_to_base64(image_array):
    """NumPy array'i base64'e çevir"""
    depth_normalized = ((image_array - image_array.min()) / 
                       (image_array.max() - image_array.min()) * 255).astype(np.uint8)
    depth_image = Image.fromarray(depth_normalized)
    
    buffered = io.BytesIO()
    depth_image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def process_depth(job):
    """Ana işlem fonksiyonu"""
    try:
        job_input = job["input"]
        
        if "image" not in job_input:
            return {"error": "❌ 'image' parametresi gerekli (base64 string)"}
        
        print(f"📥 İşlem başlıyor - Job ID: {job['id']}")
        start_time = time.time()
        
        # Model yükle
        model = load_model()
        
        # İmajı decode et
        image_data = base64.b64decode(job_input["image"])
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        print(f"📸 İmaj boyutu: {image.size}")
        
        # Depth map oluştur
        inference_start = time.time()
        with torch.no_grad():
            prediction = model.inference([image])
        inference_time = time.time() - inference_start
        
        # Sonucu hazırla
        depth_map = prediction.depth[0]
        depth_base64 = image_to_base64(depth_map)
        
        total_time = time.time() - start_time
        print(f"✅ Tamamlandı - İnference: {inference_time:.2f}s, Toplam: {total_time:.2f}s")
        
        return {
            "depth_map": depth_base64,
            "original_size": list(image.size),
            "depth_shape": list(depth_map.shape),
            "inference_time": round(inference_time, 2),
            "total_time": round(total_time, 2),
            "success": True
        }
        
    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "success": False}

# RunPod başlangıç
if __name__ == "__main__":
    print("🎯 Depth Anything 3 Serverless başlatılıyor...")
    runpod.serverless.start({"handler": process_depth})
