#!/bin/bash

echo "========================================"
echo "   AGI Layer v3.9 - Telegram Chat"
echo "========================================"
echo

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "[ERROR] Файл .env не найден!"
    echo "Скопируйте env.example в .env и настройте параметры."
    echo
    cp env.example .env
    echo "Файл .env создан. Отредактируйте его и запустите скрипт снова."
    exit 1
fi

echo "[INFO] Проверка Docker..."
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker не установлен или недоступен!"
    echo "Установите Docker и запустите его."
    exit 1
fi

echo "[INFO] Проверка Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "[ERROR] Docker Compose не найден!"
    exit 1
fi

echo "[INFO] Остановка существующих контейнеров..."
docker-compose down

echo "[INFO] Запуск системы AGI с Telegram Chat..."
echo
echo "Запускаются сервисы:"
echo "- PostgreSQL (база данных)"
echo "- ChromaDB (векторная память)"
echo "- Redis (кэш)"
echo "- MetaAgent (координатор)"
echo "- TextAgent (нейросеть Phi-2)"
echo "- VisionAgent (анализ изображений)"
echo "- ImageAgent (генерация изображений)"
echo "- TelegramChatAgent (чат-бот)"
echo

docker-compose up -d postgres chromadb redis
echo "[INFO] Ожидание запуска баз данных..."
sleep 10

docker-compose up -d meta_agent
echo "[INFO] Ожидание запуска MetaAgent..."
sleep 5

docker-compose up -d text_agent vision_agent image_agent
echo "[INFO] Ожидание запуска AI агентов..."
sleep 15

docker-compose up -d telegram_chat_agent
echo "[INFO] Запуск Telegram Chat Agent..."
sleep 5

echo
echo "========================================"
echo "   СИСТЕМА ЗАПУЩЕНА!"
echo "========================================"
echo
echo "🤖 Telegram Chat Bot готов к работе!"
echo
echo "📱 Найдите вашего бота в Telegram и отправьте /start"
echo
echo "🌐 Доступные интерфейсы:"
echo "  - ChromaDB: http://localhost:8000"
echo "  - PostgreSQL: localhost:5432"
echo
echo "📊 Проверка статуса:"
echo "  docker-compose ps"
echo
echo "📋 Просмотр логов:"
echo "  docker-compose logs -f telegram_chat_agent"
echo
echo "🛑 Остановка системы:"
echo "  docker-compose down"
echo

# Показать статус сервисов
echo "[INFO] Статус сервисов:"
docker-compose ps

echo
read -p "Нажмите Enter для просмотра логов чат-бота..."

echo
echo "========================================"
echo "   ЛОГИ TELEGRAM CHAT AGENT"
echo "========================================"
echo "Нажмите Ctrl+C для выхода из просмотра логов"
echo

docker-compose logs -f telegram_chat_agent