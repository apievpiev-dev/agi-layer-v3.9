#!/usr/bin/env python3
"""
Проверка статуса Telegram бота
"""

import requests
import json

TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
CHAT_ID = "458589236"

def check_bot_status():
    """Проверяет статус бота через API"""
    try:
        # Проверка бота
        bot_url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(bot_url)
        
        if response.status_code == 200:
            bot_data = response.json()
            print("✅ Бот активен:")
            print(f"   Имя: {bot_data['result']['first_name']}")
            print(f"   Username: @{bot_data['result']['username']}")
            print(f"   ID: {bot_data['result']['id']}")
        else:
            print(f"❌ Ошибка проверки бота: {response.status_code}")
            return False
            
        # Проверка обновлений
        updates_url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        updates_response = requests.get(updates_url)
        
        if updates_response.status_code == 200:
            updates = updates_response.json()
            print(f"\n📨 Получено обновлений: {len(updates['result'])}")
            
            if updates['result']:
                print("Последние сообщения:")
                for update in updates['result'][-3:]:  # Последние 3
                    if 'message' in update:
                        msg = update['message']
                        text = msg.get('text', '[медиа]')
                        from_user = msg['from']['first_name']
                        print(f"   {from_user}: {text}")
            else:
                print("   Нет новых сообщений")
                
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def send_test_message():
    """Отправляет тестовое сообщение"""
    try:
        send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {
            'chat_id': CHAT_ID,
            'text': '🤖 Тест: Бот работает!'
        }
        
        response = requests.post(send_url, data=data)
        
        if response.status_code == 200:
            print("✅ Тестовое сообщение отправлено!")
            return True
        else:
            print(f"❌ Ошибка отправки: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Проверка Telegram бота...")
    print("=" * 50)
    
    if check_bot_status():
        print("\n" + "=" * 50)
        print("📤 Отправка тестового сообщения...")
        send_test_message()
    
    print("\n" + "=" * 50)
    print("✅ Проверка завершена!")

