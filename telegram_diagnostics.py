#!/usr/bin/env python3
"""
Диагностика проблем с Telegram ботом
"""

import asyncio
import aiohttp
import json

async def check_telegram_api():
    """Проверка Telegram API"""
    
    TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
    CHAT_ID = "458589236"
    
    print("🔍 ДИАГНОСТИКА TELEGRAM БОТА")
    print("=" * 40)
    
    # 1. Проверка токена
    print("1️⃣ Проверка токена бота...")
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{TOKEN}/getMe"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        bot_info = data['result']
                        print(f"✅ Бот активен: @{bot_info['username']}")
                        print(f"   Имя: {bot_info['first_name']}")
                        print(f"   ID: {bot_info['id']}")
                    else:
                        print(f"❌ Ошибка API: {data.get('description')}")
                        return False
                else:
                    print(f"❌ HTTP ошибка: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    
    # 2. Проверка Chat ID
    print(f"\n2️⃣ Проверка Chat ID: {CHAT_ID}")
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{TOKEN}/getChat"
            params = {"chat_id": CHAT_ID}
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        chat_info = data['result']
                        print(f"✅ Чат найден: {chat_info.get('title', chat_info.get('first_name', 'Unknown'))}")
                        print(f"   Тип: {chat_info['type']}")
                    else:
                        print(f"❌ Ошибка чата: {data.get('description')}")
                        return False
                else:
                    print(f"❌ HTTP ошибка: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Ошибка проверки чата: {e}")
        return False
    
    # 3. Отправка тестового сообщения
    print(f"\n3️⃣ Отправка тестового сообщения...")
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": "🤖 AGI Layer v3.9 - Тест подключения!\n\nЕсли вы видите это сообщение, бот работает корректно!"
            }
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('ok'):
                        print("✅ Тестовое сообщение отправлено!")
                        return True
                    else:
                        print(f"❌ Ошибка отправки: {result.get('description')}")
                        return False
                else:
                    print(f"❌ HTTP ошибка: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

async def check_bot_updates():
    """Проверка обновлений бота"""
    
    TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
    
    print(f"\n4️⃣ Проверка обновлений бота...")
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        updates = data['result']
                        print(f"✅ Получено обновлений: {len(updates)}")
                        
                        if updates:
                            print("📥 Последние сообщения:")
                            for update in updates[-3:]:  # Последние 3
                                if 'message' in update:
                                    msg = update['message']
                                    text = msg.get('text', 'Нет текста')
                                    chat_id = msg['chat']['id']
                                    print(f"   Chat {chat_id}: {text}")
                        else:
                            print("ℹ️ Нет новых сообщений")
                        return True
                    else:
                        print(f"❌ Ошибка получения обновлений: {data.get('description')}")
                        return False
                else:
                    print(f"❌ HTTP ошибка: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Ошибка получения обновлений: {e}")
        return False

async def main():
    """Основная функция диагностики"""
    
    # Основные проверки
    api_ok = await check_telegram_api()
    
    if api_ok:
        # Проверка обновлений
        await check_bot_updates()
        
        print(f"\n🎉 ДИАГНОСТИКА ЗАВЕРШЕНА")
        print("✅ Telegram бот работает корректно!")
        print("\n📱 Теперь можете:")
        print("   1. Написать боту /start")
        print("   2. Проверить команды /status, /generate")
        print("   3. Использовать систему AGI Layer v3.9")
        
    else:
        print(f"\n❌ ПРОБЛЕМЫ ОБНАРУЖЕНЫ")
        print("\n🔧 Возможные решения:")
        print("   1. Проверьте правильность токена")
        print("   2. Убедитесь, что бот запущен у @BotFather")
        print("   3. Проверьте Chat ID")
        print("   4. Убедитесь, что бот добавлен в чат")
        print("   5. Проверьте интернет соединение")

if __name__ == "__main__":
    asyncio.run(main())

