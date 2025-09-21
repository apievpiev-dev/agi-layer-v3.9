@echo off
chcp 65001 >nul
title AGI Layer v3.9 - Telegram Chat Bot

echo.
echo ===============================================
echo   🤖 AGI Layer v3.9 - Telegram Chat Bot
echo ===============================================
echo.

echo 🔧 Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python найден

echo.
echo 📦 Установка зависимостей...
pip install python-telegram-bot aiohttp asyncpg pillow torch transformers diffusers >nul 2>&1

echo.
echo 🚀 Запуск Telegram чат-бота...
echo.
echo 💬 Бот будет доступен в Telegram после запуска
echo 🔗 Найдите бота по токену или используйте существующий чат
echo.
echo ⚡ Для остановки нажмите Ctrl+C
echo.

python telegram_chat_bot.py

echo.
echo 🛑 Бот остановлен
pause