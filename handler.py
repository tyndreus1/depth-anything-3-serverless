"""
Depth Anything 3 - RunPod Serverless Handler (FINAL VERSION)
Manuel paket kurulumu - xformers sorunu yok
"""

import os
import sys
import subprocess
import time

def setup_environment():
    """Ortamı hazırla - Manuel paket kurulumu"""
    
    print("=" * 60)
    print("🚀 Depth Anything 3 Kurulum Başlıyor (Manuel)")
    print("=" * 60)
    
    try:
        # 1. RunPod SDK
        print("📦 RunPod SDK kuruluyor...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--no-cache-dir", "--quiet", "runpod"
        ])
        print("✅ RunPod SDK kuruldu")
        
        # 2. Temel paketler (zaten base image'da var ama güncelleyelim)
        print("📦 Temel paketler kontrol ediliyor...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--no-cache-dir", "--quiet",
            "torch>=2.0.0",
            "torchvision>=0.15.0", 
            "numpy>=1.24.0",
            "pillow>=9.5.0"
        ])
        print("✅ Temel paketler hazır")
        
        # 3. OpenCV (headless - GUI yok)
        print("📦 OpenCV kuruluyor...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "--no-cache-dir", "--quiet", 
            "opencv-python-headless>=4.7.0"
        ])
        print("✅ OpenCV kuruldu")
        
        # 4. Hugging Face Hub
        print("📦 Hugging Face Hub kuruluyor...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "--no-cache-dir", "--quiet",
            "huggingface-hub>=0.14.0"
        ])
        print("✅ Hugging Face Hub kuruldu")
        
        # 5. Depth-Anything-3 (xformers OLMADAN!)
        print("📦 Depth Anything 3 kuruluyor (xformers atlanıyor)...")
        
        # Git clone
        workspace = "/workspace"
        da3_dir = os.path.join(workspace, "Depth-Anything-3")
        
        if not os.path.exists(da3_dir):
            subprocess.check_call([
                "git", "clone", 
                "https://github.com/ByteDance-Seed/Depth-Anything-3.git",
                da3_dir
            ])
        
        # Setup.py'yi xformers olmadan çalıştır
        os.chdir(da3_dir)
        
        # Önce setup.py'deki xformers dependency'sini kaldır
        setup_py_path = os.path.join(da3_dir, "setup.py")
        if os.path.exists(setup_py_path):
            with open(setup_py_path, 'r') as f:
                setup_content = f.read()
            
            # xformers satırını kaldır
            setup_content = setup_content.replace(
                'git+https://github.com/facebookresearch/xformers.git@main#egg=xformers',
                ''
            )
            
            with open(setup_py_path, 'w') as f:
                f.write(setup_content)
        
        # Şimdi kur
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "--no-cache-dir", "-e", "."
        ])
        
        print("✅ Depth Anything 3 kuruldu")
        
        print("=" * 60)
        print("✅ KURULUM TAMAMLANDI!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Kurulum hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Kurulum yap
if not setup_environment():
    print("❌ Kurulum başarısız, çıkılıyor...")
    sys.exit(1)

# Şimdi handler'ı çalıştır
import runpod
import torch
import base64
import io
from PIL import Image
import numpy as np

# Depth Anything 3'ü import et
try:
    from depth_anything_3.api import DepthAnything3
except ImportError:
    print("❌ Depth Anything 3 import edilemedi!")
    sys.exit(1)

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
            return {"error": "❌ 'image' parametresi gerekli (base64 string)", "success": False}
        
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
