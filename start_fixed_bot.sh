#!/bin/bash

# AGI Layer v3.9 - Исправленный Telegram Bot

echo "==============================================="
echo "  🤖 AGI Layer v3.9 - Исправленный бот"
echo "==============================================="
echo

# Проверка Python
echo "🔧 Проверка Python..."
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ Python не найден! Установите Python 3.8+"
    exit 1
fi

echo "✅ Python найден: $($PYTHON --version)"

# Запуск бота
echo
echo "🚀 Запуск исправленного Telegram бота..."
echo
echo "💬 Бот работает в демо режиме без внешних зависимостей"
echo "🔗 Найдите бота в Telegram и напишите /start"
echo
echo "⚡ Для остановки нажмите Ctrl+C"
echo

$PYTHON telegram_chat_bot_fixed.py