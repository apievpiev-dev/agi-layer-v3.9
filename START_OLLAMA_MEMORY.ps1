# AGI Layer - Ollama Chat с Памятью
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AGI Layer - Ollama Chat с Памятью" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка Docker
Write-Host "[1/5] Проверка Docker..." -ForegroundColor Yellow
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
Write-Host "[2/5] Запуск PostgreSQL, ChromaDB и Ollama..." -ForegroundColor Yellow
docker-compose -f docker-compose-ollama-memory.yml up -d

Write-Host ""
Write-Host "[3/5] Ожидание запуска сервисов..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "[4/5] Проверка статуса..." -ForegroundColor Yellow
docker-compose -f docker-compose-ollama-memory.yml ps

Write-Host ""
Write-Host "[5/5] Проверка подключений..." -ForegroundColor Yellow
$pgResult = docker exec agi_postgres_memory pg_isready -U agi_user -d agi_layer 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PostgreSQL готов" -ForegroundColor Green
} else {
    Write-Host "⚠️  PostgreSQL еще запускается..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   🧠 Чат с памятью доступен по адресу:" -ForegroundColor Green
Write-Host "   http://localhost:8503" -ForegroundColor White
Write-Host ""
Write-Host "   🎯 Возможности:" -ForegroundColor Yellow
Write-Host "   - Сохранение истории чатов" -ForegroundColor White
Write-Host "   - Поиск по памяти" -ForegroundColor White
Write-Host "   - Контекстные ответы" -ForegroundColor White
Write-Host ""
Write-Host "   🤖 Для загрузки модели выполните:" -ForegroundColor Yellow
Write-Host "   docker exec -it agi_ollama_memory ollama pull llama2" -ForegroundColor White
Write-Host ""
Write-Host "   ⏹️  Для остановки выполните:" -ForegroundColor Yellow
Write-Host "   docker-compose -f docker-compose-ollama-memory.yml down" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Нажмите Enter для открытия браузера"

# Открытие браузера
Start-Process "http://localhost:8503"