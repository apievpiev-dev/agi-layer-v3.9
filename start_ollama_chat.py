#!/usr/bin/env python3
"""
Запуск веб-чата с Ollama
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавление корневой директории в путь
sys.path.append(str(Path(__file__).parent))

from services.ollama_web_chat import OllamaWebChat


async def main():
    """Основная функция запуска Ollama Chat"""
    print("🚀 Запуск веб-чата с Ollama...")
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Конфигурация
    config = {
        'ollama_host': os.getenv('OLLAMA_HOST', 'localhost'),
        'ollama_port': int(os.getenv('OLLAMA_PORT', 11434))
    }
    
    print(f"📡 Подключение к Ollama: {config['ollama_host']}:{config['ollama_port']}")
    
    chat_ui = OllamaWebChat(config)
    
    try:
        await chat_ui.initialize()
        print("🌐 Веб-интерфейс доступен по адресу: http://localhost:8502")
        print("🤖 Для начала работы загрузите модель: ollama pull llama2")
        print("⏹️  Для остановки нажмите Ctrl+C")
        
        chat_ui.run(host="0.0.0.0", port=8502)
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка веб-чата...")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await chat_ui.cleanup()
        print("✅ Веб-чат остановлен")


if __name__ == "__main__":
    asyncio.run(main())