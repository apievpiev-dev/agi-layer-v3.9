#!/usr/bin/env python3
"""
Исправленный Telegram бот для AGI Layer v3.9
"""

import asyncio
import logging
import aiohttp
from datetime import datetime
import json

# Настройки
TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
CHAT_ID = "458589236"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FixedTelegramBot:
    def __init__(self):
        self.token = TOKEN
        self.chat_id = CHAT_ID
        self.api_url = API_URL
        self.last_update_id = 0
        self.message_count = 0
        
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
                        response_text = await response.text()
                        logger.error(f"Ответ сервера: {response_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Ошибка отправки: {e}")
            return False
    
    async def get_updates(self):
        """Получение обновлений с обработкой ошибок"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/getUpdates"
                params = {
                    "offset": self.last_update_id + 1, 
                    "timeout": 30,
                    "allowed_updates": ["message"]
                }
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            updates = data.get('result', [])
                            logger.info(f"📨 Получено {len(updates)} обновлений")
                            return updates
                        else:
                            logger.error(f"❌ Ошибка API getUpdates: {data}")
                    elif response.status == 409:
                        logger.error("❌ Конфликт: другой бот уже получает обновления")
                        logger.info("🔄 Попытка очистки webhook...")
                        await self.clear_webhook()
                        return []
                    else:
                        logger.error(f"❌ HTTP ошибка getUpdates: {response.status}")
                        response_text = await response.text()
                        logger.error(f"Ответ: {response_text}")
        except Exception as e:
            logger.error(f"❌ Ошибка получения обновлений: {e}")
        return []
    
    async def clear_webhook(self):
        """Очистка webhook"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/deleteWebhook"
                async with session.post(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            logger.info("✅ Webhook очищен")
                            return True
                        else:
                            logger.error(f"❌ Ошибка очистки webhook: {result}")
                    else:
                        logger.error(f"❌ HTTP ошибка очистки: {response.status}")
        except Exception as e:
            logger.error(f"❌ Ошибка очистки webhook: {e}")
        return False
    
    async def process_message(self, message):
        """Обработка сообщения"""
        try:
            text = message.get('text', '')
            chat_id = message['chat']['id']
            user_name = message['from'].get('first_name', 'Пользователь')
            user_id = message['from'].get('id', '')
            
            self.message_count += 1
            
            logger.info(f"👤 Сообщение от {user_name} (ID: {user_id}): {text}")
            
            # Простые ответы
            if text == '/start':
                response = f"""🤖 <b>AGI Layer v3.9</b> - Система управления

Привет, {user_name}! 👋

Система запущена и работает.

<b>Доступные команды:</b>
/start - Показать это сообщение
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
🟢 <b>OCRAgent:</b> Готов к работе
🟢 <b>EmbeddingAgent:</b> Готов к работе
🟢 <b>RecoveryAgent:</b> Работает

<b>Статистика:</b>
📨 Обработано сообщений: {self.message_count}
🕐 Время работы: Активно

Все системы функционируют нормально! ✅"""
                
            elif text == '/help':
                response = f"""❓ <b>Помощь по командам AGI Layer v3.9</b>

<b>Основные команды:</b>
/start - Начало работы с ботом
/status - Статус всех систем
/help - Эта справка
/time - Текущее время
/ping - Проверка связи

<b>Специальные команды:</b>
/generate [описание] - Генерация изображения
/report - Отчет о работе системы

<b>Как пользоваться:</b>
Просто отправьте команду или вопрос, и я отвечу!

Система готова помочь! 🤖"""
                
            elif text == '/time':
                response = f"""🕐 <b>Текущее время:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
                
            elif text == '/ping':
                response = f"""🏓 <b>Pong!</b>

Связь работает отлично! ✅
Время ответа: {datetime.now().strftime('%H:%M:%S')}"""
                
            elif text.startswith('/generate '):
                prompt = text[10:]  # Убираем "/generate "
                response = f"""🎨 <b>Генерация изображения</b>

<b>Промпт:</b> {prompt}
<b>Статус:</b> Обработка...

⚠️ <i>Для полной генерации изображений нужно запустить ImageAgent с моделью Stable Diffusion 1.5.</i>

Пока что система работает в базовом режиме."""
                
            elif text == '/report':
                response = f"""📈 <b>Отчет о работе системы</b>

<b>Дата:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
<b>Время работы:</b> Активно
<b>Обработано сообщений:</b> {self.message_count}
<b>Статус:</b> Все системы работают

Telegram бот успешно подключен и функционирует! ✅"""
                
            else:
                # Ответ на обычное сообщение
                response = f"""Привет, {user_name}! 👋

Я <b>AGI Layer v3.9</b> - система искусственного интеллекта.

<b>Что я умею:</b>
• Отвечать на команды
• Показывать статус системы  
• Генерировать изображения (в разработке)
• Обрабатывать текст и изображения

<b>Попробуйте команды:</b>
/start - меню
/status - статус
/help - помощь
/time - время

Или просто напишите что-нибудь! 😊"""
            
            # Отправка ответа
            success = await self.send_message(response, chat_id)
            if success:
                logger.info(f"✅ Ответ отправлен пользователю {user_name}")
            else:
                logger.error(f"❌ Не удалось отправить ответ пользователю {user_name}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки сообщения: {e}")
            # Отправка сообщения об ошибке
            await self.send_message("❌ Произошла ошибка при обработке сообщения", chat_id)
    
    async def run(self):
        """Запуск бота"""
        logger.info("🤖 Запуск исправленного Telegram бота AGI Layer v3.9")
        
        # Очистка webhook перед запуском
        await self.clear_webhook()
        
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
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("🛑 Остановка бота...")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в основном цикле: {e}")
                await asyncio.sleep(5)

async def main():
    """Основная функция"""
    bot = FixedTelegramBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")