"""
Depth Anything 3 - RunPod Serverless Handler
Bu dosya RunPod serverless endpoint'te çalışacak ana kod
"""

import runpod
import torch
import base64
import io
import time
from PIL import Image
import numpy as np
from depth_anything_3.api import DepthAnything3

# Global model - Sadece bir kez yüklenir (cold start'ta)
MODEL = None
DEVICE = None

def load_model():
    """Model'i yükle (sadece ilk çağrıda)"""
    global MODEL, DEVICE
    
    if MODEL is None:
        print("🚀 Model yükleniyor...")
        start_time = time.time()
        
        DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"📍 Device: {DEVICE}")
        
        # Model'i indir ve yükle
        MODEL = DepthAnything3.from_pretrained("depth-anything/DA3-LARGE")
        MODEL = MODEL.to(device=DEVICE)
        MODEL.eval()  # Inference mode
        
        elapsed = time.time() - start_time
        print(f"✅ Model yüklendi ({elapsed:.2f} saniye)")
    
    return MODEL


def image_to_base64(image_array):
    """NumPy array'i base64 string'e çevir"""
    # Normalize depth map (0-255 arası)
    depth_normalized = ((image_array - image_array.min()) / 
                       (image_array.max() - image_array.min()) * 255).astype(np.uint8)
    
    # PIL Image'e çevir
    depth_image = Image.fromarray(depth_normalized)
    
    # Base64'e encode et
    buffered = io.BytesIO()
    depth_image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return img_base64


def process_depth(job):
    """
    Ana işlem fonksiyonu
    RunPod bu fonksiyonu her istek için çağırır
    """
    try:
        job_input = job["input"]
        
        # Input validasyonu
        if "image" not in job_input:
            return {"error": "❌ 'image' parametresi gerekli (base64 string)"}
        
        print(f"📥 İşlem başlıyor - Job ID: {job['id']}")
        start_time = time.time()
        
        # Model'i yükle (ilk çağrıda)
        model = load_model()
        
        # Base64 imajı decode et
        image_data = base64.b64decode(job_input["image"])
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        
        print(f"📸 İmaj boyutu: {image.size}")
        
        # Depth map oluştur
        inference_start = time.time()
        
        with torch.no_grad():
            prediction = model.inference([image])
        
        inference_time = time.time() - inference_start
        
        # Sonucu base64'e çevir
        depth_map = prediction.depth[0]  # İlk imajın depth map'i
        depth_base64 = image_to_base64(depth_map)
        
        # Toplam süre
        total_time = time.time() - start_time
        
        print(f"✅ İşlem tamamlandı - İnference: {inference_time:.2f}s, Toplam: {total_time:.2f}s")
        
        # Sonucu döndür
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
        
        return {
            "error": str(e),
            "success": False
        }


# RunPod serverless başlangıç noktası
if __name__ == "__main__":
    print("🎯 Depth Anything 3 Serverless başlatılıyor...")
    runpod.serverless.start({"handler": process_depth})