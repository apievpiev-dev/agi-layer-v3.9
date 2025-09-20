@echo off
echo ========================================
echo    AGI Layer v3.9 - System Startup
echo ========================================
echo.

echo Checking Docker installation...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed!
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo Docker found! Checking Docker Compose...
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Compose is not installed!
    pause
    exit /b 1
)

echo Docker Compose found!
echo.

echo Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "models" mkdir models
if not exist "output" mkdir output
if not exist "output\images" mkdir output\images
if not exist "data" mkdir data
if not exist "data\chroma" mkdir data\chroma
if not exist "backups" mkdir backups

echo.
echo Building Docker images...
docker-compose build

if %errorlevel% neq 0 (
    echo ERROR: Failed to build Docker images!
    pause
    exit /b 1
)

echo.
echo Starting AGI Layer v3.9 system...
docker-compose up -d

if %errorlevel% neq 0 (
    echo ERROR: Failed to start system!
    pause
    exit /b 1
)

echo.
echo ========================================
echo    SYSTEM STARTED SUCCESSFULLY!
echo ========================================
echo.
echo Services running:
echo - PostgreSQL: localhost:5432
echo - ChromaDB: localhost:8000
echo - Redis: localhost:6379
echo - Web UI: http://localhost:8501
echo - MetaAgent API: http://localhost:8001
echo.
echo Telegram Bot: @atlas_wb_bot
echo Chat ID: 458589236
echo.
echo Test commands:
echo /start - Start system
echo /status - System status
echo /generate beautiful landscape - Generate image
echo /report - System report
echo.
echo To stop system: docker-compose down
echo To view logs: docker-compose logs -f
echo.
echo ========================================
pause

