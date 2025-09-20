#!/bin/bash

# AGI Layer v3.9 - Entrypoint скрипт

set -e

echo "🚀 Запуск AGI Layer v3.9 - $SERVICE_NAME"

# Ожидание готовности базы данных
if [ "$SERVICE_NAME" != "postgres" ]; then
    echo "⏳ Ожидание готовности PostgreSQL..."
    until pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER; do
        echo "PostgreSQL недоступен - ожидание..."
        sleep 2
    done
    echo "✅ PostgreSQL готов"
fi

# Ожидание готовности ChromaDB для сервисов, которые его используют
if [[ "$SERVICE_NAME" == "embedding_agent" ]] || [[ "$SERVICE_NAME" == "meta_agent" ]]; then
    echo "⏳ Ожидание готовности ChromaDB..."
    until curl -s http://$CHROMA_HOST:$CHROMA_PORT/api/v1/heartbeat; do
        echo "ChromaDB недоступен - ожидание..."
        sleep 2
    done
    echo "✅ ChromaDB готов"
fi

# Загрузка моделей при первом запуске
if [ "$DOWNLOAD_MODELS_ON_START" = "true" ]; then
    echo "📥 Проверка и загрузка моделей..."
    python scripts/download_models.py --check-only
fi

# Запуск сервиса
case $SERVICE_NAME in
    "meta_agent")
        echo "🎯 Запуск MetaAgent..."
        python -m agents.meta_agent
        ;;
    "telegram_agent")
        echo "📱 Запуск TelegramAgent..."
        python -m agents.telegram_agent
        ;;
    "image_agent")
        echo "🎨 Запуск ImageAgent..."
        python -m agents.image_agent
        ;;
    "text_agent")
        echo "📝 Запуск TextAgent..."
        python -m agents.text_agent
        ;;
    "vision_agent")
        echo "👁️ Запуск VisionAgent..."
        python -m agents.vision_agent
        ;;
    "ocr_agent")
        echo "🔍 Запуск OCRAgent..."
        python -m agents.ocr_agent
        ;;
    "embedding_agent")
        echo "🧠 Запуск EmbeddingAgent..."
        python -m agents.embedding_agent
        ;;
    "recovery_agent")
        echo "🔄 Запуск RecoveryAgent..."
        python -m agents.recovery_agent
        ;;
    "web_ui")
        echo "🌐 Запуск Web UI..."
        python -m services.web_ui
        ;;
    "watchdog")
        echo "🐕 Запуск Watchdog..."
        python -m services.watchdog
        ;;
    *)
        echo "❌ Неизвестный сервис: $SERVICE_NAME"
        exit 1
        ;;
esac

