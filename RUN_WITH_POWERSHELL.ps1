# AGI Layer v3.9 - PowerShell запуск
Write-Host "🤖 AGI Layer v3.9 - PowerShell запуск" -ForegroundColor Green
Write-Host ""

# Получаем текущую папку
$CurrentPath = Get-Location
Write-Host "📁 Текущая папка: $CurrentPath" -ForegroundColor Yellow

# Проверяем наличие файлов
if (Test-Path "docker-compose.yml") {
    Write-Host "✅ docker-compose.yml найден" -ForegroundColor Green
} else {
    Write-Host "❌ docker-compose.yml НЕ найден!" -ForegroundColor Red
    exit 1
}

if (Test-Path ".env") {
    Write-Host "✅ .env файл найден" -ForegroundColor Green
} else {
    Write-Host "❌ .env файл НЕ найден!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🐳 Остановка старых контейнеров..." -ForegroundColor Yellow
docker-compose down

Write-Host ""
Write-Host "🏗️ Сборка образов..." -ForegroundColor Yellow
docker-compose build

Write-Host ""
Write-Host "🚀 Запуск системы..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "📊 Статус сервисов:" -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "✅ Система запущена!" -ForegroundColor Green
Write-Host "🌐 Web UI: http://localhost:8501" -ForegroundColor Cyan
Write-Host "📱 Telegram бот готов!" -ForegroundColor Cyan
Write-Host "📊 API: http://localhost:8000" -ForegroundColor Cyan

Write-Host ""
Write-Host "🔍 Для просмотра логов: docker-compose logs -f" -ForegroundColor Yellow
Read-Host "Нажмите Enter для выхода"
