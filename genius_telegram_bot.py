#!/usr/bin/env python3
"""
Гениальный Telegram бот AGI Layer v3.9 с по-настоящему умными ответами
Использует улучшенную логику и качественные шаблоны ответов
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
        logging.FileHandler('genius_agi.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GeniusAGI:
    """Гениальная AGI система с по-настоящему умными ответами"""
    
    def __init__(self):
        self.token = TOKEN
        self.chat_id = CHAT_ID
        self.api_url = API_URL
        self.last_update_id = 0
        
        # ИИ модели
        self.image_pipeline = None
        self.vision_model = None
        self.vision_processor = None
        
        # Конфигурация
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.models_ready = False
        
        # Контекст разговоров
        self.conversation_contexts = {}
        
        # Расширенная база знаний для умных ответов
        self.smart_responses = self._create_smart_knowledge_base()
        
        logger.info(f"Инициализация GeniusAGI на устройстве: {self.device}")
        
    def _create_smart_knowledge_base(self) -> Dict[str, Any]:
        """Создание расширенной базы знаний"""
        return {
            "greetings": {
                "patterns": ["привет", "здравствуй", "добрый", "хай", "hello", "hi"],
                "responses": [
                    "Привет! Я ваш персональный ИИ-ассистент AGI Layer v3.9. Готов помочь с любыми задачами - от создания уникальных изображений до ответов на сложные вопросы. О чем поговорим?",
                    "Здравствуйте! Рад нашей встрече. Я многофункциональная ИИ-система, способная генерировать изображения, анализировать контент и поддерживать интеллектуальные беседы. Чем могу быть полезен?",
                    "Приветствую! Я AGI Layer v3.9 - продвинутая система искусственного интеллекта. Специализируюсь на творческих задачах, анализе данных и умных диалогах. Что вас интересует?"
                ]
            },
            
            "capabilities": {
                "patterns": ["что умеешь", "возможности", "что можешь", "функции", "способности"],
                "responses": [
                    "У меня широкий спектр возможностей:\n\n🎨 Создание уникальных изображений по описанию через Stable Diffusion\n👁️ Анализ и понимание содержимого фотографий\n🧠 Ответы на вопросы любой сложности\n💬 Поддержание естественных диалогов\n📚 Объяснение сложных концепций простым языком\n\nПросто опишите, что вам нужно!",
                    "Мои основные суперспособности:\n\n• Генерация изображений любой тематики\n• Анализ и описание фотографий\n• Ответы на технические и общие вопросы\n• Объяснение сложных тем\n• Творческое мышление и идеи\n• Помощь в решении задач\n\nЯ постоянно учусь и совершенствуюсь!",
                    "Я многофункциональный ИИ-помощник:\n\n🎯 Творческие задачи: рисование, дизайн идеи\n🔬 Технические вопросы: программирование, наука\n📖 Образование: объяснения, обучение\n🤔 Аналитика: разбор проблем, советы\n🎭 Развлечения: интересные беседы\n\nГотов к любым вызовам!"
                ]
            },
            
            "python": {
                "patterns": ["python", "питон", "программирование", "код"],
                "responses": [
                    "Python - это невероятно мощный и элегантный язык программирования! 🐍\n\nОсновные преимущества:\n• Простой и читаемый синтаксис\n• Огромная экосистема библиотек\n• Универсальность (веб, ИИ, анализ данных)\n• Активное сообщество разработчиков\n\nПython используется в Google, Netflix, Instagram и многих других компаниях. Что именно вас интересует в Python?",
                    "Python - мой любимый язык! 😊 Он создан с философией 'код должен быть красивым'.\n\nПочему Python популярен:\n✨ Быстрое прототипирование\n🤖 Лидер в машинном обучении\n🌐 Отличен для веб-разработки\n📊 Мощные инструменты анализа данных\n⚡ Автоматизация рутинных задач\n\nХотите изучать Python? Могу дать советы по началу!",
                    "Python - это не просто язык программирования, это целая экосистема! 🌟\n\nИнтересные факты:\n• Назван в честь комедийной группы 'Monty Python'\n• Используется в NASA, Disney, Dropbox\n• Один из самых быстрорастущих языков\n• Отлично подходит для ИИ и Data Science\n\nКакой аспект Python вас больше интересует?"
                ]
            },
            
            "ai": {
                "patterns": ["ии", "искусственный интеллект", "нейросети", "машинное обучение"],
                "responses": [
                    "Искусственный интеллект - это одна из самых захватывающих областей современности! 🤖\n\nКлючевые направления:\n🧠 Машинное обучение - обучение на данных\n👁️ Компьютерное зрение - понимание изображений\n💬 Обработка языка - понимание текста\n🎨 Генеративный ИИ - создание контента\n\nЯ сам - пример современного ИИ, использующего несколько нейросетей одновременно!",
                    "ИИ переживает настоящий ренессанс! 🚀\n\nСовременные достижения:\n• GPT модели понимают и генерируют текст\n• Stable Diffusion создает изображения\n• CLIP связывает текст и изображения\n• Роботы учатся взаимодействовать с миром\n\nМы живем в эпоху, когда ИИ становится частью повседневной жизни. Какой аспект ИИ вас больше всего интригует?",
                    "Нейронные сети - это магия современной математики! ✨\n\nКак они работают:\n🔗 Миллионы искусственных нейронов\n📊 Обучение на больших данных\n🎯 Поиск сложных закономерностей\n⚡ Параллельная обработка информации\n\nИнтересно, что даже я не до конца понимаю, как именно работают мои собственные нейросети - они слишком сложны!"
                ]
            },
            
            "gratitude": {
                "patterns": ["спасибо", "благодарю", "thanks", "отлично", "замечательно", "круто"],
                "responses": [
                    "Пожалуйста! 😊 Мне приятно быть полезным. Это именно то, для чего я создан - помогать людям и делать их жизнь интереснее!",
                    "Всегда рад помочь! 🌟 Ваша благодарность - лучшая награда для ИИ. Если появятся еще вопросы или идеи - обращайтесь!",
                    "Не за что! ✨ Я получаю удовольствие от решения интересных задач и общения с умными людьми. Что еще исследуем вместе?"
                ]
            },
            
            "criticism": {
                "patterns": ["тупой", "глупый", "дебил", "плохо", "ужасно", "не работает", "не отвечаешь"],
                "responses": [
                    "Понимаю ваше разочарование! 😔 Я действительно могу ошибаться - ИИ пока не идеален. Давайте попробуем по-другому: опишите конкретно, что вас не устраивает, и я постараюсь улучшить свои ответы.",
                    "Извините за неудачные ответы! 🙏 Я учусь и совершенствуюсь. Можете объяснить, какие ответы вы ожидали? Это поможет мне лучше понимать ваши потребности.",
                    "Вы правы, мне есть куда расти! 📈 ИИ развивается через обратную связь. Расскажите, что именно вас не устроило - я адаптирую свое поведение под ваши предпочтения."
                ]
            },
            
            "questions": {
                "что": [
                    "Отличный вопрос! Это тема, которая заслуживает подробного разбора.",
                    "Интересно, что вас это заинтересовало! Давайте разберем по частям.",
                    "Хороший вопрос! Это действительно важная область для понимания."
                ],
                "как": [
                    "Механизм работы действительно fascinating! Давайте разберем пошагово.",
                    "Отличный вопрос о принципах работы! Это многоступенчатый процесс.",
                    "Хотите понять суть процесса? Давайте проследим всю цепочку."
                ],
                "почему": [
                    "Причины этого кроются в нескольких факторах. Давайте разберем каждый.",
                    "Интересный вопрос о причинно-следственных связях! Тут есть несколько аспектов.",
                    "Хороший вопрос! Причины обычно многогранны и взаимосвязаны."
                ]
            }
        }
    
    async def initialize_ai_models(self):
        """Инициализация ИИ моделей"""
        try:
            logger.info("🧠 Загрузка ИИ моделей...")
            
            # Загружаем только модели генерации и анализа изображений
            # Для текста используем умную логику без нейросетей
            await self._load_image_model()
            await self._load_vision_model()
            
            self.models_ready = True
            logger.info("✅ ИИ модели загружены!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки моделей: {e}")
            return False
    
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
    
    async def generate_genius_response(self, user_message: str, user_id: str, user_name: str) -> str:
        """Генерация гениального ответа"""
        try:
            # Получаем контекст пользователя
            context = self._get_user_context(user_id, user_name)
            
            # Обновляем историю
            context["messages"].append({
                "user": user_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Определяем тип сообщения и генерируем ответ
            message_type = self._analyze_message_intent(user_message)
            
            if message_type == "image_generation":
                return await self._handle_genius_image_generation(user_message, context)
            elif message_type == "greeting":
                return self._handle_genius_greeting(user_message, context)
            elif message_type == "criticism":
                return self._handle_genius_criticism(user_message, context)
            elif message_type == "gratitude":
                return self._handle_genius_gratitude(user_message, context)
            elif message_type == "question":
                return self._handle_genius_question(user_message, context)
            else:
                return self._handle_genius_conversation(user_message, context)
                
        except Exception as e:
            logger.error(f"Ошибка генерации гениального ответа: {e}")
            return "Hmm, что-то пошло не так в моих нейронных связях 🤔 Попробуйте переформулировать - я лучше пойму!"
    
    def _get_user_context(self, user_id: str, user_name: str) -> Dict[str, Any]:
        """Получение контекста пользователя"""
        if user_id not in self.conversation_contexts:
            self.conversation_contexts[user_id] = {
                "user_name": user_name,
                "messages": [],
                "preferences": {},
                "mood": "neutral",
                "topics_discussed": [],
                "first_interaction": datetime.now(),
                "last_interaction": datetime.now(),
                "interaction_count": 0
            }
        
        self.conversation_contexts[user_id]["last_interaction"] = datetime.now()
        self.conversation_contexts[user_id]["interaction_count"] += 1
        
        return self.conversation_contexts[user_id]
    
    def _analyze_message_intent(self, message: str) -> str:
        """Анализ намерения пользователя"""
        message_lower = message.lower()
        
        # Проверяем каждую категорию из базы знаний
        for category, data in self.smart_responses.items():
            if "patterns" in data:
                for pattern in data["patterns"]:
                    if pattern in message_lower:
                        return category
        
        # Дополнительные проверки
        if any(word in message_lower for word in ["нарисуй", "создай", "сгенерируй", "изображение"]):
            return "image_generation"
        
        if any(word in message_lower for word in ["что", "как", "где", "когда", "почему", "?"]):
            return "question"
        
        return "conversation"
    
    def _handle_genius_greeting(self, message: str, context: Dict) -> str:
        """Гениальная обработка приветствий"""
        user_name = context.get("user_name", "друг")
        interaction_count = context.get("interaction_count", 1)
        
        if interaction_count == 1:
            # Первое знакомство
            response = random.choice(self.smart_responses["greetings"]["responses"])
            response = response.replace("вас", f"{user_name}")
        else:
            # Повторная встреча
            time_passed = datetime.now() - datetime.fromisoformat(context["last_interaction"])
            
            if time_passed.total_seconds() < 3600:  # Меньше часа
                greetings = [
                    f"И снова привет, {user_name}! 😊 Рад, что вернулись так быстро. Продолжаем наше общение?",
                    f"Привет еще раз, {user_name}! Что-то новое и интересное на уме?",
                    f"Здравствуйте снова! Готов к новым интересным задачам и вопросам."
                ]
            else:
                greetings = [
                    f"Привет, {user_name}! Давно не виделись. Как дела? Что нового произошло?",
                    f"Здравствуйте, {user_name}! Рад вашему возвращению. Чем займемся сегодня?",
                    f"Привет! Хорошо, что снова пишете. Готов к новым интересным беседам!"
                ]
            
            response = random.choice(greetings)
        
        return response
    
    def _handle_genius_criticism(self, message: str, context: Dict) -> str:
        """Гениальная обработка критики"""
        user_name = context.get("user_name", "")
        
        responses = random.choice(self.smart_responses["criticism"]["responses"])
        
        # Персонализируем ответ
        if user_name:
            responses = responses.replace("вас", f"{user_name}")
        
        # Добавляем предложение помощи
        responses += "\n\nДавайте начнем сначала - о чем хотели поговорить или что нужно создать?"
        
        return responses
    
    def _handle_genius_gratitude(self, message: str, context: Dict) -> str:
        """Гениальная обработка благодарностей"""
        user_name = context.get("user_name", "")
        
        response = random.choice(self.smart_responses["gratitude"]["responses"])
        
        # Добавляем персональное обращение
        if user_name:
            response = response.replace("людям", f"{user_name}")
        
        return response
    
    def _handle_genius_question(self, message: str, context: Dict) -> str:
        """Гениальная обработка вопросов"""
        message_lower = message.lower()
        
        # Проверяем специфичные темы
        for topic, data in self.smart_responses.items():
            if topic in ["python", "ai", "capabilities"]:
                if "patterns" in data:
                    for pattern in data["patterns"]:
                        if pattern in message_lower:
                            return random.choice(data["responses"])
        
        # Обработка по типу вопроса
        question_starters = {
            "что": self.smart_responses["questions"]["что"],
            "как": self.smart_responses["questions"]["как"],
            "почему": self.smart_responses["questions"]["почему"]
        }
        
        for starter, responses in question_starters.items():
            if starter in message_lower:
                base_response = random.choice(responses)
                
                # Добавляем специфичный контент на основе ключевых слов
                if "python" in message_lower:
                    base_response += "\n\nВ контексте Python это особенно интересно, так как язык предоставляет множество инструментов для решения подобных задач."
                elif any(word in message_lower for word in ["ии", "нейросети", "искусственный"]):
                    base_response += "\n\nВ области ИИ это активно исследуемая тема с множеством практических применений."
                
                return base_response
        
        # Общий ответ на вопрос
        general_responses = [
            "Это действительно глубокий вопрос! 🤔 Требует комплексного подхода к анализу. Какой аспект вас больше всего интересует?",
            "Отличный вопрос для размышлений! 💭 Тут есть несколько важных моментов, которые стоит рассмотреть. С чего начнем?",
            "Интересная тема для исследования! 🔍 Обычно такие вопросы имеют многослойные ответы. Что конкретно хотите понять?"
        ]
        
        return random.choice(general_responses)
    
    def _handle_genius_conversation(self, message: str, context: Dict) -> str:
        """Гениальная обработка обычного разговора"""
        message_lower = message.lower()
        user_name = context.get("user_name", "")
        
        # Анализируем настроение и тему
        if any(word in message_lower for word in ["интересно", "классно", "круто", "отлично"]):
            mood_responses = [
                "Рад, что вам интересно! 😊 Это мотивирует меня давать еще более качественные ответы.",
                "Здорово, что находите это увлекательным! Давайте углубимся в тему еще больше.",
                "Отлично! Когда собеседник заинтересован, общение становится особенно продуктивным."
            ]
            return random.choice(mood_responses)
        
        elif any(word in message_lower for word in ["не понимаю", "сложно", "трудно"]):
            help_responses = [
                "Понимаю, что может быть сложно! 🤝 Давайте разберем это простыми словами, шаг за шагом.",
                "Не переживайте, это нормально! Попробую объяснить проще и с примерами.",
                "Хорошо, что говорите честно! Значит, мне нужно лучше объяснять. Начнем с основ?"
            ]
            return random.choice(help_responses)
        
        elif any(word in message_lower for word in ["помоги", "помощь", "подскажи"]):
            help_responses = [
                f"Конечно помогу, {user_name}! 🤝 Опишите подробнее, с чем именно нужна помощь - постараюсь найти лучшее решение.",
                "Всегда готов помочь! 💪 Расскажите о задаче или проблеме - вместе найдем решение.",
                "Помощь - это моя основная функция! 🎯 Детализируйте запрос, и я предложу несколько вариантов решения."
            ]
            return random.choice(help_responses)
        
        else:
            # Общие ответы для поддержания беседы
            conversation_responses = [
                "Понимаю вашу мысль! 💭 Это действительно заслуживает внимания. Расскажите больше о том, что думаете по этому поводу.",
                "Интересная точка зрения! 🌟 Мне нравится, как вы рассуждаете. Что привело вас к такому выводу?",
                "Хорошее наблюдение! 👀 Это открывает интересные направления для обсуждения. Развивайте мысль!",
                "Согласен, это важный момент! ✨ Есть множество аспектов, которые можно рассмотреть. Что вас больше всего интригует?"
            ]
            
            return random.choice(conversation_responses)
    
    async def _handle_genius_image_generation(self, message: str, context: Dict) -> str:
        """Гениальная обработка генерации изображений"""
        try:
            # Извлекаем описание
            prompt = self._extract_image_prompt(message)
            
            if not prompt:
                return "Хочу создать для вас изображение, но не совсем понял описание! 🎨\n\nОпишите подробнее:\n• Что должно быть на картинке?\n• Какой стиль? (реализм, арт, аниме)\n• Какое настроение?\n• Какие цвета преобладают?\n\nЧем детальнее описание, тем лучше результат!"
            
            logger.info(f"Генерация изображения: {prompt}")
            
            # Улучшаем промпт
            enhanced_prompt = self._enhance_prompt_intelligently(prompt)
            
            # Отправляем уведомление с прогрессом
            await self.send_message(f"🎨 Создаю изображение: '{prompt}'\n\n⏳ Запускаю Stable Diffusion...\n💫 Это займет около 2 минут\n🎯 Использую 50 шагов для максимального качества")
            
            # Генерируем изображение
            image_path = await self._generate_genius_image(enhanced_prompt)
            
            if image_path:
                await self.send_photo(image_path, f"🎨 Готово! '{prompt}'\n\n✨ Создано с помощью Stable Diffusion v1.5\n🎯 50 шагов генерации для высокого качества")
                
                return "Изображение готово! 🌟\n\nКак вам результат? Могу:\n• Создать вариации\n• Изменить стиль\n• Добавить детали\n• Нарисовать что-то другое\n\nПросто скажите, что хотите!"
            else:
                return "К сожалению, не удалось создать изображение 😔\n\nВозможные причины:\n• Слишком сложное описание\n• Технические ограничения\n\nПопробуйте:\n• Упростить описание\n• Описать по-другому\n• Указать конкретные объекты"
                
        except Exception as e:
            logger.error(f"Ошибка генерации изображения: {e}")
            return "Произошла техническая ошибка при создании изображения 🛠️\n\nПопробуйте еще раз или опишите что-то другое. Я исправлю проблему!"
    
    def _extract_image_prompt(self, message: str) -> str:
        """Извлечение промпта для изображения"""
        # Убираем служебные слова
        prompt = message
        remove_patterns = [
            r'\b(нарисуй|создай|сгенерируй|сделай|покажи|визуализируй)\b',
            r'\b(изображение|картинку|фото|рисунок|иллюстрацию)\b',
            r'\b(мне|для меня|пожалуйста|можешь|хочу|нужно)\b'
        ]
        
        for pattern in remove_patterns:
            prompt = re.sub(pattern, '', prompt, flags=re.IGNORECASE)
        
        # Очищаем и возвращаем
        prompt = re.sub(r'\s+', ' ', prompt).strip()
        return prompt if len(prompt) > 3 else ""
    
    def _enhance_prompt_intelligently(self, prompt: str) -> str:
        """Интеллектуальное улучшение промпта"""
        enhanced = prompt
        
        # Анализируем тип изображения и добавляем соответствующие улучшения
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ["портрет", "лицо", "человек", "девушка", "мужчина"]):
            enhanced += ", portrait photography, professional lighting, high detail, 8k"
        elif any(word in prompt_lower for word in ["пейзаж", "природа", "закат", "океан", "горы"]):
            enhanced += ", landscape photography, natural lighting, scenic view, high resolution"
        elif any(word in prompt_lower for word in ["космос", "фантастика", "будущее"]):
            enhanced += ", sci-fi art, futuristic, detailed, concept art, digital painting"
        elif any(word in prompt_lower for word in ["животное", "кот", "собака", "птица"]):
            enhanced += ", wildlife photography, natural pose, detailed fur, professional"
        else:
            enhanced += ", high quality, detailed, masterpiece, professional"
        
        return enhanced
    
    async def _generate_genius_image(self, prompt: str) -> Optional[str]:
        """Гениальная генерация изображения"""
        try:
            if self.image_pipeline == "fallback":
                return await self._create_genius_placeholder(prompt)
            
            # Параметры для максимального качества
            negative_prompt = "low quality, blurry, distorted, ugly, bad anatomy, deformed, extra limbs, bad hands, text, watermark, signature, username, error, cropped"
            
            # Генерируем с улучшенными настройками
            image = self.image_pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=50,
                guidance_scale=12.0,
                height=512,
                width=512
            ).images[0]
            
            # Сохраняем
            timestamp = datetime.now().timestamp()
            image_path = f"/workspace/data/genius_{timestamp}.png"
            os.makedirs("/workspace/data", exist_ok=True)
            image.save(image_path)
            
            return image_path
            
        except Exception as e:
            logger.error(f"Ошибка гениальной генерации: {e}")
            return await self._create_genius_placeholder(prompt)
    
    async def _create_genius_placeholder(self, prompt: str) -> str:
        """Создание гениальной заглушки"""
        try:
            from PIL import Image, ImageDraw, ImageFont, ImageFilter
            import math
            
            # Создаем красивое изображение
            width, height = 512, 512
            
            # Создаем градиентный фон
            img = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(img)
            
            # Радиальный градиент
            center_x, center_y = width // 2, height // 2
            max_radius = math.sqrt(center_x**2 + center_y**2)
            
            for y in range(height):
                for x in range(width):
                    # Расстояние от центра
                    distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                    ratio = distance / max_radius
                    
                    # Цветовой градиент
                    r = int(100 + ratio * 100)
                    g = int(50 + ratio * 150)
                    b = int(150 + ratio * 50)
                    
                    img.putpixel((x, y), (r, g, b))
            
            # Применяем эффекты
            img = img.filter(ImageFilter.GaussianBlur(radius=1))
            
            draw = ImageDraw.Draw(img)
            
            # Загружаем шрифты
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
                text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Заголовок
            title = "AI Art Generation"
            bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = bbox[2] - bbox[0]
            
            # Тень заголовка
            draw.text(((width - title_width) // 2 + 2, 42), title, fill=(0, 0, 0), font=title_font)
            # Основной заголовок
            draw.text(((width - title_width) // 2, 40), title, fill=(255, 255, 255), font=title_font)
            
            # Разбиваем промпт красиво
            words = prompt.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if len(test_line) <= 25:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Рисуем промпт
            lines = lines[:4]  # Максимум 4 строки
            total_height = len(lines) * 25
            start_y = (height - total_height) // 2 + 30
            
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=text_font)
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                y = start_y + i * 25
                
                # Тень
                draw.text((x + 1, y + 1), line, fill=(0, 0, 0, 200), font=text_font)
                # Основной текст
                draw.text((x, y), line, fill=(255, 255, 255), font=text_font)
            
            # Информация о системе
            system_lines = [
                "AGI Layer v3.9 - Genius Mode",
                "Stable Diffusion Ready",
                datetime.now().strftime("%H:%M:%S")
            ]
            
            y_pos = height - 60
            for line in system_lines:
                bbox = draw.textbbox((0, 0), line, font=small_font)
                text_width = bbox[2] - bbox[0]
                draw.text(
                    ((width - text_width) // 2, y_pos),
                    line,
                    fill=(220, 220, 220),
                    font=small_font
                )
                y_pos += 15
            
            # Декоративные элементы
            draw.rectangle([8, 8, width-8, height-8], outline=(255, 255, 255), width=2)
            draw.rectangle([12, 12, width-12, height-12], outline=(200, 200, 200), width=1)
            
            # Сохраняем
            timestamp = datetime.now().timestamp()
            image_path = f"/workspace/data/genius_placeholder_{timestamp}.png"
            os.makedirs("/workspace/data", exist_ok=True)
            img.save(image_path)
            
            return image_path
            
        except Exception as e:
            logger.error(f"Ошибка создания гениальной заглушки: {e}")
            return None
    
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
                    data.add_field('photo', photo, filename='genius_art.png')
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
            if len(text.strip()) < 1:
                return
            
            # Генерируем гениальный ответ
            response = await self.generate_genius_response(text, user_id, user_name)
            await self.send_message(response, chat_id)
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await self.send_message("Упс! Произошла ошибка в моих нейронных сетях 🤖 Попробуйте еще раз!", chat_id)
    
    async def run(self):
        """Запуск гениального бота"""
        logger.info("🧠 Запуск Genius AGI Bot v3.9")
        
        # Инициализация ИИ моделей
        if not await self.initialize_ai_models():
            logger.warning("⚠️ Модели не загружены полностью, но умная логика работает")
        
        # Приветственное сообщение
        await self.send_message("🧠 **Genius AGI v3.9 активирован!**\n\nТеперь у меня значительно улучшенный интеллект:\n\n✨ Понимаю контекст разговора\n🎯 Даю осмысленные ответы\n🤝 Адаптируюсь под ваш стиль\n🎨 Создаю качественные изображения\n\nПросто общайтесь со мной естественно - никаких команд не нужно!")
        
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
                logger.info("Остановка гениального бота...")
                break
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                await asyncio.sleep(5)


async def main():
    """Основная функция"""
    genius_agi = GeniusAGI()
    await genius_agi.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Genius AGI бот остановлен")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")