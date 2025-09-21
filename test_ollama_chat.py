#!/usr/bin/env python3
"""
Тестирование веб-чата с Ollama без Docker
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# Добавление корневой директории в путь
sys.path.append(str(Path(__file__).parent))

from services.ollama_web_chat import OllamaWebChat


async def test_ollama_connection():
    """Тестирование подключения к Ollama"""
    print("🔍 Тестирование подключения к Ollama...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Попытка подключения к Ollama
            async with session.get("http://localhost:11434/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    print(f"✅ Ollama работает! Доступные модели: {models}")
                    return True
                else:
                    print(f"❌ Ollama недоступен (статус: {response.status})")
                    return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Ollama: {e}")
        print("\n💡 Решения:")
        print("1. Установите Ollama: https://ollama.ai/download")
        print("2. Запустите Ollama: ollama serve")
        print("3. Загрузите модель: ollama pull llama2")
        return False


async def test_web_chat():
    """Тестирование веб-чата"""
    print("\n🧪 Тестирование веб-чата...")
    
    config = {
        'ollama_host': 'localhost',
        'ollama_port': 11434
    }
    
    try:
        chat_ui = OllamaWebChat(config)
        await chat_ui.initialize()
        
        # Тест получения моделей
        models = await chat_ui._get_available_models()
        print(f"✅ Веб-чат инициализирован. Модели: {models}")
        
        # Тест генерации ответа (если есть модели)
        if models:
            test_prompt = "Привет! Как дела?"
            print(f"📝 Тестирование генерации ответа на: '{test_prompt}'")
            
            response = await chat_ui._generate_single_response(test_prompt, models[0])
            print(f"✅ Получен ответ: {response[:100]}...")
        
        await chat_ui.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования веб-чата: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование Ollama Chat Web Interface")
    print("=" * 50)
    
    # Тест 1: Подключение к Ollama
    ollama_ok = await test_ollama_connection()
    
    if ollama_ok:
        # Тест 2: Веб-чат
        chat_ok = await test_web_chat()
        
        if chat_ok:
            print("\n🎉 Все тесты пройдены успешно!")
            print("\n📋 Следующие шаги:")
            print("1. Запустите веб-чат: python3 start_ollama_chat.py")
            print("2. Откройте браузер: http://localhost:8502")
            print("3. Начните общение с ИИ!")
        else:
            print("\n❌ Тест веб-чата не пройден")
            sys.exit(1)
    else:
        print("\n❌ Ollama недоступен. Проверьте установку и запуск Ollama.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)