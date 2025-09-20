#!/bin/bash

# AGI Layer v3.9 - Скрипт развертывания

set -e

echo "🚀 AGI Layer v3.9 - Развертывание системы"

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
    exit 1
fi

echo "✅ Docker и Docker Compose найдены"

# Создание .env файла если не существует
if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cp .env.example .env
    echo "⚠️  Отредактируйте .env файл с вашими настройками"
fi

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p logs models output/images data/chroma backups

# Установка прав доступа
echo "🔐 Установка прав доступа..."
chmod +x scripts/*.sh
chmod +x docker-entrypoint.sh

# Проверка доступности портов
echo "🔍 Проверка портов..."
PORTS=(5432 6379 8000 8001 8002 8003 8004 8005 8006 8007 8008 8501)
for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Порт $port уже используется"
    fi
done

# Загрузка моделей (опционально)
if [ "$1" = "--with-models" ]; then
    echo "📥 Загрузка моделей..."
    docker run --rm -v $(pwd)/models:/app/models agi-layer-v3.9 python scripts/download_models.py --all
fi

# Сборка Docker образов
echo "🔨 Сборка Docker образов..."
docker-compose build

# Запуск сервисов
echo "🚀 Запуск сервисов..."
docker-compose up -d

# Ожидание готовности сервисов
echo "⏳ Ожидание готовности сервисов..."
sleep 10

# Проверка статуса сервисов
echo "🔍 Проверка статуса сервисов..."
docker-compose ps

# Показать логи
echo "📋 Показать логи (Ctrl+C для выхода)..."
docker-compose logs -f

echo "✅ AGI Layer v3.9 успешно развернут!"
echo ""
echo "🌐 Web UI: http://localhost:8501"
echo "📊 MetaAgent API: http://localhost:8001"
echo "📱 Telegram Agent: http://localhost:8002"
echo ""
echo "Для остановки: docker-compose down"
echo "Для просмотра логов: docker-compose logs -f"
echo "Для перезапуска: docker-compose restart"

