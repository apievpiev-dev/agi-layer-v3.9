#!/usr/bin/env python3
"""
Финальный тест Telegram бота
"""

import asyncio
import aiohttp
import json

TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
CHAT_ID = "458589236"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

async def test_bot():
    """Тест бота"""
    print("🧪 Финальный тест Telegram бота...")
    print("=" * 50)
    
    # 1. Отправка сообщения
    print("📤 1. Отправка тестового сообщения...")
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": "/start",
                "parse_mode": "HTML"
            }
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('ok'):
                        print("✅ Сообщение отправлено успешно!")
                        message_id = result.get('result', {}).get('message_id')
                        print(f"ID сообщения: {message_id}")
                    else:
                        print(f"❌ Ошибка API: {result}")
                        return
                else:
                    print(f"❌ HTTP ошибка: {response.status}")
                    return
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return
    
    # 2. Ожидание
    print("\n⏳ 2. Ожидание ответа (10 секунд)...")
    await asyncio.sleep(10)
    
    # 3. Проверка обновлений
    print("📋 3. Проверка обновлений...")
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}/getUpdates"
            params = {"limit": 5}
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        updates = data.get('result', [])
                        print(f"📨 Получено {len(updates)} обновлений")
                        
                        if updates:
                            print("\n📬 Последние сообщения:")
                            for i, update in enumerate(updates[-3:]):
                                if 'message' in update:
                                    message = update['message']
                                    text = message.get('text', '')
                                    user = message.get('from', {})
                                    user_name = user.get('first_name', 'Неизвестно')
                                    date = message.get('date', '')
                                    
                                    print(f"  {i+1}. От {user_name}: {text[:100]}...")
                                    print(f"     Дата: {date}")
                        else:
                            print("📭 Нет сообщений")
                    else:
                        print(f"❌ Ошибка API: {data}")
                else:
                    print(f"❌ HTTP ошибка: {response.status}")
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Результат теста:")
    print("✅ Бот может отправлять сообщения")
    print("❓ Бот может получать сообщения (проверьте в Telegram)")
    print("💡 Отправьте /start в Telegram и проверьте ответ")

async def main():
    """Основная функция"""
    await test_bot()

if __name__ == "__main__":
    asyncio.run(main())