@echo off
echo 🔧 AGI Layer v3.9 - Быстрое исправление
echo.

echo 📁 Проверка текущей папки...
cd /d "%~dp0"
echo Текущая папка: %CD%

echo.
echo 📝 Проверка docker-compose.yml...
if exist docker-compose.yml (
    echo ✅ docker-compose.yml найден
) else (
    echo ❌ docker-compose.yml НЕ найден!
    echo Создаю базовый файл...
    goto :create_basic
)

echo.
echo 🐳 Запуск с полным путем...
docker-compose -f "%CD%\docker-compose.yml" down
docker-compose -f "%CD%\docker-compose.yml" build
docker-compose -f "%CD%\docker-compose.yml" up -d

echo.
echo 📊 Статус:
docker-compose -f "%CD%\docker-compose.yml" ps

goto :end

:create_basic
echo Создаю минимальный docker-compose.yml...
(
echo name: agi-layer
echo.
echo services:
echo   postgres:
echo     image: postgres:15-alpine
echo     environment:
echo       POSTGRES_DB: agi_layer
echo       POSTGRES_USER: agi_user
echo       POSTGRES_PASSWORD: agi_password
echo     ports:
echo       - "5432:5432"
echo.
echo   redis:
echo     image: redis:7-alpine
echo     ports:
echo       - "6379:6379"
echo.
echo   app:
echo     build: .
echo     environment:
echo       - TELEGRAM_BOT_TOKEN=8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw
echo       - TELEGRAM_CHAT_ID=458589236
echo     ports:
echo       - "8000:8000"
echo       - "8501:8501"
echo     depends_on:
echo       - postgres
echo       - redis
) > docker-compose.yml

echo ✅ Базовый docker-compose.yml создан
docker-compose up -d

:end
echo.
echo ✅ Готово!
pause
