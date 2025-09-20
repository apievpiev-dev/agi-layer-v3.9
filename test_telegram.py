#!/usr/bin/env python3
"""
Тест Telegram бота AGI Layer v3.9
"""

import asyncio
import logging
from telegram import Bot
from telegram.error import TelegramError

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_telegram_bot():
    """Тест Telegram бота"""
    
    # Ваши настройки
    TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
    CHAT_ID = "458589236"
    
    try:
        print("🤖 Тестирование Telegram бота...")
        
        # Создание бота
        bot = Bot(token=TOKEN)
        
        # Проверка токена
        print("📡 Проверка токена...")
        bot_info = await bot.get_me()
        print(f"✅ Бот подключен: @{bot_info.username}")
        print(f"   Имя: {bot_info.first_name}")
        print(f"   ID: {bot_info.id}")
        
        # Отправка тестового сообщения
        print("📤 Отправка тестового сообщения...")
        message = await bot.send_message(
            chat_id=CHAT_ID,
            text="🤖 AGI Layer v3.9 - Тест подключения!\n\nСистема работает корректно!"
        )
        print(f"✅ Сообщение отправлено! ID: {message.message_id}")
        
        # Проверка получения обновлений
        print("📥 Проверка получения сообщений...")
        updates = await bot.get_updates(limit=1)
        print(f"✅ Получено обновлений: {len(updates)}")
        
        print("\n🎉 Telegram бот работает корректно!")
        return True
        
    except TelegramError as e:
        print(f"❌ Ошибка Telegram API: {e}")
        return False
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

async def test_bot_commands():
    """Тест команд бота"""
    
    TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
    CHAT_ID = "458589236"
    
    try:
        print("\n🧪 Тестирование команд бота...")
        
        bot = Bot(token=TOKEN)
        
        # Список команд
        commands = [
            ("start", "Запуск системы AGI Layer v3.9"),
            ("status", "Статус всех агентов системы"),
            ("generate", "Генерация изображения по описанию"),
            ("report", "Отчет о работе системы"),
            ("reboot", "Перезапуск системы")
        ]
        
        # Установка команд
        await bot.set_my_commands(commands)
        print("✅ Команды бота установлены")
        
        # Отправка списка команд
        commands_text = "🤖 Доступные команды:\n\n"
        for cmd, desc in commands:
            commands_text += f"/{cmd} - {desc}\n"
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=commands_text
        )
        print("✅ Список команд отправлен")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка установки команд: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТ TELEGRAM БОТА AGI LAYER V3.9")
    print("=" * 50)
    
    # Тест подключения
    connection_test = await test_telegram_bot()
    
    if connection_test:
        # Тест команд
        commands_test = await test_bot_commands()
        
        if commands_test:
            print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
            print("\n📱 Теперь можете использовать команды:")
            print("   /start - запуск системы")
            print("   /status - статус агентов")
            print("   /generate beautiful landscape - генерация изображения")
            print("   /report - отчет системы")
        else:
            print("\n❌ Ошибка в командах бота")
    else:
        print("\n❌ Ошибка подключения к Telegram")
        print("\n🔧 Возможные проблемы:")
        print("   1. Неверный токен бота")
        print("   2. Неверный Chat ID")
        print("   3. Бот не запущен")
        print("   4. Проблемы с интернетом")

if __name__ == "__main__":
    asyncio.run(main())

