#!/usr/bin/env python3
"""
Проверка сообщений в Telegram
"""

import asyncio
import aiohttp
import json

TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

async def check_messages():
    """Проверка сообщений"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}/getUpdates"
            params = {"limit": 5, "timeout": 10}
            async with session.get(url, params=params) as response:
                print(f"HTTP статус: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        updates = data.get('result', [])
                        print(f"📨 Получено {len(updates)} обновлений:")
                        print("=" * 50)
                        
                        for i, update in enumerate(updates):
                            print(f"\n📬 Обновление #{i+1}:")
                            print(f"ID: {update.get('update_id')}")
                            
                            if 'message' in update:
                                message = update['message']
                                text = message.get('text', '')
                                user = message.get('from', {})
                                user_name = user.get('first_name', 'Неизвестно')
                                user_id = user.get('id', '')
                                chat_id = message.get('chat', {}).get('id', '')
                                date = message.get('date', '')
                                
                                print(f"👤 От: {user_name} (ID: {user_id})")
                                print(f"💬 Сообщение: {text}")
                                print(f"💬 Чат ID: {chat_id}")
                                print(f"🕐 Дата: {date}")
                                
                                # Проверяем, есть ли ответ
                                if 'reply_to_message' in message:
                                    reply = message['reply_to_message']
                                    print(f"↩️ Ответ на: {reply.get('text', '')[:50]}...")
                                else:
                                    print("❓ Нет ответа")
                            else:
                                print("❌ Не сообщение")
                            print("-" * 30)
                        return updates
                    else:
                        print(f"❌ Ошибка API: {data}")
                else:
                    print(f"❌ HTTP ошибка: {response.status}")
                    response_text = await response.text()
                    print(f"Ответ: {response_text}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    return []

async def main():
    """Основная функция"""
    print("🔍 Проверка сообщений в Telegram...")
    print("=" * 50)
    updates = await check_messages()
    
    if not updates:
        print("📭 Нет новых сообщений")
    else:
        print(f"\n📬 Всего найдено {len(updates)} сообщений")

if __name__ == "__main__":
    asyncio.run(main())