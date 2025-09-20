@echo off
echo 🚀 AGI Layer v3.9 - Полный запуск системы
echo.

echo 🔧 Шаг 1: Исправление WSL...
wsl --update
wsl --shutdown
timeout /t 3 /nobreak >nul

echo.
echo 🐳 Шаг 2: Запуск Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
echo Ожидание запуска Docker Desktop...
timeout /t 10 /nobreak >nul

echo.
echo 📦 Шаг 3: Сборка образов...
docker-compose build

echo.
echo 🚀 Шаг 4: Запуск всех сервисов...
docker-compose up -d

echo.
echo 📊 Шаг 5: Проверка статуса...
docker-compose ps

echo.
echo ✅ Система запущена!
echo 🌐 Web UI: http://localhost:8501
echo 📱 Telegram бот готов к работе
echo 📊 Мониторинг: http://localhost:8000
echo.
pause
