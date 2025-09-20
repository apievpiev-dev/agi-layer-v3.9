@echo off
echo 🔧 Исправление проблем Docker по рекомендации Gordon AI
echo.

echo 1️⃣ Очистка кэша Docker...
docker system prune -a --volumes -f

echo.
echo 2️⃣ Загрузка образов вручную...
docker pull postgres:15-alpine
docker pull redis:7-alpine  
docker pull chromadb/chroma:latest

echo.
echo 3️⃣ Запуск с отключенным BuildKit...
set DOCKER_BUILDKIT=0
docker-compose build

echo.
echo 4️⃣ Запуск системы...
docker-compose up -d

echo.
echo ✅ Готово! Проверьте статус:
docker-compose ps

pause
