#!/usr/bin/env python3
"""
Простой тест Telegram бота
"""

import requests
import json

def test_telegram_simple():
    """Простой тест Telegram API"""
    
    TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
    CHAT_ID = "458589236"
    
    print("🤖 ПРОСТОЙ ТЕСТ TELEGRAM БОТА")
    print("=" * 40)
    
    # 1. Проверка бота
    print("1️⃣ Проверка бота...")
    url = f"https://api.telegram.org/bot{TOKEN}/getMe"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                bot_info = data['result']
                print(f"✅ Бот активен: @{bot_info['username']}")
                print(f"   Имя: {bot_info['first_name']}")
            else:
                print(f"❌ Ошибка: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    # 2. Отправка сообщения
    print("\n2️⃣ Отправка тестового сообщения...")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": "🤖 AGI Layer v3.9 - Тест!\n\nБот работает! ✅"
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            if result['ok']:
                print("✅ Сообщение отправлено!")
                return True
            else:
                print(f"❌ Ошибка отправки: {result.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_telegram_simple()
    
    if success:
        print("\n🎉 ТЕСТ УСПЕШЕН!")
        print("📱 Теперь можете писать боту команды:")
        print("   /start")
        print("   /status")
        print("   /generate beautiful landscape")
    else:
        print("\n❌ ТЕСТ НЕ ПРОЙДЕН")
        print("🔧 Проверьте:")
        print("   1. Правильность токена")
        print("   2. Chat ID")
        print("   3. Интернет соединение")

