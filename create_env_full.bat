@echo off
echo 📝 Создание .env файла с вашими настройками...
echo.

(
echo # AGI Layer v3.9 - Конфигурация
echo.
echo # Telegram настройки
echo TELEGRAM_BOT_TOKEN=8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw
echo TELEGRAM_CHAT_ID=458589236
echo.
echo # База данных
echo POSTGRES_DB=agi_layer
echo POSTGRES_USER=agi_user
echo POSTGRES_PASSWORD=agi_secure_pass_2024
echo POSTGRES_HOST=postgres
echo POSTGRES_PORT=5432
echo.
echo # Redis
echo REDIS_URL=redis://redis:6379
echo.
echo # API настройки
echo API_HOST=0.0.0.0
echo API_PORT=8000
echo.
echo # Web UI
echo WEB_UI_PORT=8501
echo.
echo # Модели
echo MODELS_PATH=/app/models
echo DOWNLOAD_MODELS=true
echo.
echo # Логирование
echo LOG_LEVEL=INFO
echo LOG_PATH=/app/logs
echo.
echo # Безопасность
echo SECRET_KEY=agi_layer_secret_key_2024
echo ALLOWED_HOSTS=localhost,127.0.0.1
) > .env

echo ✅ .env файл создан с вашими настройками!
echo.
pause
