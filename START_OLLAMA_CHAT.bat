@echo off
echo ========================================
echo   AGI Layer - Запуск Ollama Chat
echo ========================================
echo.

echo [1/4] Проверка Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker не установлен!
    echo Скачайте Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo ✅ Docker найден

echo.
echo [2/4] Запуск Ollama и веб-чата...
docker-compose -f docker-compose-ollama.yml up -d

echo.
echo [3/4] Ожидание запуска сервисов...
timeout /t 10 /nobreak >nul

echo.
echo [4/4] Проверка статуса...
docker-compose -f docker-compose-ollama.yml ps

echo.
echo ========================================
echo   🌐 Веб-чат доступен по адресу:
echo   http://localhost:8502
echo.
echo   🤖 Для загрузки модели выполните:
echo   docker exec -it agi_ollama ollama pull llama2
echo.
echo   ⏹️  Для остановки выполните:
echo   docker-compose -f docker-compose-ollama.yml down
echo ========================================
echo.

echo Нажмите любую клавишу для открытия браузера...
pause >nul

start http://localhost:8502