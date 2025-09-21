#!/usr/bin/env python3
"""
Очистка webhook для Telegram бота
"""

import asyncio
import aiohttp

TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

async def clear_webhook():
    """Очистка webhook"""
    try:
        async with aiohttp.ClientSession() as session:
            # Получение информации о webhook
            url = f"{API_URL}/getWebhookInfo"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        webhook_info = data.get('result', {})
                        print(f"📡 Webhook URL: {webhook_info.get('url', 'Не установлен')}")
                        print(f"📡 Webhook pending: {webhook_info.get('pending_update_count', 0)}")
                        
                        # Очистка webhook
                        clear_url = f"{API_URL}/deleteWebhook"
                        async with session.post(clear_url) as clear_response:
                            if clear_response.status == 200:
                                clear_data = await clear_response.json()
                                if clear_data.get('ok'):
                                    print("✅ Webhook очищен!")
                                    return True
                                else:
                                    print(f"❌ Ошибка очистки: {clear_data}")
                            else:
                                print(f"❌ HTTP ошибка: {clear_response.status}")
                    else:
                        print(f"❌ Ошибка API: {data}")
                else:
                    print(f"❌ HTTP ошибка: {response.status}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    return False

async def main():
    """Основная функция"""
    print("🧹 Очистка webhook Telegram бота...")
    print("=" * 50)
    await clear_webhook()

if __name__ == "__main__":
    asyncio.run(main())