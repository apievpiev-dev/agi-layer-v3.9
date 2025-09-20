@echo off
title AGI Layer v3.9 - Запуск системы
color 0A

echo.
echo  @@@@@@   @@@@@@@  @@@       @@@        @@@@@@@  @@@ @@@  @@@@@@@ @@@@@@@  
echo @@@@@@@@  @@@@@@@@  @@@       @@@       @@@@@@@@  @@@ @@@  @@@@@@@ @@@@@@@@  
echo @@!  @@@  @@!  @@@  @@!       @@!       @@!  @@@  @@! !@@  @@!     @@!  @@@ 
echo !@!  @!@  !@!  @!@  !@!       !@!       !@!  @!@  !@! @!!  !@!     !@!  @!@ 
echo @!@!@!@!  @!@  !@!  @!!       @!!       @!@!@!@!   !@!@!   @!!!:!  @!@!!@!  
echo !!!@!!!!  !@!  !!!  !!!       !!!       !!!@!!!!    @!!!   !!!!!:  !!@!@!   
echo !!:  !!!  !!:  !!!  !!:       !!:       !!:  !!!    !!:    !!:     !!: :!!  
echo :!:  !:!  :!:  !:!   :!:       :!:       :!:  !:!    :!:    :!:     :!:  !:! 
echo ::   :::   :::: ::   :: ::::   :: ::::  ::   :::     ::     :: ::::  ::   ::: 
echo  :   : :  :: :  :   : :: : :  : :: : :   :   : :     :      : :: ::    :   : : 
echo.
echo                           v3.9 - CPU-Only Headless AGI Infrastructure
echo                                   https://github.com/agi-layer
echo.
echo ===================================================================================
echo.

REM Проверка файла .env
if not exist ".env" (
    echo ❌ Файл .env не найден!
    echo 📝 Создаем .env из примера...
    copy env.example .env
    echo.
    echo ⚠️  ВАЖНО: Настройте Telegram бота в файле .env
    echo    Откройте .env и замените:
    echo    TELEGRAM_TOKEN=ВАШ_ТОКЕН_ЗДЕСЬ
    echo    TELEGRAM_CHAT_ID=ВАШ_CHAT_ID_ЗДЕСЬ
    echo.
    echo 📖 Инструкция: TELEGRAM_SETUP.md
    pause
)

REM Проверка Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker не найден!
    echo 📥 Установите Docker Desktop: https://www.docker.com/products/docker-desktop/
    echo.
    echo 🔧 Альтернатива - запуск без Docker:
    echo    install-without-docker.bat
    pause
    exit /b 1
)

echo ✅ Docker найден
echo.

REM Создание необходимых папок
echo 📁 Создание папок...
if not exist "logs" mkdir logs
if not exist "models" mkdir models
if not exist "output" mkdir output
if not exist "output\images" mkdir output\images
echo ✅ Папки созданы
echo.

REM Проверка образов Docker
echo 🐳 Проверка Docker образов...
docker images | findstr agi-layer >nul
if errorlevel 1 (
    echo 📦 Сборка Docker образов...
    docker-compose build
    if errorlevel 1 (
        echo ❌ Ошибка сборки образов
        pause
        exit /b 1
    )
)

echo ✅ Docker образы готовы
echo.

REM Запуск системы
echo 🚀 Запуск AGI Layer v3.9...
echo.
echo Запускаются сервисы:
echo   - PostgreSQL (База данных)
echo   - ChromaDB (Векторная память)  
echo   - Redis (Кэш и очереди)
echo   - MetaAgent (Координатор)
echo   - TelegramAgent (Telegram бот)
echo   - ImageAgent (Генерация изображений)
echo   - TextAgent (Обработка текста)
echo   - VisionAgent (Анализ изображений)
echo   - OCRAgent (Распознавание текста)
echo   - EmbeddingAgent (Векторизация)
echo   - RecoveryAgent (Восстановление)
echo   - WebUI (Веб интерфейс)
echo   - Watchdog (Мониторинг)
echo.

docker-compose up -d

if errorlevel 1 (
    echo ❌ Ошибка запуска системы
    echo 🔍 Проверьте логи: docker-compose logs
    pause
    exit /b 1
)

echo.
echo ✅ Система AGI Layer v3.9 запущена!
echo.
echo 🌐 Интерфейсы:
echo   Web UI:      http://localhost:8501
echo   PostgreSQL:  localhost:5432
echo   ChromaDB:    http://localhost:8000
echo   Redis:       localhost:6379
echo.
echo 🤖 Telegram бот активен (если настроен)
echo.
echo 📊 Команды управления:
echo   Статус:      docker-compose ps
echo   Логи:        docker-compose logs -f
echo   Остановка:   docker-compose down
echo   Перезапуск:  docker-compose restart
echo.
echo 🎯 Откройте Web UI в браузере: http://localhost:8501
echo.

REM Ожидание запуска
echo ⏳ Ожидание запуска всех сервисов (30 сек)...
timeout /t 30 /nobreak >nul

REM Проверка статуса
echo 📋 Статус контейнеров:
docker-compose ps

echo.
echo 🎉 AGI Layer v3.9 готов к работе!
echo.
pause

