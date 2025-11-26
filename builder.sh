#!/bin/bash

# Depth Anything 3 - RunPod Serverless Builder
# Bu script Docker image'ı build edip RunPod'a deploy eder

set -e  # Hata olursa dur

echo "🚀 Depth Anything 3 Build Başlıyor..."

# Renkli output için
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Docker Hub kullanıcı adını al
read -p "Docker Hub kullanıcı adınız (örn: alpress): " DOCKER_USER

if [ -z "$DOCKER_USER" ]; then
    echo -e "${RED}❌ Docker Hub kullanıcı adı gerekli!${NC}"
    exit 1
fi

# Image adı
IMAGE_NAME="$DOCKER_USER/depth-anything-3-serverless"
VERSION="v1.0"

echo -e "${YELLOW}📦 Docker image build ediliyor...${NC}"
echo "Image: $IMAGE_NAME:$VERSION"

# Docker build
docker build -t $IMAGE_NAME:$VERSION .
docker tag $IMAGE_NAME:$VERSION $IMAGE_NAME:latest

echo -e "${GREEN}✅ Build tamamlandı!${NC}"

# Docker Hub'a push et
read -p "Docker Hub'a push edilsin mi? (y/n): " PUSH_CONFIRM

if [ "$PUSH_CONFIRM" = "y" ]; then
    echo -e "${YELLOW}📤 Docker Hub'a push ediliyor...${NC}"
    
    # Login (gerekirse)
    docker login
    
    # Push
    docker push $IMAGE_NAME:$VERSION
    docker push $IMAGE_NAME:latest
    
    echo -e "${GREEN}✅ Push tamamlandı!${NC}"
    echo ""
    echo -e "${GREEN}🎉 RunPod'da kullanmak için image adı:${NC}"
    echo -e "${YELLOW}$IMAGE_NAME:latest${NC}"
else
    echo -e "${YELLOW}⏭️  Push atlandı${NC}"
fi

echo ""
echo -e "${GREEN}✅ Tüm işlemler tamamlandı!${NC}"