#!/usr/bin/env python3
"""
Прямая отправка сообщения в Telegram
"""

import asyncio
import aiohttp

TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
CHAT_ID = "458589236"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

async def send_direct_message():
    """Прямая отправка сообщения"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": """🤖 <b>AGI Layer v3.9</b> - Система управления

Привет! 👋

Система запущена и работает.

<b>Доступные команды:</b>
/start - Показать меню
/status - Статус системы  
/help - Помощь
/time - Текущее время
/ping - Проверка связи

<b>Что я умею:</b>
• Отвечать на команды
• Показывать статус системы  
• Обрабатывать запросы

Попробуйте отправить /start или любое сообщение! 😊

Система готова к работе! ✅""",
                "parse_mode": "HTML"
            }
            async with session.post(url, json=data) as response:
                print(f"HTTP статус: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    if result.get('ok'):
                        print("✅ Сообщение успешно отправлено!")
                        message = result.get('result', {})
                        print(f"ID сообщения: {message.get('message_id')}")
                        print(f"Дата: {message.get('date')}")
                        return True
                    else:
                        print(f"❌ Ошибка API: {result}")
                else:
                    print(f"❌ HTTP ошибка: {response.status}")
                    response_text = await response.text()
                    print(f"Ответ сервера: {response_text}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    return False

async def main():
    """Основная функция"""
    print("📤 Прямая отправка сообщения в Telegram...")
    print("=" * 50)
    success = await send_direct_message()
    if success:
        print("\n🎉 Сообщение доставлено!")
    else:
        print("\n❌ Не удалось отправить сообщение")

if __name__ == "__main__":
    asyncio.run(main())