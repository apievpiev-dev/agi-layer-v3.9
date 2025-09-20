@echo off
echo 🤖 AGI Layer v3.9 - Исправление и запуск
echo.

echo 📝 Шаг 1: Создание .env файла...
(
echo # AGI Layer v3.9 - Конфигурация
echo TELEGRAM_BOT_TOKEN=8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw
echo TELEGRAM_CHAT_ID=458589236
echo POSTGRES_DB=agi_layer
echo POSTGRES_USER=agi_user
echo POSTGRES_PASSWORD=agi_secure_pass_2024
echo POSTGRES_HOST=postgres
echo POSTGRES_PORT=5432
echo REDIS_URL=redis://redis:6379
echo API_HOST=0.0.0.0
echo API_PORT=8000
echo WEB_UI_PORT=8501
echo MODELS_PATH=/app/models
echo DOWNLOAD_MODELS=true
echo LOG_LEVEL=INFO
echo LOG_PATH=/app/logs
echo SECRET_KEY=agi_layer_secret_key_2024
echo ALLOWED_HOSTS=localhost,127.0.0.1
) > .env

echo ✅ .env файл создан!
echo.

echo 🐳 Шаг 2: Проверка Docker...
docker --version
docker-compose --version

echo.
echo 🔧 Шаг 3: Остановка старых контейнеров...
docker-compose down 2>nul

echo.
echo 🏗️ Шаг 4: Сборка образов...
docker-compose build --no-cache

echo.
echo 🚀 Шаг 5: Запуск системы...
docker-compose up -d

echo.
echo 📊 Шаг 6: Статус сервисов...
docker-compose ps

echo.
echo ✅ Система запущена!
echo 🌐 Web UI: http://localhost:8501
echo 📱 Telegram бот готов!
echo 📊 API: http://localhost:8000
echo.
echo 🔍 Для просмотра логов: docker-compose logs -f
echo.
pause
