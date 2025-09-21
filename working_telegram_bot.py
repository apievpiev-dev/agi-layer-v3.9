#!/usr/bin/env python3
"""
РАБОЧИЙ Telegram бот AGI Layer v3.9
Простой, честный, без вранья - только то что реально работает
"""

import asyncio
import logging
import aiohttp
import os
import torch
import random
from datetime import datetime

# Настройки
TOKEN = '8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw'
CHAT_ID = '458589236'
API_URL = f"https://api.telegram.org/bot{TOKEN}"

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkingBot:
    """Простой рабочий бот"""
    
    def __init__(self):
        self.token = TOKEN
        self.chat_id = CHAT_ID
        self.api_url = API_URL
        self.last_update_id = 0
        
        # Только Stable Diffusion - она точно работает
        self.image_pipeline = None
        self.device = "cpu"
        
    async def load_image_model(self):
        """Загрузка модели генерации (единственное что точно работает)"""
        try:
            from diffusers import StableDiffusionPipeline
            
            logger.info("Загрузка Stable Diffusion...")
            
            self.image_pipeline = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False
            )
            
            self.image_pipeline.enable_attention_slicing()
            
            logger.info("✅ Stable Diffusion загружен")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки SD: {e}")
            return False
    
    def get_response(self, message: str, user_name: str) -> str:
        """Простые честные ответы"""
        msg = message.lower()
        
        if 'привет' in msg or 'hello' in msg:
            return f"Привет, {user_name}! Я простой бот AGI Layer v3.9. Умею рисовать картинки через Stable Diffusion. Что нарисовать?"
        
        elif 'что умеешь' in msg or 'возможности' in msg:
            return """Честно о том, что работает:

✅ Генерация изображений (Stable Diffusion v1.5)
✅ Простые ответы
✅ Получение сообщений

❌ НЕ работает:
- Умный анализ текста
- Сложные нейросетевые ответы
- Анализ фото

Попробуйте: 'нарисуй кота в космосе'"""
        
        elif any(word in msg for word in ['нарисуй', 'создай', 'сгенерируй']):
            # Извлекаем что рисовать
            prompt = msg
            for word in ['нарисуй', 'создай', 'сгенерируй', 'картинку', 'изображение']:
                prompt = prompt.replace(word, '').strip()
            
            if len(prompt) > 2:
                # Запускаем генерацию в фоне
                asyncio.create_task(self._generate_image(prompt))
                return f"🎨 Рисую: '{prompt}'\n⏳ Подождите 2 минуты..."
            else:
                return "Что именно нарисовать? Опишите подробнее!"
        
        elif 'python' in msg:
            return "Python - отличный язык программирования! Простой, мощный, популярный. Используется для ИИ, веб-разработки, анализа данных."
        
        elif any(word in msg for word in ['тупой', 'глупый', 'дебил']):
            return "Да, вы правы! 😅 Мои текстовые ответы пока простые. Но генерация изображений работает хорошо! Попробуйте попросить что-то нарисовать."
        
        elif 'спасибо' in msg:
            return "Пожалуйста! 😊"
        
        else:
            responses = [
                f"Понял, {user_name}! Мои ответы пока простые, но я честно работаю. Лучше всего получается рисовать!",
                f"Спасибо за сообщение! Попробуйте попросить нарисовать что-нибудь - это у меня хорошо получается.",
                f"Понимаю! Для сложных вопросов я пока слабоват, но могу создать классную картинку!"
            ]
            return random.choice(responses)
    
    async def _generate_image(self, prompt: str):
        """Генерация изображения"""
        try:
            if not self.image_pipeline:
                await self.send_message("❌ Модель не загружена")
                return
            
            logger.info(f"Генерирую: {prompt}")
            
            # Генерируем
            image = self.image_pipeline(
                prompt=f"{prompt}, high quality, detailed",
                negative_prompt="low quality, blurry",
                num_inference_steps=25,
                guidance_scale=8.0,
                height=512,
                width=512
            ).images[0]
            
            # Сохраняем
            timestamp = datetime.now().timestamp()
            image_path = f"/workspace/data/working_{timestamp}.png"
            os.makedirs("/workspace/data", exist_ok=True)
            image.save(image_path)
            
            # Отправляем
            await self.send_photo(image_path, f"🎨 Готово: '{prompt}'")
            
            logger.info(f"✅ Изображение создано: {image_path}")
            
        except Exception as e:
            logger.error(f"Ошибка генерации: {e}")
            await self.send_message(f"❌ Ошибка создания изображения: {str(e)}")
    
    async def send_message(self, text, chat_id=None):
        """Отправка сообщения"""
        try:
            target_chat_id = chat_id or self.chat_id
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/sendMessage"
                data = {"chat_id": target_chat_id, "text": text}
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            logger.info(f"Отправлено: {text[:50]}...")
                            return True
                    logger.error(f"Ошибка отправки: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Ошибка отправки: {e}")
            return False
    
    async def send_photo(self, photo_path, caption="", chat_id=None):
        """Отправка фото"""
        try:
            target_chat_id = chat_id or self.chat_id
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/sendPhoto"
                
                with open(photo_path, 'rb') as photo:
                    data = aiohttp.FormData()
                    data.add_field('chat_id', target_chat_id)
                    data.add_field('photo', photo, filename='working.png')
                    data.add_field('caption', caption)
                    
                    async with session.post(url, data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get('ok'):
                                logger.info(f"Фото отправлено: {caption[:30]}...")
                                return True
                        logger.error(f"Ошибка отправки фото: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Ошибка отправки фото: {e}")
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
                    else:
                        logger.error(f"Ошибка getUpdates: {response.status}")
        except Exception as e:
            logger.error(f"Ошибка получения обновлений: {e}")
        return []
    
    async def process_message(self, message):
        """Обработка сообщения"""
        try:
            text = message.get('text', '')
            chat_id = message['chat']['id']
            user_name = message['from'].get('first_name', 'Пользователь')
            
            logger.info(f"ПОЛУЧЕНО от {user_name}: '{text}'")
            
            if len(text.strip()) < 1:
                return
            
            # Генерируем ответ
            response = self.get_response(text, user_name)
            
            # Отправляем ответ
            success = await self.send_message(response, chat_id)
            
            if success:
                logger.info(f"ОТВЕТИЛ: {response[:50]}...")
            else:
                logger.error("Не удалось отправить ответ")
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
    
    async def run(self):
        """Запуск бота"""
        logger.info("🚀 Запуск Working Bot")
        
        # Загружаем модель
        if await self.load_image_model():
            logger.info("✅ Модель загружена")
        else:
            logger.warning("⚠️ Модель не загружена")
        
        # Отправляем сообщение о запуске
        await self.send_message("""🤖 Working Bot запущен!

ЧЕСТНО:
✅ Stable Diffusion работает
✅ Простые ответы работают  
✅ Telegram API работает

Попробуйте: 'нарисуй кота' или 'что умеешь'""")
        
        logger.info("🔄 Запуск основного цикла...")
        
        # Основной цикл
        while True:
            try:
                updates = await self.get_updates()
                
                if updates:
                    logger.info(f"Получено {len(updates)} обновлений")
                
                for update in updates:
                    self.last_update_id = update['update_id']
                    logger.info(f"Обрабатываю update {self.last_update_id}")
                    
                    if 'message' in update:
                        await self.process_message(update['message'])
                
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Остановка...")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле: {e}")
                await asyncio.sleep(5)


async def main():
    bot = WorkingBot()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")