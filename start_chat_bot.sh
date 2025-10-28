#!/bin/bash

# AGI Layer v3.9 - Telegram Chat Bot Launcher

echo "==============================================="
echo "  🤖 AGI Layer v3.9 - Telegram Chat Bot"
echo "==============================================="
echo

# Проверка Python
echo "🔧 Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден! Установите Python 3.8+"
    exit 1
fi

echo "✅ Python3 найден: $(python3 --version)"

# Установка зависимостей
echo
echo "📦 Установка зависимостей..."
pip3 install python-telegram-bot aiohttp asyncpg pillow torch transformers diffusers --quiet

# Запуск бота
echo
echo "🚀 Запуск Telegram чат-бота..."
echo
echo "💬 Бот будет доступен в Telegram после запуска"
echo "🔗 Найдите бота по токену или используйте существующий чат"
echo
echo "⚡ Для остановки нажмите Ctrl+C"
echo

python3 telegram_chat_bot.py