@echo off
echo ========================================
echo    Запуск веб-чата с Ollama
echo ========================================

echo.
echo Проверка Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Docker не установлен или не запущен!
    echo Установите Docker Desktop и запустите его.
    pause
    exit /b 1
)

echo.
echo Проверка Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Docker Compose не установлен!
    pause
    exit /b 1
)

echo.
echo Запуск веб-чата с Ollama...
docker-compose -f docker-compose-ollama-chat.yml up -d

if errorlevel 1 (
    echo.
    echo ОШИБКА: Не удалось запустить сервисы!
    echo Проверьте логи: docker-compose -f docker-compose-ollama-chat.yml logs
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Веб-чат с Ollama запущен!
echo ========================================
echo.
echo Доступные сервисы:
echo - Веб-чат: http://localhost:8501
echo - Ollama API: http://localhost:11434
echo.
echo Для загрузки модели используйте:
echo docker exec -it agi_ollama_chat ollama pull llama2
echo.
echo Для остановки сервисов:
echo docker-compose -f docker-compose-ollama-chat.yml down
echo.
pause