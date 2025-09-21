#!/usr/bin/env python3
"""
Тест веб-чата с Ollama
"""

import asyncio
import aiohttp
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ollama_chat import OllamaChatService


async def test_ollama_connection():
    """Тест подключения к Ollama"""
    print("🔍 Тестирование подключения к Ollama...")
    
    ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    service = OllamaChatService(ollama_url)
    
    try:
        await service.initialize()
        
        # Проверка статуса
        status = await service.check_ollama_status()
        if status:
            print("✅ Ollama сервер доступен")
        else:
            print("❌ Ollama сервер недоступен")
            return False
        
        # Получение списка моделей
        models = await service.get_models()
        if models:
            print(f"📋 Доступные модели ({len(models)}):")
            for model in models:
                size_mb = model.get('size', 0) / (1024 * 1024) if model.get('size') else 0
                print(f"  - {model['name']} ({size_mb:.1f} MB)")
        else:
            print("⚠️ Нет доступных моделей")
            print("💡 Загрузите модель: ollama pull llama2")
            return False
        
        # Тест генерации ответа
        if models:
            test_model = models[0]['name']
            print(f"🧪 Тестирование генерации с моделью: {test_model}")
            
            test_prompt = "Привет! Как дела?"
            response = await service.generate_response(test_model, test_prompt)
            
            if response and not response.startswith("Ошибка"):
                print(f"✅ Тест генерации успешен")
                print(f"📝 Ответ: {response[:100]}...")
            else:
                print(f"❌ Ошибка генерации: {response}")
                return False
        
        print("🎉 Все тесты пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False
    
    finally:
        if service.http_session:
            await service.http_session.close()


async def test_streaming():
    """Тест потоковой генерации"""
    print("\n🌊 Тестирование потоковой генерации...")
    
    ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    service = OllamaChatService(ollama_url)
    
    try:
        await service.initialize()
        
        models = await service.get_models()
        if not models:
            print("⚠️ Нет моделей для тестирования")
            return False
        
        test_model = models[0]['name']
        test_prompt = "Расскажи короткую историю про кота"
        
        print(f"📝 Промпт: {test_prompt}")
        print("📤 Потоковый ответ:")
        
        full_response = ""
        async for chunk in service.stream_response(test_model, test_prompt):
            full_response += chunk
            print(chunk, end='', flush=True)
        
        print(f"\n✅ Потоковая генерация завершена ({len(full_response)} символов)")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка потокового тестирования: {e}")
        return False
    
    finally:
        if service.http_session:
            await service.http_session.close()


async def main():
    """Основная функция тестирования"""
    print("=" * 50)
    print("🤖 ТЕСТ ВЕБ-ЧАТА С OLLAMA")
    print("=" * 50)
    
    # Проверка переменных окружения
    ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    print(f"🔗 Ollama URL: {ollama_url}")
    
    # Тест подключения
    connection_ok = await test_ollama_connection()
    
    if connection_ok:
        # Тест потоковой генерации
        await test_streaming()
    
    print("\n" + "=" * 50)
    if connection_ok:
        print("🎉 ВЕБ-ЧАТ ГОТОВ К ИСПОЛЬЗОВАНИЮ!")
        print("🌐 Откройте: http://localhost:8501")
    else:
        print("❌ ТРЕБУЕТСЯ НАСТРОЙКА")
        print("💡 Запустите: ollama serve")
        print("💡 Загрузите модель: ollama pull llama2")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())