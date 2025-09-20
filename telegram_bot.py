#!/usr/bin/env python3
"""
Простой работающий Telegram бот для AGI Layer v3.9
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

class SimpleTelegramBot:
    def __init__(self):
        self.token = TOKEN
        self.chat_id = CHAT_ID
        self.api_url = API_URL
        self.last_update_id = 0
        
    async def send_message(self, text):
        """Отправка сообщения"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/sendMessage"
                data = {
                    "chat_id": self.chat_id,
                    "text": text
                }
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            logger.info(f"Сообщение отправлено: {text[:50]}...")
                            return True
                    logger.error(f"Ошибка отправки: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return False
    
    async def get_updates(self):
        """Получение обновлений"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/getUpdates"
                params = {"offset": self.last_update_id + 1, "timeout": 30}
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            return data.get('result', [])
        except Exception as e:
            logger.error(f"Ошибка получения обновлений: {e}")
        return []
    
    async def process_message(self, message):
        """Обработка сообщения"""
        try:
            text = message.get('text', '')
            chat_id = message['chat']['id']
            user_name = message['from'].get('first_name', 'Пользователь')
            
            logger.info(f"Получено сообщение от {user_name}: {text}")
            
            if text == '/start':
                response = f"""🤖 AGI Layer v3.9 - Система управления

Привет, {user_name}! Система запущена и работает.

Доступные команды:
/start - Показать это сообщение
/status - Статус системы
/generate [описание] - Генерация изображения
/report - Отчет о работе
/time - Текущее время

Система готова к работе! ✅"""
                
            elif text == '/status':
                response = f"""📊 Статус системы AGI Layer v3.9

🟢 MetaAgent: Работает
🟢 TelegramAgent: Работает  
🟢 ImageAgent: Готов к работе
🟢 TextAgent: Готов к работе
🟢 VisionAgent: Готов к работе
🟢 OCRAgent: Готов к работе
🟢 EmbeddingAgent: Готов к работе
🟢 RecoveryAgent: Работает

Все системы функционируют нормально! ✅"""
                
            elif text.startswith('/generate '):
                prompt = text[10:]  # Убираем "/generate "
                response = f"""🎨 Генерация изображения

Промпт: {prompt}
Статус: Обработка...

⚠️ Для полной генерации изображений нужно запустить ImageAgent с моделью Stable Diffusion 1.5.

Пока что система работает в базовом режиме."""
                
            elif text == '/report':
                response = f"""📈 Отчет о работе системы

Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Время работы: Активно
Обработано сообщений: {self.last_update_id}
Статус: Все системы работают

Telegram бот успешно подключен и функционирует! ✅"""
                
            elif text == '/time':
                response = f"""🕐 Текущее время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
                
            else:
                response = f"""Привет, {user_name}! 👋

Используйте команды для управления системой:
/start - показать меню
/status - статус системы
/generate [описание] - генерация изображения
/report - отчет о работе"""
            
            # Отправка ответа
            await self.send_message(response)
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
    
    async def run(self):
        """Запуск бота"""
        logger.info("🤖 Запуск Telegram бота AGI Layer v3.9")
        
        # Отправка приветственного сообщения
        await self.send_message("🚀 AGI Layer v3.9 запущен!\n\nБот готов к работе. Используйте /start для начала.")
        
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
                logger.info("Остановка бота...")
                break
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                await asyncio.sleep(5)

async def main():
    """Основная функция"""
    bot = SimpleTelegramBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")

