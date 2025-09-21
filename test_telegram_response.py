#!/usr/bin/env python3
"""
Тест получения сообщений от Telegram бота
"""

import asyncio
import aiohttp
import json

TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
CHAT_ID = "458589236"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

async def get_recent_messages():
    """Получение последних сообщений"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}/getUpdates"
            params = {"limit": 10, "timeout": 10}
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        updates = data.get('result', [])
                        print(f"📨 Получено {len(updates)} обновлений:")
                        print("=" * 50)
                        
                        for update in updates:
                            if 'message' in update:
                                message = update['message']
                                text = message.get('text', '')
                                user = message.get('from', {})
                                user_name = user.get('first_name', 'Неизвестно')
                                chat_id = message.get('chat', {}).get('id', '')
                                date = message.get('date', '')
                                
                                print(f"👤 От: {user_name} (ID: {chat_id})")
                                print(f"💬 Сообщение: {text}")
                                print(f"🕐 Дата: {date}")
                                print("-" * 30)
                        return updates
                    else:
                        print(f"❌ Ошибка API: {data}")
                else:
                    print(f"❌ HTTP ошибка: {response.status}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    return []

async def send_test_message():
    """Отправка тестового сообщения"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": "🤖 Тест: Бот работает и готов отвечать на сообщения!"
            }
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('ok'):
                        print("✅ Тестовое сообщение отправлено!")
                        return True
                    else:
                        print(f"❌ Ошибка отправки: {result}")
                else:
                    print(f"❌ HTTP ошибка: {response.status}")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
    return False

async def main():
    """Основная функция"""
    print("🔍 Проверка Telegram бота...")
    print("=" * 50)
    
    # Отправка тестового сообщения
    await send_test_message()
    print()
    
    # Получение последних сообщений
    updates = await get_recent_messages()
    
    if not updates:
        print("📭 Нет новых сообщений")
    else:
        print(f"📬 Найдено {len(updates)} сообщений")

if __name__ == "__main__":
    asyncio.run(main())