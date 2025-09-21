@echo off
echo ========================================
echo   AGI Layer v3.9 - Telegram Chat
echo ========================================
echo.

REM Проверка наличия .env файла
if not exist .env (
    echo [ERROR] Файл .env не найден!
    echo Скопируйте env.example в .env и настройте параметры.
    echo.
    copy env.example .env
    echo Файл .env создан. Отредактируйте его и запустите скрипт снова.
    pause
    exit /b 1
)

echo [INFO] Проверка Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker не установлен или недоступен!
    echo Установите Docker Desktop и запустите его.
    pause
    exit /b 1
)

echo [INFO] Проверка Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose не найден!
    pause
    exit /b 1
)

echo [INFO] Остановка существующих контейнеров...
docker-compose down

echo [INFO] Запуск системы AGI с Telegram Chat...
echo.
echo Запускаются сервисы:
echo - PostgreSQL (база данных)
echo - ChromaDB (векторная память) 
echo - Redis (кэш)
echo - MetaAgent (координатор)
echo - TextAgent (нейросеть Phi-2)
echo - VisionAgent (анализ изображений)
echo - ImageAgent (генерация изображений)
echo - TelegramChatAgent (чат-бот)
echo.

docker-compose up -d postgres chromadb redis
echo [INFO] Ожидание запуска баз данных...
timeout /t 10 /nobreak >nul

docker-compose up -d meta_agent
echo [INFO] Ожидание запуска MetaAgent...
timeout /t 5 /nobreak >nul

docker-compose up -d text_agent vision_agent image_agent
echo [INFO] Ожидание запуска AI агентов...
timeout /t 15 /nobreak >nul

docker-compose up -d telegram_chat_agent
echo [INFO] Запуск Telegram Chat Agent...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   СИСТЕМА ЗАПУЩЕНА!
echo ========================================
echo.
echo 🤖 Telegram Chat Bot готов к работе!
echo.
echo 📱 Найдите вашего бота в Telegram и отправьте /start
echo.
echo 🌐 Доступные интерфейсы:
echo   - ChromaDB: http://localhost:8000
echo   - PostgreSQL: localhost:5432
echo.
echo 📊 Проверка статуса:
echo   docker-compose ps
echo.
echo 📋 Просмотр логов:
echo   docker-compose logs -f telegram_chat_agent
echo.
echo 🛑 Остановка системы:
echo   docker-compose down
echo.

REM Показать статус сервисов
echo [INFO] Статус сервисов:
docker-compose ps

echo.
echo Нажмите любую клавишу для просмотра логов чат-бота...
pause >nul

echo.
echo ========================================
echo   ЛОГИ TELEGRAM CHAT AGENT
echo ========================================
echo Нажмите Ctrl+C для выхода из просмотра логов
echo.

docker-compose logs -f telegram_chat_agent