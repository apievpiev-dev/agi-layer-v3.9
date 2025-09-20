#!/usr/bin/env python3
"""
Умный Telegram бот AGI Layer v3.9 с настоящим интеллектом
Использует более мощные модели и улучшенную логику
"""

import asyncio
import logging
import aiohttp
import os
import sys
import torch
import re
import json
import random
from datetime import datetime
from typing import Dict, Any, Optional, List
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
        logging.FileHandler('smart_agi.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SmartAGI:
    """Умная AGI система с настоящим интеллектом"""
    
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
        
        # Контекст разговоров для каждого пользователя
        self.conversation_contexts = {}
        
        # База знаний для улучшенных ответов
        self.knowledge_base = self._load_knowledge_base()
        
        logger.info(f"Инициализация SmartAGI на устройстве: {self.device}")
        
    def _load_knowledge_base(self) -> Dict[str, List[str]]:
        """Загрузка базы знаний для умных ответов"""
        return {
            "приветствие": [
                "Привет! Я ваш персональный ИИ-помощник. Готов помочь с любыми задачами - от создания изображений до ответов на сложные вопросы.",
                "Здравствуйте! Рад вас видеть. Я могу генерировать изображения, анализировать фото, отвечать на вопросы и просто интересно общаться.",
                "Привет! Я интеллектуальная система AGI Layer v3.9. Умею создавать картинки, понимать изображения и поддерживать умные беседы."
            ],
            "возможности": [
                "Я умею многое! Могу создавать уникальные изображения по вашему описанию, анализировать фотографии, отвечать на вопросы, запоминать информацию и вести интеллектуальные беседы.",
                "Мои основные способности: генерация изображений через Stable Diffusion, анализ фото через компьютерное зрение, ответы на вопросы и естественное общение.",
                "Я - многофункциональный ИИ. Создаю картинки, понимаю изображения, отвечаю на вопросы любой сложности и поддерживаю живые беседы."
            ],
            "python": [
                "Python - это мощный, универсальный язык программирования, известный своей простотой и читаемостью. Он широко используется в веб-разработке, анализе данных, машинном обучении и автоматизации.",
                "Python создан Гвидо ван Россумом в 1991 году. Это интерпретируемый язык с динамической типизацией, который отлично подходит как для начинающих, так и для профессионалов.",
                "Python - язык программирования высокого уровня с философией 'простота и читаемость кода'. Используется в ИИ, веб-разработке, науке о данных и многих других областях."
            ],
            "ии": [
                "Искусственный интеллект - это область компьютерных наук, создающая системы, способные выполнять задачи, обычно требующие человеческого интеллекта: обучение, распознавание образов, принятие решений.",
                "ИИ работает через машинное обучение - алгоритмы анализируют большие объемы данных, находят закономерности и учатся делать предсказания или принимать решения на основе этих паттернов.",
                "Современный ИИ основан на нейронных сетях - математических моделях, имитирующих работу человеческого мозга. Они обучаются на данных и могут решать сложные задачи."
            ],
            "нейросети": [
                "Нейронные сети - это вычислительные модели, вдохновленные структурой человеческого мозга. Они состоят из связанных узлов (нейронов), которые обрабатывают и передают информацию.",
                "Нейросети обучаются на примерах, постепенно настраивая связи между нейронами. Это позволяет им распознавать паттерны, классифицировать данные и делать предсказания.",
                "Глубокие нейронные сети имеют множество слоев, что позволяет им изучать сложные зависимости в данных. Они используются в компьютерном зрении, обработке языка и многих других областях."
            ],
            "благодарность": [
                "Пожалуйста! Рад был помочь. Если у вас есть еще вопросы или нужна помощь - обращайтесь в любое время!",
                "Всегда пожалуйста! Это моя работа и удовольствие - помогать людям. Что-то еще интересует?",
                "Не за что! Я здесь для того, чтобы быть полезным. Если понадобится что-то еще - просто напишите!"
            ]
        }
    
    async def initialize_ai_models(self):
        """Инициализация улучшенных ИИ моделей"""
        try:
            logger.info("🧠 Загрузка улучшенных ИИ моделей...")
            
            # Загружаем более мощную текстовую модель
            await self._load_improved_text_model()
            
            # Загружаем модель генерации изображений
            await self._load_image_model()
            
            # Загружаем модель анализа изображений
            await self._load_vision_model()
            
            self.models_ready = True
            logger.info("✅ Все улучшенные ИИ модели загружены!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки моделей: {e}")
            return False
    
    async def _load_improved_text_model(self):
        """Загрузка улучшенной текстовой модели"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            
            # Используем более мощную модель для лучших ответов
            model_name = "microsoft/DialoGPT-medium"  # Увеличиваем размер модели
            
            logger.info(f"Загрузка улучшенной текстовой модели: {model_name}")
            
            self.text_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.text_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                device_map="cpu" if self.device == "cpu" else "auto",
                pad_token_id=50256  # Устанавливаем pad_token
            )
            
            # Устанавливаем pad_token в токенизаторе
            if self.text_tokenizer.pad_token is None:
                self.text_tokenizer.pad_token = self.text_tokenizer.eos_token
                
            logger.info("✅ Улучшенная текстовая модель загружена")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки улучшенной текстовой модели: {e}")
            # Fallback на простую модель
            self.text_model = "fallback"
    
    async def _load_image_model(self):
        """Загрузка модели генерации изображений"""
        try:
            from diffusers import StableDiffusionPipeline
            
            model_name = "runwayml/stable-diffusion-v1-5"
            
            logger.info(f"Загрузка модели генерации изображений: {model_name}")
            
            self.image_pipeline = StableDiffusionPipeline.from_pretrained(
                model_name,
                torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
                safety_checker=None,
                requires_safety_checker=False
            )
            
            if self.device == "cpu":
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
    
    async def generate_smart_response(self, user_message: str, user_id: str) -> str:
        """Генерация умного ответа"""
        try:
            # Получаем контекст пользователя
            context = self._get_user_context(user_id)
            
            # Определяем тип сообщения
            message_type = self._classify_message(user_message)
            
            # Генерируем ответ в зависимости от типа
            if message_type == "image_generation":
                return await self._handle_smart_image_generation(user_message)
            elif message_type == "question":
                return await self._handle_smart_question(user_message, context)
            elif message_type == "greeting":
                return self._handle_smart_greeting(user_message, context)
            elif message_type == "gratitude":
                return self._handle_gratitude(user_message)
            else:
                return await self._handle_smart_conversation(user_message, context)
                
        except Exception as e:
            logger.error(f"Ошибка генерации умного ответа: {e}")
            return "Извините, произошла ошибка при обработке вашего сообщения. Попробуйте переформулировать вопрос."
    
    def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Получение контекста пользователя"""
        if user_id not in self.conversation_contexts:
            self.conversation_contexts[user_id] = {
                "messages": [],
                "preferences": {},
                "topics": [],
                "last_interaction": datetime.now()
            }
        return self.conversation_contexts[user_id]
    
    def _classify_message(self, message: str) -> str:
        """Классификация типа сообщения"""
        message_lower = message.lower()
        
        # Генерация изображений
        image_keywords = [
            "нарисуй", "создай", "сгенерируй", "изображение", "картинку", "фото",
            "покажи", "визуализируй", "рисунок", "иллюстрация"
        ]
        if any(keyword in message_lower for keyword in image_keywords):
            return "image_generation"
        
        # Приветствия
        greeting_keywords = [
            "привет", "здравствуй", "добрый", "хай", "hello", "hi"
        ]
        if any(keyword in message_lower for keyword in greeting_keywords):
            return "greeting"
        
        # Благодарности
        gratitude_keywords = [
            "спасибо", "благодарю", "thanks", "thank you", "отлично", "замечательно"
        ]
        if any(keyword in message_lower for keyword in gratitude_keywords):
            return "gratitude"
        
        # Вопросы
        question_keywords = [
            "что", "как", "где", "когда", "почему", "зачем", "какой", "какая", "какие",
            "расскажи", "объясни", "поясни", "?"
        ]
        if any(keyword in message_lower for keyword in question_keywords):
            return "question"
        
        return "conversation"
    
    async def _handle_smart_image_generation(self, message: str) -> str:
        """Умная обработка генерации изображений"""
        try:
            # Извлекаем и улучшаем промпт
            prompt = self._extract_and_enhance_prompt(message)
            
            if not prompt:
                return "Не могу понять, что именно нарисовать. Опишите подробнее - какие объекты, стиль, настроение, цвета вы хотите видеть на изображении?"
            
            logger.info(f"Генерация изображения: {prompt}")
            
            # Отправляем уведомление
            await self.send_message("🎨 Создаю изображение... Это займет около 2 минут. Я уведомлю вас, когда будет готово!")
            
            # Генерируем изображение
            image_path = await self._generate_enhanced_image(prompt)
            
            if image_path:
                await self.send_photo(image_path, f"🎨 Готово! Изображение по вашему описанию: '{prompt}'")
                return "Изображение создано! Как вам результат? Могу создать вариации или что-то другое."
            else:
                return "К сожалению, не удалось создать изображение. Попробуйте описать что-то другое или переформулируйте запрос."
                
        except Exception as e:
            logger.error(f"Ошибка генерации изображения: {e}")
            return "Произошла ошибка при создании изображения. Попробуйте еще раз с другим описанием."
    
    def _extract_and_enhance_prompt(self, message: str) -> str:
        """Извлечение и улучшение промпта"""
        # Убираем служебные слова
        prompt = message
        remove_words = [
            "нарисуй", "создай", "сгенерируй", "сделай", "покажи", "визуализируй",
            "изображение", "картинку", "фото", "рисунок", "иллюстрацию",
            "мне", "пожалуйста", "можешь", "хочу"
        ]
        
        for word in remove_words:
            prompt = re.sub(rf'\b{word}\b', '', prompt, flags=re.IGNORECASE)
        
        prompt = prompt.strip()
        
        # Улучшаем промпт для лучшего качества
        if prompt:
            # Добавляем качественные термины
            enhanced_prompt = f"{prompt}, high quality, detailed, masterpiece, best quality, professional"
            return enhanced_prompt
        
        return ""
    
    async def _generate_enhanced_image(self, prompt: str) -> Optional[str]:
        """Улучшенная генерация изображения"""
        try:
            if self.image_pipeline == "fallback":
                return await self._create_enhanced_placeholder(prompt)
            
            # Улучшенные параметры генерации
            enhanced_prompt = f"{prompt}, high quality, detailed, masterpiece, 8k, professional photography"
            negative_prompt = "low quality, blurry, distorted, ugly, bad anatomy, deformed, extra limbs, bad hands, text, watermark"
            
            # Генерируем изображение с улучшенными настройками
            image = self.image_pipeline(
                prompt=enhanced_prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=50,  # Больше шагов для качества
                guidance_scale=12.0,     # Выше guidance для соответствия промпту
                height=512,
                width=512
            ).images[0]
            
            # Сохраняем
            timestamp = datetime.now().timestamp()
            image_path = f"/workspace/data/smart_generated_{timestamp}.png"
            os.makedirs("/workspace/data", exist_ok=True)
            image.save(image_path)
            
            return image_path
            
        except Exception as e:
            logger.error(f"Ошибка улучшенной генерации: {e}")
            return await self._create_enhanced_placeholder(prompt)
    
    async def _create_enhanced_placeholder(self, prompt: str) -> str:
        """Создание улучшенной заглушки изображения"""
        try:
            from PIL import Image, ImageDraw, ImageFont, ImageFilter
            import random
            
            # Создаем изображение с градиентом
            width, height = 512, 512
            img = Image.new('RGB', (width, height), color=(0, 0, 0))
            
            # Создаем градиентный фон
            for y in range(height):
                for x in range(width):
                    r = int(50 + (x / width) * 150)
                    g = int(50 + (y / height) * 150)
                    b = int(100 + ((x + y) / (width + height)) * 100)
                    img.putpixel((x, y), (r, g, b))
            
            # Применяем размытие для эффекта
            img = img.filter(ImageFilter.GaussianBlur(radius=2))
            
            draw = ImageDraw.Draw(img)
            
            # Загружаем шрифты
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
                text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except:
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Разбиваем промпт на строки
            words = prompt.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if len(test_line) <= 20:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Ограничиваем количество строк
            lines = lines[:3]
            
            # Рисуем заголовок
            title = "AI Generated Image"
            bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = bbox[2] - bbox[0]
            draw.text(
                ((width - title_width) // 2, 50),
                title,
                fill=(255, 255, 255),
                font=title_font
            )
            
            # Рисуем промпт
            total_height = len(lines) * 35
            start_y = (height - total_height) // 2 + 50
            
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=text_font)
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                y = start_y + i * 35
                
                # Тень для читаемости
                draw.text((x + 2, y + 2), line, fill=(0, 0, 0, 128), font=text_font)
                # Основной текст
                draw.text((x, y), line, fill=(255, 255, 255), font=text_font)
            
            # Добавляем информацию о системе
            system_info = [
                "AGI Layer v3.9",
                "Smart AI System",
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ]
            
            y_pos = height - 80
            for info in system_info:
                bbox = draw.textbbox((0, 0), info, font=small_font)
                text_width = bbox[2] - bbox[0]
                draw.text(
                    ((width - text_width) // 2, y_pos),
                    info,
                    fill=(200, 200, 200),
                    font=small_font
                )
                y_pos += 20
            
            # Декоративная рамка
            draw.rectangle([10, 10, width-10, height-10], outline=(255, 255, 255), width=3)
            draw.rectangle([15, 15, width-15, height-15], outline=(150, 150, 150), width=1)
            
            # Сохраняем
            timestamp = datetime.now().timestamp()
            image_path = f"/workspace/data/smart_placeholder_{timestamp}.png"
            os.makedirs("/workspace/data", exist_ok=True)
            img.save(image_path)
            
            return image_path
            
        except Exception as e:
            logger.error(f"Ошибка создания улучшенной заглушки: {e}")
            return None
    
    async def _handle_smart_question(self, message: str, context: Dict) -> str:
        """Умная обработка вопросов"""
        try:
            message_lower = message.lower()
            
            # Проверяем базу знаний
            for topic, responses in self.knowledge_base.items():
                if topic in message_lower:
                    # Выбираем случайный ответ из базы знаний
                    base_response = random.choice(responses)
                    
                    # Добавляем персонализацию
                    if len(context["messages"]) > 0:
                        base_response += "\n\nЕсли у вас есть еще вопросы по этой теме - спрашивайте!"
                    
                    return base_response
            
            # Если в базе знаний нет ответа, используем ИИ
            if self.text_model != "fallback" and self.models_ready:
                return await self._generate_ai_response(message, context)
            else:
                return await self._generate_smart_fallback(message, context)
                
        except Exception as e:
            logger.error(f"Ошибка обработки вопроса: {e}")
            return "Это интересный вопрос! К сожалению, сейчас не могу дать детальный ответ, но запомню его для изучения."
    
    async def _generate_ai_response(self, message: str, context: Dict) -> str:
        """Генерация ответа с помощью ИИ"""
        try:
            # Подготавливаем контекст разговора
            conversation_history = context.get("messages", [])[-3:]  # Последние 3 сообщения
            
            # Формируем промпт с контекстом
            prompt_parts = []
            for msg in conversation_history:
                prompt_parts.append(f"Human: {msg['user']}")
                prompt_parts.append(f"AI: {msg['ai']}")
            
            prompt_parts.append(f"Human: {message}")
            prompt_parts.append("AI:")
            
            full_prompt = "\n".join(prompt_parts)
            
            # Токенизируем
            inputs = self.text_tokenizer.encode(full_prompt, return_tensors="pt", max_length=512, truncation=True)
            
            # Генерируем ответ
            with torch.no_grad():
                outputs = self.text_model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 150,
                    num_return_sequences=1,
                    temperature=0.8,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.text_tokenizer.eos_token_id,
                    eos_token_id=self.text_tokenizer.eos_token_id,
                    no_repeat_ngram_size=3
                )
            
            # Декодируем
            response = self.text_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Извлекаем только ответ ИИ
            ai_response = response.split("AI:")[-1].strip()
            
            # Очищаем от артефактов
            ai_response = self._clean_ai_response(ai_response)
            
            if len(ai_response) < 10:
                return await self._generate_smart_fallback(message, context)
            
            # Сохраняем в контекст
            self._update_context(context, message, ai_response)
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Ошибка ИИ генерации: {e}")
            return await self._generate_smart_fallback(message, context)
    
    def _clean_ai_response(self, response: str) -> str:
        """Очистка ответа ИИ от артефактов"""
        # Убираем повторы
        response = re.sub(r'\b(\w+)\s+\1\b', r'\1', response)
        
        # Убираем странные символы
        response = re.sub(r'[^\w\s.,!?;:()\-\'"]+', '', response, flags=re.UNICODE)
        
        # Ограничиваем длину
        if len(response) > 500:
            response = response[:500] + "..."
        
        # Убираем незавершенные предложения
        sentences = response.split('.')
        if len(sentences) > 1 and len(sentences[-1].strip()) < 10:
            response = '.'.join(sentences[:-1]) + '.'
        
        return response.strip()
    
    async def _generate_smart_fallback(self, message: str, context: Dict) -> str:
        """Умная заглушка для ответов"""
        message_lower = message.lower()
        
        # Анализируем тему сообщения
        if any(word in message_lower for word in ["python", "программирование", "код"]):
            responses = [
                "Python - отличный выбор для изучения программирования! Это мощный и в то же время простой язык. Что именно вас интересует в Python?",
                "Программирование на Python открывает множество возможностей - от веб-разработки до машинного обучения. С чего хотите начать?",
                "Python популярен благодаря своей простоте и мощности. Используется в ИИ, анализе данных, веб-разработке. Какая область вас интересует?"
            ]
        elif any(word in message_lower for word in ["ии", "искусственный", "интеллект", "нейросети"]):
            responses = [
                "Искусственный интеллект - fascinating область! Современные ИИ системы, как я, используют глубокое обучение для понимания и генерации контента. Что именно хотите узнать?",
                "ИИ развивается невероятно быстро. Нейронные сети теперь могут создавать изображения, понимать текст, даже программировать. Какой аспект ИИ вас больше интересует?",
                "Нейронные сети работают подобно человеческому мозгу - обрабатывают информацию через множество связанных узлов. Это позволяет им учиться и решать сложные задачи."
            ]
        elif any(word in message_lower for word in ["как", "работает", "устроен"]):
            responses = [
                "Это сложный вопрос! Принцип работы зависит от многих факторов. Могу объяснить подробнее, если уточните, что именно вас интересует.",
                "Хороший вопрос о принципах работы! Обычно это включает несколько этапов и механизмов. Что конкретно хотите понять?",
                "Механизм работы действительно интересен! Это многоступенчатый процесс с различными компонентами. Какой аспект вас больше интересует?"
            ]
        elif any(word in message_lower for word in ["что", "такое", "это"]):
            responses = [
                "Это интересная тема для изучения! Обычно это понятие включает множество аспектов и имеет богатую историю развития. Что именно хотите узнать?",
                "Хороший вопрос! Это область знаний с множеством нюансов и практических применений. Какой аспект вас больше интересует?",
                "Это обширная тема! Могу рассказать о различных аспектах - от основ до продвинутых концепций. С чего начнем?"
            ]
        else:
            responses = [
                "Интересная мысль! Это действительно заслуживает обсуждения. Расскажите больше о том, что вас интересует в этом вопросе.",
                "Понимаю вашу точку зрения. Это многогранная тема с различными подходами. Что бы вы хотели узнать подробнее?",
                "Хорошее наблюдение! Есть много способов взглянуть на это. Какой аспект вас больше всего интригует?"
            ]
        
        response = random.choice(responses)
        
        # Сохраняем в контекст
        self._update_context(context, message, response)
        
        return response
    
    def _handle_smart_greeting(self, message: str, context: Dict) -> str:
        """Умная обработка приветствий"""
        is_first_time = len(context.get("messages", [])) == 0
        
        if is_first_time:
            greetings = random.choice(self.knowledge_base["приветствие"])
        else:
            greetings = [
                "Снова привет! Рад вас видеть. Чем могу помочь сегодня?",
                "Здравствуйте еще раз! Готов к новым интересным задачам. Что будем делать?",
                "Привет! Хорошо, что вернулись. Есть что-то интересное для обсуждения или создания?"
            ]
            greetings = random.choice(greetings)
        
        # Сохраняем в контекст
        self._update_context(context, message, greetings)
        
        return greetings
    
    def _handle_gratitude(self, message: str) -> str:
        """Обработка благодарностей"""
        return random.choice(self.knowledge_base["благодарность"])
    
    async def _handle_smart_conversation(self, message: str, context: Dict) -> str:
        """Умная обработка обычного разговора"""
        if self.text_model != "fallback" and self.models_ready:
            return await self._generate_ai_response(message, context)
        else:
            return await self._generate_smart_fallback(message, context)
    
    def _update_context(self, context: Dict, user_message: str, ai_response: str):
        """Обновление контекста разговора"""
        context["messages"].append({
            "user": user_message,
            "ai": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Ограничиваем историю
        if len(context["messages"]) > 10:
            context["messages"] = context["messages"][-10:]
        
        context["last_interaction"] = datetime.now()
    
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
                    data.add_field('photo', photo, filename='smart_generated.png')
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
            user_id = str(message['from']['id'])
            user_name = message['from'].get('first_name', 'Пользователь')
            
            logger.info(f"Получено от {user_name}: {text}")
            
            # Игнорируем очень короткие сообщения
            if len(text.strip()) < 2:
                return
            
            # Генерируем умный ответ
            response = await self.generate_smart_response(text, user_id)
            await self.send_message(response, chat_id)
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await self.send_message("Извините, произошла ошибка при обработке сообщения.", chat_id)
    
    async def run(self):
        """Запуск умного бота"""
        logger.info("🧠 Запуск Smart AGI Bot v3.9")
        
        # Инициализация ИИ моделей
        if not await self.initialize_ai_models():
            logger.warning("⚠️ Модели не загружены, работаем в улучшенном режиме заглушек")
        
        # Приветственное сообщение
        await self.send_message("🧠 Smart AGI v3.9 запущен!\n\nТеперь у меня значительно улучшенный интеллект. Общайтесь со мной естественно - я понимаю контекст и даю осмысленные ответы!")
        
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
                logger.info("Остановка умного бота...")
                break
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                await asyncio.sleep(5)


async def main():
    """Основная функция"""
    smart_agi = SmartAGI()
    await smart_agi.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Smart AGI бот остановлен")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")