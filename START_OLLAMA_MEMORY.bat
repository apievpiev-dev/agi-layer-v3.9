@echo off
echo ========================================
echo   AGI Layer - Ollama Chat с Памятью
echo ========================================
echo.

echo [1/5] Проверка Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker не установлен!
    echo Скачайте Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo ✅ Docker найден

echo.
echo [2/5] Запуск PostgreSQL, ChromaDB и Ollama...
docker-compose -f docker-compose-ollama-memory.yml up -d

echo.
echo [3/5] Ожидание запуска сервисов...
timeout /t 15 /nobreak >nul

echo.
echo [4/5] Проверка статуса...
docker-compose -f docker-compose-ollama-memory.yml ps

echo.
echo [5/5] Проверка подключений...
docker exec agi_postgres_memory pg_isready -U agi_user -d agi_layer >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ PostgreSQL готов
) else (
    echo ⚠️  PostgreSQL еще запускается...
)

echo.
echo ========================================
echo   🧠 Чат с памятью доступен по адресу:
echo   http://localhost:8503
echo.
echo   🎯 Возможности:
echo   - Сохранение истории чатов
echo   - Поиск по памяти
echo   - Контекстные ответы
echo.
echo   🤖 Для загрузки модели выполните:
echo   docker exec -it agi_ollama_memory ollama pull llama2
echo.
echo   ⏹️  Для остановки выполните:
echo   docker-compose -f docker-compose-ollama-memory.yml down
echo ========================================
echo.

echo Нажмите любую клавишу для открытия браузера...
pause >nul

start http://localhost:8503