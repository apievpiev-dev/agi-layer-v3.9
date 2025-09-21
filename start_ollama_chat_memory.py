#!/usr/bin/env python3
"""
Запуск веб-чата с Ollama и памятью
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавление корневой директории в путь
sys.path.append(str(Path(__file__).parent))

from services.ollama_chat_with_memory import OllamaChatWithMemory


async def main():
    """Основная функция запуска Ollama Chat with Memory"""
    print("🧠 Запуск веб-чата с Ollama и памятью...")
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Конфигурация
    config = {
        'ollama_host': os.getenv('OLLAMA_HOST', 'localhost'),
        'ollama_port': int(os.getenv('OLLAMA_PORT', 11434)),
        'postgres': {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'agi_layer'),
            'user': os.getenv('POSTGRES_USER', 'agi_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'agi_password')
        },
        'chroma': {
            'host': os.getenv('CHROMA_HOST', 'localhost'),
            'port': int(os.getenv('CHROMA_PORT', 8000))
        }
    }
    
    print(f"📡 Подключение к Ollama: {config['ollama_host']}:{config['ollama_port']}")
    print(f"🗄️  База данных: {config['postgres']['host']}:{config['postgres']['port']}/{config['postgres']['database']}")
    print(f"🔍 ChromaDB: {config['chroma']['host']}:{config['chroma']['port']}")
    
    chat_ui = OllamaChatWithMemory(config)
    
    try:
        await chat_ui.initialize()
        print("🌐 Веб-интерфейс доступен по адресу: http://localhost:8503")
        print("🧠 Возможности:")
        print("  - Сохранение истории чатов")
        print("  - Поиск по памяти")
        print("  - Контекстные ответы")
        print("🤖 Для начала работы загрузите модель: ollama pull llama2")
        print("⏹️  Для остановки нажмите Ctrl+C")
        
        chat_ui.run(host="0.0.0.0", port=8503)
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка веб-чата...")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await chat_ui.cleanup()
        print("✅ Веб-чат остановлен")


if __name__ == "__main__":
    asyncio.run(main())