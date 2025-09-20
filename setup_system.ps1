# AGI Layer v3.9 - Системная диагностика и настройка
# Запуск: powershell -ExecutionPolicy Bypass -File setup_system.ps1

Write-Host "🚀 AGI Layer v3.9 - Диагностика системы" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Gray

# 1. Создание .env файла
Write-Host "📝 Создание .env файла..." -ForegroundColor Yellow
try {
    if (!(Test-Path ".env")) {
        Copy-Item "env.example" ".env"
        Write-Host "✅ .env файл создан" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ .env файл уже существует" -ForegroundColor Blue
    }
} catch {
    Write-Host "❌ Ошибка создания .env: $($_.Exception.Message)" -ForegroundColor Red
}

# 2. Проверка Git
Write-Host "🔍 Проверка Git..." -ForegroundColor Yellow
try {
    $gitVersion = git --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Git установлен: $gitVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Git не найден" -ForegroundColor Red
        Write-Host "📥 Скачайте Git: https://git-scm.com/download/win" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Git не установлен" -ForegroundColor Red
    Write-Host "📥 Скачайте Git: https://git-scm.com/download/win" -ForegroundColor Cyan
}

# 3. Проверка Docker
Write-Host "🐳 Проверка Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker установлен: $dockerVersion" -ForegroundColor Green
        
        # Проверка Docker Compose
        $composeVersion = docker-compose --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker Compose: $composeVersion" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Docker Compose не найден" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Docker не найден" -ForegroundColor Red
        Write-Host "📥 Скачайте Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Docker не установлен" -ForegroundColor Red
    Write-Host "📥 Скачайте Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Cyan
}

# 4. Проверка Python
Write-Host "🐍 Проверка Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python установлен: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "❌ Python не найден" -ForegroundColor Red
        Write-Host "📥 Скачайте Python: https://www.python.org/downloads/" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Python не установлен" -ForegroundColor Red
}

# 5. Создание необходимых папок
Write-Host "📁 Создание папок..." -ForegroundColor Yellow
$folders = @("logs", "models", "output", "output/images", "templates")
foreach ($folder in $folders) {
    if (!(Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        Write-Host "✅ Создана папка: $folder" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ Папка существует: $folder" -ForegroundColor Blue
    }
}

# 6. Проверка файлов проекта
Write-Host "📋 Проверка файлов проекта..." -ForegroundColor Yellow
$requiredFiles = @(
    "main.py",
    "docker-compose.yml", 
    "Dockerfile",
    "requirements.txt",
    ".env"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ $file отсутствует!" -ForegroundColor Red
    }
}

# 7. Информация о системе
Write-Host "💻 Информация о системе:" -ForegroundColor Yellow
Write-Host "OS: $env:OS" -ForegroundColor Cyan
Write-Host "Процессор: $env:PROCESSOR_IDENTIFIER" -ForegroundColor Cyan
Write-Host "Архитектура: $env:PROCESSOR_ARCHITECTURE" -ForegroundColor Cyan
Write-Host "Пользователь: $env:USERNAME" -ForegroundColor Cyan
Write-Host "Папка проекта: $PWD" -ForegroundColor Cyan

Write-Host ""
Write-Host "🎯 Следующие шаги:" -ForegroundColor Green
Write-Host "1. Установите недостающие компоненты (Git, Docker, Python)" -ForegroundColor White
Write-Host "2. Настройте Telegram бота в файле .env" -ForegroundColor White
Write-Host "3. Запустите: docker-compose up -d" -ForegroundColor White
Write-Host "4. Проверьте Web UI: http://localhost:8501" -ForegroundColor White

Write-Host ""
Write-Host "✨ Диагностика завершена!" -ForegroundColor Green
