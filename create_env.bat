@echo off
echo Creating .env file for AGI Layer v3.9...

echo # AGI Layer v3.9 - Configuration > .env
echo PROJECT_NAME=AGI Layer v3.9 >> .env
echo VERSION=3.9.0 >> .env
echo DEBUG=false >> .env
echo. >> .env
echo # Database PostgreSQL >> .env
echo POSTGRES_HOST=postgres >> .env
echo POSTGRES_PORT=5432 >> .env
echo POSTGRES_DB=agi_layer >> .env
echo POSTGRES_USER=agi_user >> .env
echo POSTGRES_PASSWORD=agi_password >> .env
echo. >> .env
echo # ChromaDB >> .env
echo CHROMA_HOST=chromadb >> .env
echo CHROMA_PORT=8000 >> .env
echo CHROMA_COLLECTION=agi_memory >> .env
echo. >> .env
echo # Redis >> .env
echo REDIS_HOST=redis >> .env
echo REDIS_PORT=6379 >> .env
echo REDIS_PASSWORD= >> .env
echo. >> .env
echo # Telegram Bot >> .env
echo TELEGRAM_TOKEN=8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw >> .env
echo TELEGRAM_CHAT_ID=458589236 >> .env
echo. >> .env
echo # Web UI >> .env
echo WEB_UI_HOST=0.0.0.0 >> .env
echo WEB_UI_PORT=8501 >> .env
echo. >> .env
echo # Models >> .env
echo MODELS_PATH=/app/models >> .env
echo DOWNLOAD_MODELS_ON_START=true >> .env
echo. >> .env
echo # Logging >> .env
echo LOG_LEVEL=INFO >> .env
echo LOG_PATH=/app/logs >> .env
echo. >> .env
echo # Security >> .env
echo SECRET_KEY=agi-layer-v39-secure-key-2024 >> .env
echo ALLOWED_HOSTS=* >> .env
echo. >> .env
echo # Agents >> .env
echo AGENT_LOOP_INTERVAL=1.0 >> .env
echo AGENT_TIMEOUT=300 >> .env
echo MAX_CONCURRENT_TASKS=10 >> .env

echo.
echo .env file created successfully!
echo.
echo Next steps:
echo 1. Install Docker Desktop
echo 2. Run: docker-compose up -d
echo 3. Test bot with /start command
echo.
pause

