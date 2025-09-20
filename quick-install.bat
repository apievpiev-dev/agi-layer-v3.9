@echo off
echo 🚀 AGI Layer v3.9 - Быстрая установка
echo.

echo 📦 Установка минимальных зависимостей...
pip install -r requirements-minimal.txt

echo.
echo ✅ Базовая установка завершена!
echo.
echo 🔧 Для полной установки запустите:
echo    pip install -r requirements.txt
echo.
echo 🐳 Или используйте Docker:
echo    docker-compose up -d
echo.
pause
