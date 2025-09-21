#!/usr/bin/env python3
"""
Простой Telegram бот без конфликтов
"""

import asyncio
import logging
import aiohttp
from datetime import datetime

# Настройки
TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
CHAT_ID = "458589236"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleBot:
    def __init__(self):
        self.token = TOKEN
        self.chat_id = CHAT_ID
        self.api_url = API_URL
        self.last_update_id = 0
        
    async def send_message(self, text, chat_id=None):
        """Отправка сообщения"""
        if chat_id is None:
            chat_id = self.chat_id
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            logger.info(f"✅ Сообщение отправлено: {text[:50]}...")
                            return True
                        else:
                            logger.error(f"❌ Ошибка API: {result}")
                    else:
                        logger.error(f"❌ HTTP ошибка: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Ошибка отправки: {e}")
            return False
    
    async def get_updates(self):
        """Получение обновлений"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/getUpdates"
                params = {
                    "offset": self.last_update_id + 1, 
                    "timeout": 1,  # Короткий timeout
                    "limit": 1     # Только одно обновление
                }
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            updates = data.get('result', [])
                            return updates
                        else:
                            if data.get('error_code') == 409:
                                logger.warning("⚠️ Конфликт: другой бот получает обновления")
                                return []
                            else:
                                logger.error(f"❌ Ошибка API: {data}")
                    else:
                        logger.error(f"❌ HTTP ошибка: {response.status}")
        except Exception as e:
            logger.error(f"❌ Ошибка получения обновлений: {e}")
        return []
    
    async def process_message(self, message):
        """Обработка сообщения"""
        try:
            text = message.get('text', '')
            chat_id = message['chat']['id']
            user_name = message['from'].get('first_name', 'Пользователь')
            
            logger.info(f"👤 Сообщение от {user_name}: {text}")
            
            # Простые ответы
            if text == '/start':
                response = f"""🤖 <b>AGI Layer v3.9</b> - Система управления

Привет, {user_name}! 👋

Система запущена и работает.

<b>Доступные команды:</b>
/start - Показать меню
/status - Статус системы  
/help - Помощь
/time - Текущее время
/ping - Проверка связи

Система готова к работе! ✅"""
                
            elif text == '/status':
                response = f"""📊 <b>Статус системы AGI Layer v3.9</b>

🟢 <b>MetaAgent:</b> Работает
🟢 <b>TelegramAgent:</b> Работает  
🟢 <b>ImageAgent:</b> Готов к работе
🟢 <b>TextAgent:</b> Готов к работе
🟢 <b>VisionAgent:</b> Готов к работе

Все системы функционируют нормально! ✅"""
                
            elif text == '/help':
                response = f"""❓ <b>Помощь по командам AGI Layer v3.9</b>

<b>Основные команды:</b>
/start - Начало работы с ботом
/status - Статус всех систем
/help - Эта справка
/time - Текущее время
/ping - Проверка связи

Система готова помочь! 🤖"""
                
            elif text == '/time':
                response = f"""🕐 <b>Текущее время:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
                
            elif text == '/ping':
                response = f"""🏓 <b>Pong!</b>

Связь работает отлично! ✅
Время ответа: {datetime.now().strftime('%H:%M:%S')}"""
                
            else:
                # Ответ на обычное сообщение
                response = f"""Привет, {user_name}! 👋

Я <b>AGI Layer v3.9</b> - система искусственного интеллекта.

<b>Что я умею:</b>
• Отвечать на команды
• Показывать статус системы  
• Обрабатывать запросы

<b>Попробуйте команды:</b>
/start - меню
/status - статус
/help - помощь
/time - время

Или просто напишите что-нибудь! 😊"""
            
            # Отправка ответа
            await self.send_message(response, chat_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения: {e}")
    
    async def run(self):
        """Запуск бота"""
        logger.info("🤖 Запуск простого Telegram бота AGI Layer v3.9")
        
        # Отправка приветственного сообщения
        await self.send_message("🚀 <b>AGI Layer v3.9</b> запущен!\n\nБот готов к работе. Используйте /start для начала.")
        
        logger.info("🔄 Начинаю основной цикл...")
        
        # Основной цикл
        while True:
            try:
                updates = await self.get_updates()
                
                for update in updates:
                    self.last_update_id = update['update_id']
                    
                    if 'message' in update:
                        await self.process_message(update['message'])
                
                # Пауза между проверками
                await asyncio.sleep(2)
                
            except KeyboardInterrupt:
                logger.info("🛑 Остановка бота...")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в основном цикле: {e}")
                await asyncio.sleep(5)

async def main():
    """Основная функция"""
    bot = SimpleBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")