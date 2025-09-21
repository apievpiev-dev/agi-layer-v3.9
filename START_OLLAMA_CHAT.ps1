# AGI Layer - Запуск Ollama Chat
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AGI Layer - Запуск Ollama Chat" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка Docker
Write-Host "[1/4] Проверка Docker..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "✅ Docker найден" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не установлен!" -ForegroundColor Red
    Write-Host "Скачайте Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host ""
Write-Host "[2/4] Запуск Ollama и веб-чата..." -ForegroundColor Yellow
docker-compose -f docker-compose-ollama.yml up -d

Write-Host ""
Write-Host "[3/4] Ожидание запуска сервисов..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "[4/4] Проверка статуса..." -ForegroundColor Yellow
docker-compose -f docker-compose-ollama.yml ps

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   🌐 Веб-чат доступен по адресу:" -ForegroundColor Green
Write-Host "   http://localhost:8502" -ForegroundColor White
Write-Host ""
Write-Host "   🤖 Для загрузки модели выполните:" -ForegroundColor Yellow
Write-Host "   docker exec -it agi_ollama ollama pull llama2" -ForegroundColor White
Write-Host ""
Write-Host "   ⏹️  Для остановки выполните:" -ForegroundColor Yellow
Write-Host "   docker-compose -f docker-compose-ollama.yml down" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Нажмите Enter для открытия браузера"

# Открытие браузера
Start-Process "http://localhost:8502"