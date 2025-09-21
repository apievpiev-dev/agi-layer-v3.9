@echo off
chcp 65001 >nul
title AGI Layer v3.9 - Исправленный Telegram Bot

echo.
echo ===============================================
echo   🤖 AGI Layer v3.9 - Исправленный бот
echo ===============================================
echo.

echo 🔧 Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Используем python3...
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Python не установлен!
        pause
        exit /b 1
    )
    set PYTHON=python3
) else (
    set PYTHON=python
)

echo ✅ Python найден

echo.
echo 🚀 Запуск исправленного Telegram бота...
echo.
echo 💬 Бот работает в демо режиме без внешних зависимостей
echo 🔗 Найдите бота в Telegram и напишите /start
echo.
echo ⚡ Для остановки нажмите Ctrl+C
echo.

%PYTHON% telegram_chat_bot_fixed.py

echo.
echo 🛑 Бот остановлен
pause