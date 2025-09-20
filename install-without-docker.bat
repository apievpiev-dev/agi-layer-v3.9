@echo off
echo 🚀 AGI Layer v3.9 - Установка БЕЗ Docker
echo.

echo 📦 Установка Python зависимостей...
pip install -r requirements-minimal.txt

echo.
echo 🗄️ Создание локальных папок...
mkdir logs 2>nul
mkdir models 2>nul
mkdir data 2>nul

echo.
echo 📝 Создание .env файла...
if not exist .env (
    copy env.example .env
    echo ✅ .env файл создан из примера
)

echo.
echo 🤖 Запуск Telegram бота...
python telegram_bot.py

echo.
echo ✅ Установка завершена!
echo 🌐 Web UI доступен по адресу: http://localhost:8501
echo.
pause
