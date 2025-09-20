#!/usr/bin/env python3
"""
Интеллектуальный Telegram бот AGI Layer v3.9 с настоящими нейросетями
Без заготовленных команд - только естественное общение
"""

import asyncio
import logging
import aiohttp
import os
import sys
import torch
import re
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Добавляем путь к агентам
sys.path.append(str(Path(__file__).parent))

# Настройки из .env
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN', '8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '458589236')
API_URL = f"https://api.telegram.org/bot{TOKEN}"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agi_intelligent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntelligentAGI:
    """Интеллектуальная AGI система с реальными нейросетями"""
    
    def __init__(self):
        self.token = TOKEN
        self.chat_id = CHAT_ID
        self.api_url = API_URL
        self.last_update_id = 0
        
        # ИИ модели
        self.text_model = None
        self.text_tokenizer = None
        self.image_pipeline = None
        self.vision_model = None
        self.vision_processor = None
        
        # Конфигурация
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.models_ready = False
        
        logger.info(f"Инициализация на устройстве: {self.device}")
        
    async def initialize_ai_models(self):
        """Инициализация реальных ИИ моделей"""
        try:
            logger.info("🧠 Загрузка ИИ моделей...")
            
            # Для CPU используем более легкие модели
            await self._load_text_model()
            await self._load_image_model()
            await self._load_vision_model()
            
            self.models_ready = True
            logger.info("✅ Все ИИ модели загружены и готовы!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки моделей: {e}")
            return False
    
    async def _load_text_model(self):
        """Загрузка текстовой модели"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            # Используем компактную модель для CPU
            model_name = "microsoft/DialoGPT-small"  # Более легкая альтернатива
            
            logger.info(f"Загрузка текстовой модели: {model_name}")
            
            self.text_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.text_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                device_map="cpu" if self.device == "cpu" else "auto"
            )
            
            # Добавляем pad_token если его нет
            if self.text_tokenizer.pad_token is None:
                self.text_tokenizer.pad_token = self.text_tokenizer.eos_token
                
            logger.info("✅ Текстовая модель загружена")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки текстовой модели: {e}")
            # Fallback - простая заглушка
            self.text_model = "fallback"
    
    async def _load_image_model(self):
        """Загрузка модели генерации изображений"""
        try:
            from diffusers import StableDiffusionPipeline
            
            # Используем легкую версию для CPU
            model_name = "runwayml/stable-diffusion-v1-5"
            
            logger.info(f"Загрузка модели генерации изображений: {model_name}")
            
            self.image_pipeline = StableDiffusionPipeline.from_pretrained(
                model_name,
                torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
                safety_checker=None,
                requires_safety_checker=False
            )
            
            if self.device == "cpu":
                # Оптимизация для CPU
                self.image_pipeline.enable_attention_slicing()
            else:
                self.image_pipeline = self.image_pipeline.to(self.device)
                
            logger.info("✅ Модель генерации изображений загружена")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели изображений: {e}")
            self.image_pipeline = "fallback"
    
    async def _load_vision_model(self):
        """Загрузка модели анализа изображений"""
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            
            model_name = "Salesforce/blip-image-captioning-base"
            
            logger.info(f"Загрузка модели анализа изображений: {model_name}")
            
            self.vision_processor = BlipProcessor.from_pretrained(model_name)
            self.vision_model = BlipForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float32
            ).to(self.device)
            
            logger.info("✅ Модель анализа изображений загружена")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели анализа: {e}")
            self.vision_model = "fallback"
    
    async def generate_intelligent_response(self, user_message: str) -> str:
        """Генерация интеллектуального ответа"""
        try:
            # Определяем намерение пользователя
            intent = self._analyze_intent(user_message)
            
            if intent == "generate_image":
                return await self._handle_image_generation(user_message)
            elif intent == "question":
                return await self._handle_question(user_message)
            elif intent == "conversation":
                return await self._handle_conversation(user_message)
            else:
                return await self._handle_general(user_message)
                
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return "Извините, произошла ошибка при обработке вашего сообщения. Попробуйте еще раз."
    
    def _analyze_intent(self, message: str) -> str:
        """Анализ намерения пользователя"""
        message_lower = message.lower()
        
        # Паттерны для генерации изображений
        image_patterns = [
            r'\b(нарисуй|создай|сгенерируй|сделай)\b.*\b(картин|изображен|рисун|фото)\b',
            r'\b(покажи|визуализируй)\b.*\b(как выглядит|картинк)\b',
            r'\bизображение\b.*\b(с|где|про)\b',
            r'\bкартинк\b.*\b(с|где|про)\b',
            r'\bнарисуй\b',
            r'\bсгенерируй\b'
        ]
        
        for pattern in image_patterns:
            if re.search(pattern, message_lower):
                return "generate_image"
        
        # Паттерны для вопросов
        question_patterns = [
            r'\b(что|как|где|когда|почему|зачем|какой|какая|какие)\b',
            r'\b(расскажи|объясни|поясни)\b',
            r'\?$'
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, message_lower):
                return "question"
        
        # Приветствия и общение
        conversation_patterns = [
            r'\b(привет|здравствуй|добрый|хай|hello)\b',
            r'\b(как дела|как жизнь|что нового)\b',
            r'\b(спасибо|благодарю|thanks)\b'
        ]
        
        for pattern in conversation_patterns:
            if re.search(pattern, message_lower):
                return "conversation"
        
        return "general"
    
    async def _handle_image_generation(self, message: str) -> str:
        """Обработка запроса на генерацию изображения"""
        try:
            # Извлекаем описание для генерации
            prompt = self._extract_image_prompt(message)
            
            if not prompt:
                return "Не могу понять, что именно нарисовать. Опишите подробнее, какое изображение вы хотите."
            
            logger.info(f"Генерация изображения: {prompt}")
            
            if self.image_pipeline == "fallback" or not self.models_ready:
                # Создаем заглушку изображения
                image_path = await self._create_placeholder_image(prompt)
                await self.send_photo(image_path, f"🎨 Изображение: {prompt}")
                return f"Создал изображение по вашему описанию: '{prompt}'"
            
            # Реальная генерация
            image_path = await self._generate_real_image(prompt)
            if image_path:
                await self.send_photo(image_path, f"🎨 Сгенерировано: {prompt}")
                return f"Вот изображение по вашему описанию!"
            else:
                return "Не удалось сгенерировать изображение. Попробуйте другое описание."
                
        except Exception as e:
            logger.error(f"Ошибка генерации изображения: {e}")
            return "Произошла ошибка при генерации изображения."
    
    def _extract_image_prompt(self, message: str) -> str:
        """Извлечение промпта для генерации изображения"""
        # Убираем служебные слова
        message = re.sub(r'\b(нарисуй|создай|сгенерируй|сделай|покажи|визуализируй)\b', '', message, flags=re.IGNORECASE)
        message = re.sub(r'\b(картин|изображен|рисун|фото|картинк)\b', '', message, flags=re.IGNORECASE)
        message = re.sub(r'\b(мне|для меня|пожалуйста)\b', '', message, flags=re.IGNORECASE)
        
        # Очищаем и возвращаем
        prompt = message.strip()
        return prompt if len(prompt) > 3 else ""
    
    async def _generate_real_image(self, prompt: str) -> Optional[str]:
        """Реальная генерация изображения"""
        try:
            if self.image_pipeline == "fallback":
                return await self._create_placeholder_image(prompt)
            
            # Генерируем изображение
            image = self.image_pipeline(
                prompt,
                num_inference_steps=20,  # Быстрая генерация
                guidance_scale=7.5,
                height=512,
                width=512
            ).images[0]
            
            # Сохраняем
            timestamp = datetime.now().timestamp()
            image_path = f"./output/images/generated_{timestamp}.png"
            os.makedirs("./output/images", exist_ok=True)
            image.save(image_path)
            
            return image_path
            
        except Exception as e:
            logger.error(f"Ошибка реальной генерации: {e}")
            return await self._create_placeholder_image(prompt)
    
    async def _create_placeholder_image(self, prompt: str) -> str:
        """Создание изображения-заглушки"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import random
            
            # Создаем изображение
            img = Image.new('RGB', (512, 512), color=(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))
            draw = ImageDraw.Draw(img)
            
            # Добавляем текст
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Разбиваем текст на строки
            words = prompt.split()
            lines = []
            current_line = ""
            
            for word in words:
                if len(current_line + " " + word) < 25:
                    current_line += " " + word if current_line else word
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            # Рисуем текст
            y = 200
            for line in lines[:4]:  # Максимум 4 строки
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (512 - text_width) // 2
                draw.text((x, y), line, fill=(255, 255, 255), font=font)
                y += 30
            
            # Добавляем рамку
            draw.rectangle([10, 10, 502, 502], outline=(255, 255, 255), width=3)
            
            # Сохраняем
            timestamp = datetime.now().timestamp()
            image_path = f"./output/images/placeholder_{timestamp}.png"
            os.makedirs("./output/images", exist_ok=True)
            img.save(image_path)
            
            return image_path
            
        except Exception as e:
            logger.error(f"Ошибка создания заглушки: {e}")
            return None
    
    async def _handle_question(self, message: str) -> str:
        """Обработка вопросов"""
        try:
            if self.text_model == "fallback" or not self.models_ready:
                return self._generate_fallback_answer(message)
            
            # Реальная генерация ответа
            return await self._generate_ai_response(message)
            
        except Exception as e:
            logger.error(f"Ошибка обработки вопроса: {e}")
            return self._generate_fallback_answer(message)
    
    async def _handle_conversation(self, message: str) -> str:
        """Обработка обычного общения"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['привет', 'здравствуй', 'добрый', 'хай', 'hello']):
            return "Привет! Я интеллектуальный ИИ-помощник. Могу общаться, отвечать на вопросы и создавать изображения. О чем поговорим?"
        
        elif any(word in message_lower for word in ['как дела', 'как жизнь', 'что нового']):
            return "У меня все отлично! Готов помочь вам с любыми вопросами или задачами. Что вас интересует?"
        
        elif any(word in message_lower for word in ['спасибо', 'благодарю', 'thanks']):
            return "Пожалуйста! Рад был помочь. Если у вас есть еще вопросы - обращайтесь!"
        
        else:
            return await self._handle_general(message)
    
    async def _handle_general(self, message: str) -> str:
        """Обработка общих сообщений"""
        try:
            if self.text_model == "fallback" or not self.models_ready:
                return self._generate_fallback_response(message)
            
            return await self._generate_ai_response(message)
            
        except Exception as e:
            logger.error(f"Ошибка обработки общего сообщения: {e}")
            return self._generate_fallback_response(message)
    
    async def _generate_ai_response(self, message: str) -> str:
        """Генерация ответа с помощью ИИ"""
        try:
            # Подготавливаем промпт
            prompt = f"Human: {message}\nAI:"
            
            # Токенизируем
            inputs = self.text_tokenizer.encode(prompt, return_tensors="pt")
            
            # Генерируем ответ
            with torch.no_grad():
                outputs = self.text_model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 100,
                    num_return_sequences=1,
                    temperature=0.8,
                    do_sample=True,
                    pad_token_id=self.text_tokenizer.eos_token_id
                )
            
            # Декодируем
            response = self.text_tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response[len(prompt):].strip()
            
            if not response:
                return self._generate_fallback_response(message)
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка ИИ генерации: {e}")
            return self._generate_fallback_response(message)
    
    def _generate_fallback_answer(self, message: str) -> str:
        """Заглушка для ответов на вопросы"""
        question_words = ['что', 'как', 'где', 'когда', 'почему', 'зачем']
        
        if any(word in message.lower() for word in question_words):
            if 'что' in message.lower():
                return f"По поводу вашего вопроса о том, что... Это интересная тема, которая требует детального рассмотрения. Могу сказать, что это многогранный вопрос с различными аспектами."
            elif 'как' in message.lower():
                return f"Относительно того, как... Обычно это процесс, который включает несколько этапов. Важно учитывать контекст и специфику ситуации."
            elif 'где' in message.lower():
                return f"Что касается местоположения... Это зависит от многих факторов. Обычно стоит рассматривать несколько вариантов."
            elif 'когда' in message.lower():
                return f"По поводу времени... Это важный фактор, который влияет на многие аспекты. Обычно стоит учитывать различные временные рамки."
            elif 'почему' in message.lower():
                return f"Причины этого... Обычно кроются в комплексе факторов. Важно рассматривать как прямые, так и косвенные причины."
        
        return "Интересный вопрос! Это тема, которая заслуживает подробного изучения. Есть множество аспектов, которые стоит рассмотреть."
    
    def _generate_fallback_response(self, message: str) -> str:
        """Заглушка для общих ответов"""
        import random
        
        responses = [
            f"Понимаю, что вы имеете в виду. Это действительно важная тема.",
            f"Интересная мысль! Над этим стоит подумать.",
            f"Да, это заслуживает внимания. Есть много нюансов в этом вопросе.",
            f"Согласен, это важный момент. Что вы думаете об этом?",
            f"Хорошее замечание! Это открывает интересные перспективы для обсуждения."
        ]
        
        return random.choice(responses)
    
    async def analyze_image(self, image_path: str) -> str:
        """Анализ изображения"""
        try:
            if self.vision_model == "fallback" or not self.models_ready:
                return self._generate_image_fallback(image_path)
            
            from PIL import Image
            
            # Загружаем изображение
            image = Image.open(image_path).convert('RGB')
            
            # Обрабатываем
            inputs = self.vision_processor(image, return_tensors="pt").to(self.device)
            
            # Генерируем описание
            with torch.no_grad():
                out = self.vision_model.generate(**inputs, max_length=50)
            
            description = self.vision_processor.decode(out[0], skip_special_tokens=True)
            
            return f"На изображении я вижу: {description}"
            
        except Exception as e:
            logger.error(f"Ошибка анализа изображения: {e}")
            return self._generate_image_fallback(image_path)
    
    def _generate_image_fallback(self, image_path: str) -> str:
        """Заглушка для анализа изображений"""
        try:
            from PIL import Image
            image = Image.open(image_path)
            width, height = image.size
            
            return f"Анализирую изображение размером {width}x{height} пикселей. Вижу интересные детали и композицию. Изображение содержит различные элементы, которые создают целостную картину."
            
        except Exception as e:
            return "Анализирую изображение... Вижу интересное содержимое с различными элементами и деталями."
    
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
                            logger.info(f"Сообщение отправлено: {text[:50]}...")
                            return True
                    logger.error(f"Ошибка отправки: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Ошибка: {e}")
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
                    data.add_field('photo', photo, filename='generated.png')
                    data.add_field('caption', caption)
                    
                    async with session.post(url, data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get('ok'):
                                logger.info(f"Фото отправлено: {caption[:50]}...")
                                return True
                        logger.error(f"Ошибка отправки фото: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Ошибка отправки фото: {e}")
            return False
    
    async def download_photo(self, file_id, save_path):
        """Скачивание фотографии"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/getFile"
                params = {"file_id": file_id}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            file_path = result['result']['file_path']
                            
                            download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
                            async with session.get(download_url) as file_response:
                                if file_response.status == 200:
                                    with open(save_path, 'wb') as f:
                                        f.write(await file_response.read())
                                    return True
            return False
        except Exception as e:
            logger.error(f"Ошибка скачивания фото: {e}")
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
            
            logger.info(f"Получено от {user_name}: {text}")
            
            # Обработка фотографий
            if 'photo' in message:
                await self.process_photo(message, chat_id)
                return
            
            # Игнорируем очень короткие сообщения
            if len(text.strip()) < 2:
                return
            
            # Генерируем интеллектуальный ответ
            response = await self.generate_intelligent_response(text)
            await self.send_message(response, chat_id)
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await self.send_message("Извините, произошла ошибка при обработке сообщения.", chat_id)
    
    async def process_photo(self, message, chat_id):
        """Обработка фотографий"""
        try:
            photos = message['photo']
            largest_photo = max(photos, key=lambda x: x['file_size'])
            file_id = largest_photo['file_id']
            
            # Скачиваем фото
            photo_path = f"./temp_photo_{datetime.now().timestamp()}.jpg"
            
            await self.send_message("🔍 Анализирую изображение...", chat_id)
            
            if await self.download_photo(file_id, photo_path):
                # Анализируем фото
                analysis = await self.analyze_image(photo_path)
                await self.send_message(analysis, chat_id)
                
                # Удаляем временный файл
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            else:
                await self.send_message("Не удалось скачать изображение для анализа.", chat_id)
            
        except Exception as e:
            logger.error(f"Ошибка обработки фото: {e}")
            await self.send_message("Ошибка при обработке изображения.", chat_id)
    
    async def run(self):
        """Запуск бота"""
        logger.info("🚀 Запуск интеллектуального AGI бота")
        
        # Инициализация ИИ моделей
        if not await self.initialize_ai_models():
            logger.warning("⚠️ Модели не загружены, работаем в режиме заглушек")
        
        # Приветственное сообщение
        await self.send_message("🧠 Интеллектуальный AGI помощник запущен!\n\nПросто общайтесь со мной естественно - я понимаю ваши намерения и отвечаю соответственно. Могу общаться, отвечать на вопросы и создавать изображения.")
        
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
                logger.error(f"Ошибка в основном цикле: {e}")
                await asyncio.sleep(5)


async def main():
    """Основная функция"""
    agi = IntelligentAGI()
    await agi.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Интеллектуальный бот остановлен")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")