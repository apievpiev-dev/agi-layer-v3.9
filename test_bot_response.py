#!/usr/bin/env python3
"""
Тест ответов Telegram бота
"""

import asyncio
import aiohttp
import time

TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
CHAT_ID = "458589236"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

async def send_test_command(command):
    """Отправка тестовой команды"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": command
            }
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('ok'):
                        print(f"✅ Команда '{command}' отправлена")
                        return True
                    else:
                        print(f"❌ Ошибка отправки: {result}")
                else:
                    print(f"❌ HTTP ошибка: {response.status}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    return False

async def get_last_messages():
    """Получение последних сообщений"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}/getUpdates"
            params = {"limit": 10}
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        updates = data.get('result', [])
                        messages = []
                        for update in updates:
                            if 'message' in update:
                                message = update['message']
                                text = message.get('text', '')
                                date = message.get('date', 0)
                                messages.append((text, date))
                        return messages
    except Exception as e:
        print(f"❌ Ошибка получения сообщений: {e}")
    return []

async def main():
    """Основная функция"""
    print("🧪 Тест ответов Telegram бота...")
    print("=" * 50)
    
    # Получаем начальное состояние
    print("📋 Получение начального состояния...")
    initial_messages = await get_last_messages()
    print(f"Начальных сообщений: {len(initial_messages)}")
    
    # Отправляем тестовую команду
    test_command = "/start"
    print(f"\n📤 Отправка команды: {test_command}")
    success = await send_test_command(test_command)
    
    if success:
        print("⏳ Ожидание ответа (5 секунд)...")
        await asyncio.sleep(5)
        
        # Проверяем новые сообщения
        print("📋 Проверка новых сообщений...")
        new_messages = await get_last_messages()
        
        if len(new_messages) > len(initial_messages):
            print("✅ Получен ответ от бота!")
            print("📬 Последние сообщения:")
            for i, (text, date) in enumerate(new_messages[-3:]):  # Последние 3
                print(f"  {i+1}. {text[:100]}...")
        else:
            print("❌ Ответ от бота не получен")
            print("💡 Возможные причины:")
            print("   - Бот не запущен")
            print("   - Бот не обрабатывает сообщения")
            print("   - Проблемы с сетью")
    else:
        print("❌ Не удалось отправить команду")

if __name__ == "__main__":
    asyncio.run(main())