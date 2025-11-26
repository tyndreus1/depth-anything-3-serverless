#!/bin/bash
# Depth Anything 3 - RunPod Start Script

echo "🚀 Downloading and starting handler..."

# Handler'ı indir ve çalıştır
curl -fsSL https://raw.githubusercontent.com/tyndreus1/depth-anything-3-serverless/main/handler.py | python -u
