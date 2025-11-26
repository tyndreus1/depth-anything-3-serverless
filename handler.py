"""
Depth Anything 3 - RunPod Serverless Handler (Self-Contained)
Bu handler kendi başına çalışır - GitHub clone ve package install yapar
"""

import os
import sys
import subprocess
import time

def setup_environment():
    """Ortamı hazırla: Git clone + pip install"""
    
    print("=" * 60)
    print("🚀 Depth Anything 3 Kurulum Başlıyor...")
    print("=" * 60)
    
    # Workspace dizini
    workspace = "/workspace"
    repo_dir = os.path.join(workspace, "depth-anything-repo")
    
    # 1. Git clone (eğer yoksa)
    if not os.path.exists(repo_dir):
        print("📦 GitHub repository clone ediliyor...")
        try:
            subprocess.check_call([
                "git", "clone",
                "https://github.com/tyndreus1/depth-anything-3-serverless.git",
                repo_dir
            ])
            print("✅ Clone tamamlandı!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Git clone başarısız: {e}")
            return False
    else:
        print("✅ Repository zaten mevcut")
    
    # 2. Requirements.txt'i kur
    requirements_path = os.path.join(repo_dir, "requirements.txt")
    if os.path.exists(requirements_path):
        print("📦 Python paketleri kuruluyor...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "--no-cache-dir", "--ignore-installed",
                "-r", requirements_path
            ])
            print("✅ Paketler kuruldu!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Pip install başarısız: {e}")
            return False
    
    # 3. RunPod SDK'yı kur
    print("📦 RunPod SDK kuruluyor...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "--no-cache-dir", "--ignore-installed", "runpod"
        ])
        print("✅ RunPod SDK kuruldu!")
    except subprocess.CalledProcessError as e:
        print(f"❌ RunPod install başarısız: {e}")
        return False
    
    print("=" * 60)
    print("✅ Kurulum tamamlandı!")
    print("=" * 60)
    
    return True

# Kurulum yap
if not setup_environment():
    print("❌ Kurulum başarısız, çıkılıyor...")
    sys.exit(1)

# Şimdi gerçek handler'ı import et ve çalıştır
import runpod
import torch
import base64
import io
from PIL import Image
import numpy as np
from depth_anything_3.api import DepthAnything3

# Global değişkenler
MODEL = None
DEVICE = None

def load_model():
    """Model'i yükle"""
    global MODEL, DEVICE
    
    if MODEL is None:
        print("🚀 Model yükleniyor...")
        start_time = time.time()
        
        DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"📍 Device: {DEVICE}")
        
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

# RunPod başlat
if __name__ == "__main__":
    print("🎯 Depth Anything 3 Serverless başlatılıyor...")
    runpod.serverless.start({"handler": process_depth})
