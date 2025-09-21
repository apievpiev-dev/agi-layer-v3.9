#!/usr/bin/env python3
"""
Тестирование веб-чата с Ollama и памятью
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# Добавление корневой директории в путь
sys.path.append(str(Path(__file__).parent))

from services.ollama_chat_with_memory import OllamaChatWithMemory, ChatMemory


async def test_memory_system():
    """Тестирование системы памяти"""
    print("🧠 Тестирование системы памяти...")
    
    config = {
        'postgres': {
            'host': 'localhost',
            'port': 5432,
            'database': 'agi_layer',
            'user': 'agi_user',
            'password': 'agi_password'
        },
        'chroma': {
            'host': 'localhost',
            'port': 8000
        }
    }
    
    try:
        memory = ChatMemory(config)
        await memory.initialize()
        
        # Тест создания сессии
        session_id = await memory.create_session("Тестовая сессия")
        print(f"✅ Создана сессия: {session_id}")
        
        # Тест добавления сообщений
        await memory.add_message(session_id, "user", "Привет, как дела?")
        await memory.add_message(session_id, "assistant", "Привет! У меня все хорошо, спасибо!")
        print("✅ Сообщения добавлены в память")
        
        # Тест поиска в памяти
        results = await memory.search_memory("как дела", limit=3)
        print(f"✅ Найдено результатов в памяти: {len(results)}")
        
        # Тест получения контекста
        context = await memory.get_context_for_session(session_id, "как дела")
        print(f"✅ Получен контекст: {len(context)} сообщений")
        
        await memory.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования памяти: {e}")
        return False


async def test_ollama_connection():
    """Тестирование подключения к Ollama"""
    print("🔍 Тестирование подключения к Ollama...")
    
    try:
        async with aiohttp.ClientSession() as session:
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


async def test_database_connections():
    """Тестирование подключений к базам данных"""
    print("🗄️  Тестирование подключений к базам данных...")
    
    # Тест PostgreSQL
    try:
        import asyncpg
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            database='agi_layer',
            user='agi_user',
            password='agi_password'
        )
        await conn.close()
        print("✅ PostgreSQL подключен")
        postgres_ok = True
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        postgres_ok = False
    
    # Тест ChromaDB
    try:
        import chromadb
        client = chromadb.HttpClient(host='localhost', port=8000)
        client.list_collections()
        print("✅ ChromaDB подключен")
        chroma_ok = True
    except Exception as e:
        print(f"❌ Ошибка подключения к ChromaDB: {e}")
        chroma_ok = False
    
    return postgres_ok and chroma_ok


async def test_web_chat_memory():
    """Тестирование веб-чата с памятью"""
    print("\n🧪 Тестирование веб-чата с памятью...")
    
    config = {
        'ollama_host': 'localhost',
        'ollama_port': 11434,
        'postgres': {
            'host': 'localhost',
            'port': 5432,
            'database': 'agi_layer',
            'user': 'agi_user',
            'password': 'agi_password'
        },
        'chroma': {
            'host': 'localhost',
            'port': 8000
        }
    }
    
    try:
        chat_ui = OllamaChatWithMemory(config)
        await chat_ui.initialize()
        
        # Тест получения моделей
        models = await chat_ui._get_available_models()
        print(f"✅ Веб-чат с памятью инициализирован. Модели: {models}")
        
        # Тест создания сессии
        session_id = await chat_ui.memory.create_session("Тестовая сессия")
        print(f"✅ Создана тестовая сессия: {session_id}")
        
        await chat_ui.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования веб-чата с памятью: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование Ollama Chat с Памятью")
    print("=" * 50)
    
    # Тест 1: Подключения к базам данных
    db_ok = await test_database_connections()
    
    if not db_ok:
        print("\n❌ Проблемы с базами данных.")
        print("\n💡 Решения:")
        print("1. Запустите PostgreSQL: docker run -d -p 5432:5432 -e POSTGRES_DB=agi_layer -e POSTGRES_USER=agi_user -e POSTGRES_PASSWORD=agi_password postgres:15-alpine")
        print("2. Запустите ChromaDB: docker run -d -p 8000:8000 chromadb/chroma:latest")
        sys.exit(1)
    
    # Тест 2: Система памяти
    memory_ok = await test_memory_system()
    
    if not memory_ok:
        print("\n❌ Тест системы памяти не пройден")
        sys.exit(1)
    
    # Тест 3: Подключение к Ollama
    ollama_ok = await test_ollama_connection()
    
    if ollama_ok:
        # Тест 4: Веб-чат с памятью
        chat_ok = await test_web_chat_memory()
        
        if chat_ok:
            print("\n🎉 Все тесты пройдены успешно!")
            print("\n📋 Следующие шаги:")
            print("1. Запустите чат с памятью: python3 start_ollama_chat_memory.py")
            print("2. Или через Docker: docker-compose -f docker-compose-ollama-memory.yml up -d")
            print("3. Откройте браузер: http://localhost:8503")
            print("4. Создайте новый чат и начните общение!")
        else:
            print("\n❌ Тест веб-чата с памятью не пройден")
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