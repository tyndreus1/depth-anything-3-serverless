# Depth Anything 3 - Windows PowerShell Builder
# Bu script Docker image'ı build edip Docker Hub'a push eder

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Depth Anything 3 - Windows Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Docker'ın çalışıp çalışmadığını kontrol et
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "✓ Docker bulundu" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker bulunamadı!" -ForegroundColor Red
    Write-Host "Lütfen Docker Desktop'ı kurun ve çalıştırın." -ForegroundColor Red
    Write-Host "https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    pause
    exit
}

# Docker daemon çalışıyor mu?
try {
    docker ps | Out-Null
    Write-Host "✓ Docker çalışıyor" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker çalışmıyor!" -ForegroundColor Red
    Write-Host "Lütfen Docker Desktop'ı başlatın." -ForegroundColor Red
    pause
    exit
}

Write-Host ""

# Docker Hub kullanıcı adı
$DOCKER_USER = Read-Host "Docker Hub kullanıcı adınız (örn: alpress)"

if ([string]::IsNullOrWhiteSpace($DOCKER_USER)) {
    Write-Host "✗ Docker Hub kullanıcı adı gerekli!" -ForegroundColor Red
    pause
    exit
}

# Image bilgileri
$IMAGE_NAME = "$DOCKER_USER/depth-anything-3-serverless"
$VERSION = "v1.0"

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Build başlıyor..." -ForegroundColor Yellow
Write-Host "Image: $IMAGE_NAME`:$VERSION" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Docker build
Write-Host "1/4 - Docker image build ediliyor..." -ForegroundColor Yellow
docker build -t ${IMAGE_NAME}:${VERSION} .

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Build başarısız!" -ForegroundColor Red
    pause
    exit
}

Write-Host "✓ Build tamamlandı!" -ForegroundColor Green
Write-Host ""

# Tag latest
Write-Host "2/4 - Latest tag ekleniyor..." -ForegroundColor Yellow
docker tag ${IMAGE_NAME}:${VERSION} ${IMAGE_NAME}:latest
Write-Host "✓ Tag eklendi!" -ForegroundColor Green
Write-Host ""

# Push onayı
Write-Host "3/4 - Docker Hub'a push edilsin mi?" -ForegroundColor Yellow
$PUSH_CONFIRM = Read-Host "(y/n)"

if ($PUSH_CONFIRM -eq "y") {
    Write-Host ""
    Write-Host "Docker Hub'a giriş yapılıyor..." -ForegroundColor Yellow
    docker login
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Giriş başarılı!" -ForegroundColor Green
        Write-Host ""
        
        Write-Host "4/4 - Push ediliyor..." -ForegroundColor Yellow
        docker push ${IMAGE_NAME}:${VERSION}
        docker push ${IMAGE_NAME}:latest
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Push tamamlandı!" -ForegroundColor Green
            Write-Host ""
            Write-Host "======================================" -ForegroundColor Green
            Write-Host "  İŞLEM BAŞARILI!" -ForegroundColor Green
            Write-Host "======================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "RunPod'da kullanmak için image adı:" -ForegroundColor Cyan
            Write-Host "$IMAGE_NAME`:latest" -ForegroundColor Yellow
            Write-Host ""
        } else {
            Write-Host "✗ Push başarısız!" -ForegroundColor Red
        }
    } else {
        Write-Host "✗ Docker Hub girişi başarısız!" -ForegroundColor Red
    }
} else {
    Write-Host "⊘ Push atlandı" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Devam etmek için bir tuşa basın..." -ForegroundColor Gray
pause
