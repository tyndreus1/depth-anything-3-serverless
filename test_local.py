"""
Lokal Test Scripti
RunPod'a deploy etmeden önce lokal olarak test edin
"""

import requests
import base64
import json
from PIL import Image
import io

# Test edilecek imaj
TEST_IMAGE_PATH = "test_image.jpg"  # Kendi test imajınızın yolunu yazın

# RunPod endpoint (deploy'dan sonra buraya yapıştırın)
RUNPOD_ENDPOINT = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync"
RUNPOD_API_KEY = "YOUR_RUNPOD_API_KEY"  # RunPod dashboard'dan aldığınız key


def image_to_base64(image_path):
    """İmajı base64'e çevir"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


def test_local_handler():
    """Handler'ı lokal olarak test et (RunPod olmadan)"""
    print("🧪 Lokal test başlıyor...")
    
    # Handler'ı import et
    import handler
    
    # Test imajını yükle
    image_base64 = image_to_base64(TEST_IMAGE_PATH)
    
    # Test job'u oluştur
    test_job = {
        "id": "test-job-123",
        "input": {
            "image": image_base64
        }
    }
    
    # İşle
    result = handler.process_depth(test_job)
    
    print("📊 Sonuç:")
    print(json.dumps(result, indent=2))
    
    # Sonucu kaydet
    if result.get("success"):
        depth_data = base64.b64decode(result["depth_map"])
        depth_image = Image.open(io.BytesIO(depth_data))
        depth_image.save("test_depth_output.png")
        print("✅ Depth map kaydedildi: test_depth_output.png")


def test_runpod_endpoint():
    """RunPod endpoint'i test et"""
    print("🌐 RunPod endpoint test başlıyor...")
    
    if "YOUR_" in RUNPOD_ENDPOINT or "YOUR_" in RUNPOD_API_KEY:
        print("❌ Lütfen RUNPOD_ENDPOINT ve RUNPOD_API_KEY değerlerini güncelleyin!")
        return
    
    # Test imajını yükle
    image_base64 = image_to_base64(TEST_IMAGE_PATH)
    
    # Request payload
    payload = {
        "input": {
            "image": image_base64
        }
    }
    
    # Headers
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    print(f"📤 İstek gönderiliyor: {RUNPOD_ENDPOINT}")
    
    # Request gönder
    response = requests.post(
        RUNPOD_ENDPOINT,
        json=payload,
        headers=headers,
        timeout=300  # 5 dakika timeout
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ İstek başarılı!")
        print(json.dumps(result, indent=2))
        
        # Depth map'i kaydet
        if "output" in result and result["output"].get("success"):
            depth_data = base64.b64decode(result["output"]["depth_map"])
            depth_image = Image.open(io.BytesIO(depth_data))
            depth_image.save("runpod_depth_output.png")
            print("✅ Depth map kaydedildi: runpod_depth_output.png")
    else:
        print(f"❌ Hata: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    print("=" * 50)
    print("🎯 Depth Anything 3 Test Scripti")
    print("=" * 50)
    
    print("\n1. Lokal test (handler.py'yi test et)")
    print("2. RunPod endpoint test (deploy'dan sonra)")
    print("3. Çıkış")
    
    choice = input("\nSeçim (1-3): ")
    
    if choice == "1":
        test_local_handler()
    elif choice == "2":
        test_runpod_endpoint()
    elif choice == "3":
        print("👋 Çıkılıyor...")
    else:
        print("❌ Geçersiz seçim!")