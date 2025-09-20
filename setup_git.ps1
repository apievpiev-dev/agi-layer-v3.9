# Setup Git for AGI Layer v3.9
Write-Host "🚀 Настройка Git репозитория для AGI Layer v3.9..." -ForegroundColor Green

try {
    # Проверка Git
    $gitVersion = git --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Git найден: $gitVersion" -ForegroundColor Green
        
        # Инициализация репозитория
        if (!(Test-Path ".git")) {
            git init
            Write-Host "✅ Git репозиторий инициализирован" -ForegroundColor Green
        } else {
            Write-Host "ℹ️ Git репозиторий уже существует" -ForegroundColor Yellow
        }
        
        # Добавление файлов
        git add .
        git commit -m "Initial commit: AGI Layer v3.9 - CPU-only headless AGI infrastructure"
        
        Write-Host "✅ Файлы добавлены в Git" -ForegroundColor Green
        Write-Host "📍 Папка проекта: $PWD" -ForegroundColor Cyan
        
    } else {
        Write-Host "❌ Git не найден. Установите Git для Windows" -ForegroundColor Red
        Write-Host "🔗 Скачайте с: https://git-scm.com/download/win" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Ошибка: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "✨ Готово!" -ForegroundColor Green
