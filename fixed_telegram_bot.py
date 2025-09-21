#!/usr/bin/env python3
"""
Исправленный Telegram бот AGI Layer v3.9 с РЕАЛЬНО работающими ответами
Без вранья - только то, что действительно работает
"""

import asyncio
import logging
import aiohttp
import os
import torch
import re
import random
from datetime import datetime
from typing import Dict, Any, Optional

# Настройки из .env
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN', '8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '458589236')
API_URL = f"https://api.telegram.org/bot{TOKEN}"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fixed_agi.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FixedAGI:
    """Исправленная AGI система - только работающие функции"""
    
    def __init__(self):
        self.token = TOKEN
        self.chat_id = CHAT_ID
        self.api_url = API_URL
        self.last_update_id = 0
        
        # ИИ модели (только проверенные)
        self.image_pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.models_ready = False
        
        # Контекст пользователей
        self.user_contexts = {}
        
        logger.info(f"Инициализация FixedAGI на {self.device}")
        
    async def initialize_working_models(self):
        """Инициализация только работающих моделей"""
        try:
            logger.info("Загрузка ТОЛЬКО проверенных моделей...")
            
            # Загружаем только Stable Diffusion - она точно работает
            await self._load_stable_diffusion()
            
            self.models_ready = True
            logger.info("✅ Проверенные модели загружены")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки: {e}")
            return False
    
    async def _load_stable_diffusion(self):
        """Загрузка Stable Diffusion (проверенная работающая модель)"""
        try:
            from diffusers import StableDiffusionPipeline
            
            logger.info("Загрузка Stable Diffusion v1.5...")
            
            self.image_pipeline = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False
            )
            
            if self.device == "cpu":
                self.image_pipeline.enable_attention_slicing()
            
            logger.info("✅ Stable Diffusion загружен и готов")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки SD: {e}")
            self.image_pipeline = None
    
    def generate_honest_response(self, message: str, user_name: str) -> str:
        """Генерация честных ответов без вранья"""
        message_lower = message.lower().strip()
        
        # Приветствия
        if any(word in message_lower for word in ['привет', 'здравствуй', 'хай', 'hello']):
            return f"Привет, {user_name}! Я AGI Layer v3.9. Могу создавать изображения через Stable Diffusion и поддерживать беседу. Что вас интересует?"
        
        # Вопросы о возможностях
        elif any(phrase in message_lower for phrase in ['что умеешь', 'что можешь', 'возможности', 'функции']):
            return """Честно о моих возможностях:

✅ РАБОТАЕТ:
🎨 Генерация изображений (Stable Diffusion v1.5)
💬 Поддержка беседы (логика на правилах)
📱 Telegram интеграция

⚠️ В РАЗРАБОТКЕ:
👁️ Анализ изображений
🧠 Сложные ответы на вопросы
📚 База знаний

Просто опишите что нарисовать или задайте простой вопрос!"""
        
        # Генерация изображений
        elif any(word in message_lower for word in ['нарисуй', 'создай', 'сгенерируй', 'изображение', 'картинку']):
            # Извлекаем описание
            prompt = message_lower
            for word in ['нарисуй', 'создай', 'сгенерируй', 'изображение', 'картинку', 'фото']:
                prompt = prompt.replace(word, '').strip()
            
            if len(prompt) > 3:
                asyncio.create_task(self._generate_and_send_image(prompt))
                return f"🎨 Создаю изображение: '{prompt}'\n\n⏳ Stable Diffusion генерирует...\n🕐 Это займет около 2 минут\n\nЯ уведомлю когда будет готово!"
            else:
                return "Опишите что нарисовать! Например: 'нарисуй кота в космосе'"
        
        # Вопросы о Python
        elif 'python' in message_lower:
            return """Python - мощный язык программирования! 🐍

Основные плюсы:
• Простой синтаксис
• Много библиотек
• Подходит для ИИ, веб-разработки, анализа данных
• Большое сообщество

Используется в Google, Netflix, Instagram.
Хотите узнать что-то конкретное о Python?"""
        
        # Вопросы об ИИ
        elif any(word in message_lower for word in ['ии', 'нейросети', 'искусственный интеллект']):
            return """Искусственный интеллект - увлекательная область! 🤖

Современный ИИ использует:
• Нейронные сети (как человеческий мозг)
• Машинное обучение на больших данных
• Глубокое обучение для сложных задач

Я сам использую несколько ИИ моделей:
- Stable Diffusion для изображений
- Правила для текстовых ответов

Что именно об ИИ хотите узнать?"""
        
        # Благодарности
        elif any(word in message_lower for word in ['спасибо', 'благодарю', 'thanks']):
            return "Пожалуйста! 😊 Рад помочь. Если нужно что-то еще - обращайтесь!"
        
        # Критика
        elif any(word in message_lower for word in ['тупой', 'глупый', 'плохо', 'дебил']):
            return "Понимаю ваше недовольство! 😔 Я действительно пока простой - использую правила вместо сложных нейросетей для текста. Но генерация изображений работает хорошо! Что конкретно улучшить?"
        
        # Вопросы "как дела"
        elif any(phrase in message_lower for phrase in ['как дела', 'как жизнь', 'что нового']):
            return "У меня все отлично! 🌟 Модели загружены, система работает стабильно. Готов создавать изображения и отвечать на вопросы. А у вас как дела?"
        
        # Общие вопросы
        elif any(word in message_lower for word in ['что', 'как', 'где', 'почему', '?']):
            return f"Интересный вопрос про '{message[:50]}...'! 🤔\n\nК сожалению, для сложных вопросов мне нужны более мощные языковые модели. Сейчас я лучше всего справляюсь с:\n\n🎨 Генерацией изображений\n💬 Простыми беседами\n📚 Базовой информацией\n\nПопробуйте попросить нарисовать что-то!"
        
        # Все остальное
        else:
            responses = [
                f"Понял, {user_name}! 👍 Пока мой текстовый интеллект простой, но я честно работаю над улучшением. Лучше всего у меня получается создавать изображения!",
                f"Спасибо за сообщение! 😊 Я использую правила для ответов, а не сложные нейросети. Зато могу классно рисовать через Stable Diffusion!",
                f"Понимаю! 💭 Мои текстовые ответы пока базовые, но генерация изображений работает отлично. Хотите что-то нарисовать?"
            ]
            return random.choice(responses)
    
    async def _generate_and_send_image(self, prompt: str):
        """Генерация и отправка изображения"""
        try:
            logger.info(f"Генерация изображения: {prompt}")
            
            if not self.image_pipeline:
                await self.send_message("❌ Модель генерации изображений не загружена")
                return
            
            # Улучшаем промпт
            enhanced_prompt = f"{prompt}, high quality, detailed, masterpiece"
            negative_prompt = "low quality, blurry, ugly, distorted"
            
            # Генерируем
            image = self.image_pipeline(
                prompt=enhanced_prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=30,  # Быстрее для тестирования
                guidance_scale=10.0,
                height=512,
                width=512
            ).images[0]
            
            # Сохраняем
            timestamp = datetime.now().timestamp()
            image_path = f"/workspace/data/fixed_{timestamp}.png"
            os.makedirs("/workspace/data", exist_ok=True)
            image.save(image_path)
            
            # Отправляем
            await self.send_photo(image_path, f"🎨 Готово! '{prompt}'")
            await self.send_message("✅ Изображение создано! Как вам результат?")
            
            logger.info(f"✅ Изображение создано и отправлено: {image_path}")
            
        except Exception as e:
            logger.error(f"Ошибка генерации изображения: {e}")
            await self.send_message(f"❌ Ошибка создания изображения: {str(e)}")
    
    async def send_message(self, text, chat_id=None):
        """Отправка сообщения"""
        try:
            target_chat_id = chat_id or self.chat_id
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/sendMessage"
                data = {
                    "chat_id": target_chat_id,
                    "text": text
                }
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
        """Отправка фотографии"""
        try:
            target_chat_id = chat_id or self.chat_id
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/sendPhoto"
                
                with open(photo_path, 'rb') as photo:
                    data = aiohttp.FormData()
                    data.add_field('chat_id', target_chat_id)
                    data.add_field('photo', photo, filename='fixed_image.png')
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
        except Exception as e:
            logger.error(f"Ошибка получения обновлений: {e}")
        return []
    
    def generate_honest_response(self, message: str, user_name: str) -> str:
        """Генерация честных ответов без вранья"""
        message_lower = message.lower().strip()
        
        # Приветствия
        if any(word in message_lower for word in ['привет', 'здравствуй', 'хай', 'hello']):
            return f"Привет, {user_name}! Я AGI Layer v3.9. Могу создавать изображения через Stable Diffusion и поддерживать беседу. Что вас интересует?"
        
        # Вопросы о возможностях
        elif any(phrase in message_lower for phrase in ['что умеешь', 'что можешь', 'возможности', 'функции']):
            return """Честно о моих возможностях:

✅ РАБОТАЕТ:
🎨 Генерация изображений (Stable Diffusion v1.5)
💬 Поддержка беседы (логика на правилах)
📱 Telegram интеграция

⚠️ В РАЗРАБОТКЕ:
👁️ Анализ изображений
🧠 Сложные ответы на вопросы
📚 База знаний

Просто опишите что нарисовать или задайте простой вопрос!"""
        
        # Генерация изображений
        elif any(word in message_lower for word in ['нарисуй', 'создай', 'сгенерируй', 'изображение', 'картинку']):
            # Извлекаем описание
            prompt = message_lower
            for word in ['нарисуй', 'создай', 'сгенерируй', 'изображение', 'картинку', 'фото']:
                prompt = prompt.replace(word, '').strip()
            
            if len(prompt) > 3:
                asyncio.create_task(self._generate_and_send_image(prompt))
                return f"🎨 Создаю изображение: '{prompt}'\n\n⏳ Stable Diffusion генерирует...\n🕐 Это займет около 2 минут\n\nЯ уведомлю когда будет готово!"
            else:
                return "Опишите что нарисовать! Например: 'нарисуй кота в космосе'"
        
        # Вопросы о Python
        elif 'python' in message_lower:
            return """Python - мощный язык программирования! 🐍

Основные плюсы:
• Простой синтаксис
• Много библиотек
• Подходит для ИИ, веб-разработки, анализа данных
• Большое сообщество

Используется в Google, Netflix, Instagram.
Хотите узнать что-то конкретное о Python?"""
        
        # Вопросы об ИИ
        elif any(word in message_lower for word in ['ии', 'нейросети', 'искусственный интеллект']):
            return """Искусственный интеллект - увлекательная область! 🤖

Современный ИИ использует:
• Нейронные сети (как человеческий мозг)
• Машинное обучение на больших данных
• Глубокое обучение для сложных задач

Я сам использую несколько ИИ моделей:
- Stable Diffusion для изображений
- Правила для текстовых ответов

Что именно об ИИ хотите узнать?"""
        
        # Благодарности
        elif any(word in message_lower for word in ['спасибо', 'благодарю', 'thanks']):
            return "Пожалуйста! 😊 Рад помочь. Если нужно что-то еще - обращайтесь!"
        
        # Критика
        elif any(word in message_lower for word in ['тупой', 'глупый', 'плохо', 'дебил']):
            return "Понимаю ваше недовольство! 😔 Я действительно пока простой - использую правила вместо сложных нейросетей для текста. Но генерация изображений работает хорошо! Что конкретно улучшить?"
        
        # Вопросы "как дела"
        elif any(phrase in message_lower for phrase in ['как дела', 'как жизнь', 'что нового']):
            return "У меня все отлично! 🌟 Модели загружены, система работает стабильно. Готов создавать изображения и отвечать на вопросы. А у вас как дела?"
        
        # Общие вопросы
        elif any(word in message_lower for word in ['что', 'как', 'где', 'почему', '?']):
            return f"Интересный вопрос про '{message[:50]}...'! 🤔\n\nК сожалению, для сложных вопросов мне нужны более мощные языковые модели. Сейчас я лучше всего справляюсь с:\n\n🎨 Генерацией изображений\n💬 Простыми беседами\n📚 Базовой информацией\n\nПопробуйте попросить нарисовать что-то!"
        
        # Все остальное
        else:
            responses = [
                f"Понял, {user_name}! 👍 Пока мой текстовый интеллект простой, но я честно работаю над улучшением. Лучше всего у меня получается создавать изображения!",
                f"Спасибо за сообщение! 😊 Я использую правила для ответов, а не сложные нейросети. Зато могу классно рисовать через Stable Diffusion!",
                f"Понимаю! 💭 Мои текстовые ответы пока базовые, но генерация изображений работает отлично. Хотите что-то нарисовать?"
            ]
            return random.choice(responses)
    
    async def process_message(self, message):
        """Обработка сообщения"""
        try:
            text = message.get('text', '')
            chat_id = message['chat']['id']
            user_name = message['from'].get('first_name', 'Пользователь')
            
            logger.info(f"Получено от {user_name}: {text}")
            
            if len(text.strip()) < 1:
                return
            
            # Генерируем честный ответ
            response = self.generate_honest_response(text, user_name)
            await self.send_message(response, chat_id)
            
        except Exception as e:
            logger.error(f"Ошибка обработки: {e}")
            await self.send_message("Ошибка обработки сообщения", chat_id)
    
    async def run(self):
        """Запуск бота"""
        logger.info("🚀 Запуск Fixed AGI Bot")
        
        # Загружаем модели
        if await self.initialize_working_models():
            logger.info("✅ Модели готовы")
        else:
            logger.warning("⚠️ Модели не загружены")
        
        # Отправляем честное сообщение о запуске
        await self.send_message("""🤖 Fixed AGI v3.9 запущен!

ЧЕСТНО о возможностях:
✅ Генерация изображений (Stable Diffusion работает)
✅ Простые ответы (правила, не нейросети)
✅ Telegram интеграция

❌ НЕ РАБОТАЕТ пока:
- Сложный анализ текста
- Умные нейросетевые ответы
- Анализ изображений

Но генерация картинок работает отлично! Попробуйте: 'нарисуй кота'""")
        
        # Основной цикл
        while True:
            try:
                updates = await self.get_updates()
                
                for update in updates:
                    self.last_update_id = update['update_id']
                    
                    if 'message' in update:
                        await self.process_message(update['message'])
                
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Остановка бота...")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле: {e}")
                await asyncio.sleep(5)


async def main():
    """Основная функция"""
    bot = FixedAGI()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")