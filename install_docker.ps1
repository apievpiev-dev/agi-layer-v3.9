# Установка Docker для Windows
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    УСТАНОВКА DOCKER ДЛЯ WINDOWS" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка Docker
Write-Host "Проверяем Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "✅ Docker уже установлен: $dockerVersion" -ForegroundColor Green
        
        # Проверка Docker Desktop
        $dockerProcess = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
        if ($dockerProcess) {
            Write-Host "✅ Docker Desktop запущен" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Docker Desktop не запущен" -ForegroundColor Yellow
            Write-Host "Запускаем Docker Desktop..." -ForegroundColor Yellow
            
            $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
            if (Test-Path $dockerPath) {
                Start-Process $dockerPath
                Write-Host "Подождите 30 секунд для запуска..." -ForegroundColor Yellow
                Start-Sleep -Seconds 30
            } else {
                Write-Host "❌ Docker Desktop не найден в стандартном пути" -ForegroundColor Red
            }
        }
        
        # Тест Docker
        Write-Host ""
        Write-Host "Тестируем Docker..." -ForegroundColor Yellow
        docker run --rm hello-world
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker работает корректно!" -ForegroundColor Green
        } else {
            Write-Host "❌ Проблема с Docker" -ForegroundColor Red
        }
        
        exit 0
    }
} catch {
    Write-Host "❌ Docker не установлен" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    ИНСТРУКЦИЯ ПО УСТАНОВКЕ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Скачайте Docker Desktop:" -ForegroundColor White
Write-Host "   https://www.docker.com/products/docker-desktop/" -ForegroundColor Blue
Write-Host ""

Write-Host "2. Или через winget:" -ForegroundColor White
Write-Host "   winget install Docker.DockerDesktop" -ForegroundColor Blue
Write-Host ""

Write-Host "3. После установки перезагрузите компьютер" -ForegroundColor White
Write-Host ""

Write-Host "4. Запустите Docker Desktop" -ForegroundColor White
Write-Host ""

# Проверка WSL2
Write-Host "Проверяем WSL2..." -ForegroundColor Yellow
try {
    wsl --status 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ WSL2 доступен" -ForegroundColor Green
    } else {
        Write-Host "⚠️  WSL2 не установлен" -ForegroundColor Yellow
        Write-Host "Устанавливаем WSL2..." -ForegroundColor Yellow
        wsl --install
    }
} catch {
    Write-Host "⚠️  Проблема с WSL2" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    АВТОМАТИЧЕСКАЯ УСТАНОВКА" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$choice = Read-Host "Попробовать автоматическую установку через winget? (y/n)"
if ($choice -eq "y" -or $choice -eq "Y") {
    Write-Host "Устанавливаем Docker через winget..." -ForegroundColor Yellow
    winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker установлен успешно!" -ForegroundColor Green
        Write-Host "Перезагрузите компьютер и запустите Docker Desktop" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Ошибка установки через winget" -ForegroundColor Red
        Write-Host "Скачайте вручную с официального сайта" -ForegroundColor Yellow
    }
} else {
    Write-Host "Скачайте Docker вручную с https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    ГОТОВО!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "После установки запустите AGI Layer v3.9:" -ForegroundColor White
Write-Host "docker-compose up -d" -ForegroundColor Blue
Write-Host ""
Read-Host "Нажмите Enter для выхода"

