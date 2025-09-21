"""
TelegramChatAgent - полноценный чат с нейросетью через Telegram
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import aiohttp
import asyncpg
from telegram import Update, Bot, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from .base_agent import BaseAgent, Task
from config.chat_config import (
    get_personality_config, 
    get_allowed_chat_ids, 
    format_message_template,
    CONTEXT_CONFIG,
    IMAGE_PROCESSING_CONFIG,
    MODERATION_CONFIG
)
import os
import io
import base64


class TelegramChatAgent(BaseAgent):
    """Агент для полноценного чата с нейросетью через Telegram"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("telegram_chat_agent", config)
        self.bot_token = config.get('telegram_token')
        self.allowed_chat_ids = get_allowed_chat_ids()
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        
        # Настройки чата из конфигурации
        self.max_context_messages = CONTEXT_CONFIG['max_messages']
        self.response_timeout = config.get('response_timeout', 30)
        self.enable_image_processing = IMAGE_PROCESSING_CONFIG['enabled']
        self.enable_voice_messages = config.get('enable_voice_messages', False)
        
        # Персонализация
        self.default_personality = config.get('default_personality', 'helpful_assistant')
        self.user_personalities = {}
        
        # Кэш активных диалогов
        self.active_conversations = {}
        
        # Модерация
        self.moderation_enabled = MODERATION_CONFIG['enabled']
        self.rate_limits = {}  # Для отслеживания лимитов пользователей
        
    async def _initialize_agent(self):
        """Инициализация Telegram Chat Agent"""
        if not self.bot_token:
            raise ValueError("Telegram token не настроен")
            
        self.bot = Bot(token=self.bot_token)
        self.application = Application.builder().token(self.bot_token).build()
        
        # Создание таблиц для чата
        await self._create_chat_tables()
        
        # Регистрация обработчиков
        self._register_handlers()
        
        # Запуск бота
        await self.application.initialize()
        await self.application.start()
        
        # Запуск polling
        asyncio.create_task(self._run_polling())
        
        # Периодическая очистка старых диалогов
        asyncio.create_task(self._cleanup_old_conversations())
        
        self.logger.info("TelegramChatAgent инициализирован")
    
    async def _create_chat_tables(self):
        """Создание таблиц для чата"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS chat_conversations (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT NOT NULL,
                        user_id BIGINT NOT NULL,
                        user_name VARCHAR(255),
                        message_text TEXT NOT NULL,
                        message_type VARCHAR(50) DEFAULT 'text',
                        is_user_message BOOLEAN DEFAULT TRUE,
                        response_text TEXT,
                        response_type VARCHAR(50),
                        context_data JSONB,
                        personality VARCHAR(100),
                        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        response_time_ms INTEGER,
                        INDEX (chat_id, processed_at),
                        INDEX (user_id)
                    );
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        user_id BIGINT PRIMARY KEY,
                        chat_id BIGINT NOT NULL,
                        personality VARCHAR(100) DEFAULT 'helpful_assistant',
                        language VARCHAR(10) DEFAULT 'ru',
                        context_length INTEGER DEFAULT 10,
                        enable_images BOOLEAN DEFAULT TRUE,
                        enable_voice BOOLEAN DEFAULT FALSE,
                        custom_prompt TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS chat_statistics (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT NOT NULL,
                        user_id BIGINT NOT NULL,
                        date DATE DEFAULT CURRENT_DATE,
                        messages_sent INTEGER DEFAULT 0,
                        responses_generated INTEGER DEFAULT 0,
                        images_processed INTEGER DEFAULT 0,
                        avg_response_time_ms INTEGER DEFAULT 0,
                        tokens_used INTEGER DEFAULT 0,
                        UNIQUE(chat_id, user_id, date)
                    );
                """)
                
                self.logger.info("Таблицы чата созданы")
                
        except Exception as e:
            self.logger.error(f"Ошибка создания таблиц чата: {e}")
            raise
    
    def _register_handlers(self):
        """Регистрация обработчиков команд и сообщений"""
        # Команды
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("help", self._cmd_help))
        self.application.add_handler(CommandHandler("personality", self._cmd_personality))
        self.application.add_handler(CommandHandler("clear", self._cmd_clear_context))
        self.application.add_handler(CommandHandler("settings", self._cmd_settings))
        self.application.add_handler(CommandHandler("stats", self._cmd_stats))
        self.application.add_handler(CommandHandler("generate", self._cmd_generate_image))
        
        # Обработка текстовых сообщений
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self._handle_text_message
        ))
        
        # Обработка изображений
        if self.enable_image_processing:
            self.application.add_handler(MessageHandler(
                filters.PHOTO, 
                self._handle_image_message
            ))
        
        # Обработка голосовых сообщений
        if self.enable_voice_messages:
            self.application.add_handler(MessageHandler(
                filters.VOICE, 
                self._handle_voice_message
            ))
    
    async def _run_polling(self):
        """Запуск polling для получения сообщений"""
        try:
            await self.application.updater.start_polling()
        except Exception as e:
            self.logger.error(f"Ошибка polling: {e}")
    
    async def _check_authorization(self, update: Update) -> bool:
        """Проверка авторизации пользователя"""
        if not self.allowed_chat_ids:
            return True  # Если не настроено, разрешаем всем
            
        chat_id = update.effective_chat.id
        return chat_id in self.allowed_chat_ids
    
    async def _check_rate_limit(self, user_id: int) -> bool:
        """Проверка лимитов пользователя"""
        if not self.moderation_enabled:
            return True
            
        now = datetime.now()
        user_key = str(user_id)
        
        if user_key not in self.rate_limits:
            self.rate_limits[user_key] = {
                'messages': [],
                'images': []
            }
        
        user_limits = self.rate_limits[user_key]
        
        # Очистка старых записей (сообщения за последнюю минуту)
        minute_ago = now - timedelta(minutes=1)
        user_limits['messages'] = [
            msg_time for msg_time in user_limits['messages'] 
            if msg_time > minute_ago
        ]
        
        # Проверка лимита сообщений
        if len(user_limits['messages']) >= MODERATION_CONFIG['rate_limit_messages_per_minute']:
            return False
        
        # Добавление текущего времени
        user_limits['messages'].append(now)
        return True
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        if not await self._check_authorization(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        user_name = update.effective_user.first_name or "Пользователь"
        
        # Инициализация пользователя
        await self._initialize_user(update.effective_user.id, update.effective_chat.id, user_name)
        
        # Использование шаблона приветствия
        welcome_text = format_message_template("welcome", user_name=user_name)
        
        await update.message.reply_text(welcome_text)
        await self._log_conversation(update, "start", "", "command")
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        if not await self._check_authorization(update):
            return
            
        help_text = format_message_template("help")
        await update.message.reply_text(help_text)
    
    async def _cmd_personality(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /personality"""
        if not await self._check_authorization(update):
            return
            
        personalities = {
            'helpful_assistant': 'Полезный помощник - отвечаю четко и по делу',
            'friendly_companion': 'Дружелюбный собеседник - общаюсь тепло и эмоционально',
            'professional_expert': 'Профессиональный эксперт - даю экспертные советы',
            'creative_writer': 'Творческий писатель - отвечаю красиво и образно',
            'technical_specialist': 'Технический специалист - фокусируюсь на технических деталях'
        }
        
        if context.args:
            new_personality = context.args[0].lower()
            if new_personality in personalities:
                await self._update_user_personality(update.effective_user.id, new_personality)
                await update.message.reply_text(
                    f"✅ Стиль общения изменен на: {personalities[new_personality]}"
                )
            else:
                await update.message.reply_text(
                    "❌ Неизвестный стиль. Доступные стили:\n" + 
                    "\n".join([f"• {k} - {v}" for k, v in personalities.items()])
                )
        else:
            current_personality = await self._get_user_personality(update.effective_user.id)
            await update.message.reply_text(
                f"🎭 Текущий стиль: {personalities.get(current_personality, 'Неизвестен')}\n\n" +
                "Доступные стили:\n" + 
                "\n".join([f"• {k} - {v}" for k, v in personalities.items()]) +
                "\n\nИспользуйте: /personality [стиль]"
            )
    
    async def _cmd_clear_context(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /clear"""
        if not await self._check_authorization(update):
            return
            
        chat_id = update.effective_chat.id
        if chat_id in self.active_conversations:
            del self.active_conversations[chat_id]
            
        await update.message.reply_text("🧹 Контекст разговора очищен!")
        await self._log_conversation(update, "clear", "", "command")
    
    async def _cmd_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /settings"""
        if not await self._check_authorization(update):
            return
            
        user_prefs = await self._get_user_preferences(update.effective_user.id)
        
        settings_text = f"""⚙️ Настройки пользователя

👤 Пользователь: {update.effective_user.first_name}
🎭 Стиль общения: {user_prefs.get('personality', 'helpful_assistant')}
🗣️ Язык: {user_prefs.get('language', 'ru')}
📝 Длина контекста: {user_prefs.get('context_length', 10)} сообщений
🖼️ Обработка изображений: {'включена' if user_prefs.get('enable_images', True) else 'отключена'}
🎵 Голосовые сообщения: {'включены' if user_prefs.get('enable_voice', False) else 'отключены'}

Для изменения настроек используйте соответствующие команды:
/personality - изменить стиль общения"""

        await update.message.reply_text(settings_text)
    
    async def _cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stats"""
        if not await self._check_authorization(update):
            return
            
        stats = await self._get_user_statistics(update.effective_user.id, update.effective_chat.id)
        
        stats_text = f"""📊 Статистика использования

📅 За сегодня:
• Отправлено сообщений: {stats.get('messages_today', 0)}
• Получено ответов: {stats.get('responses_today', 0)}
• Обработано изображений: {stats.get('images_today', 0)}
• Среднее время ответа: {stats.get('avg_response_time', 0)}мс

📈 Всего:
• Сообщений: {stats.get('total_messages', 0)}
• Ответов: {stats.get('total_responses', 0)}
• Изображений: {stats.get('total_images', 0)}
• Использовано токенов: {stats.get('total_tokens', 0)}"""

        await update.message.reply_text(stats_text)
    
    async def _cmd_generate_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /generate для генерации изображений"""
        if not await self._check_authorization(update):
            await update.message.reply_text(format_message_template("access_denied"))
            return
            
        # Проверка лимитов
        if not await self._check_rate_limit(update.effective_user.id):
            await update.message.reply_text(format_message_template("rate_limit"))
            return
        
        # Получение промпта из аргументов команды
        if not context.args:
            await update.message.reply_text(
                "🎨 Для генерации изображения укажите описание:\n"
                "/generate красивый закат над морем"
            )
            return
        
        prompt = " ".join(context.args)
        user_name = update.effective_user.first_name or "Пользователь"
        
        # Уведомление о начале генерации
        processing_msg = await update.message.reply_text(
            f"🎨 Генерирую изображение...\n"
            f"📝 Промпт: {prompt}\n"
            f"⏳ Это может занять несколько минут..."
        )
        
        try:
            # Создание задачи генерации изображения
            task_id = await self._create_image_generation_task(
                prompt, 
                update.effective_chat.id,
                update.effective_user.id,
                user_name
            )
            
            if task_id:
                await processing_msg.edit_text(
                    f"✅ Задача генерации создана!\n"
                    f"📝 Промпт: {prompt}\n"
                    f"🆔 ID задачи: {task_id}\n"
                    f"⏳ Ожидайте результат..."
                )
                
                # Логирование команды генерации
                await self._log_conversation(
                    update, f"/generate {prompt}", "", "generate_command"
                )
                
            else:
                await processing_msg.edit_text(
                    "😔 Не удалось создать задачу генерации. "
                    "ImageAgent может быть недоступен."
                )
        
        except Exception as e:
            self.logger.error(f"Ошибка команды генерации: {e}")
            await processing_msg.edit_text(
                "😔 Произошла ошибка при создании задачи генерации. "
                "Попробуйте еще раз."
            )
    
    async def _create_image_generation_task(
        self, 
        prompt: str, 
        chat_id: int, 
        user_id: int,
        user_name: str
    ) -> Optional[str]:
        """Создание задачи генерации изображения через MetaAgent"""
        try:
            url = "http://meta_agent:8000/create_task"
            task_data = {
                "task_type": "image_generation",
                "data": {
                    "prompt": prompt,
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "user_name": user_name,
                    "notify_telegram": True,
                    "quality": "standard",
                    "style": "realistic"
                },
                "priority": 2
            }
            
            async with self.http_session.post(url, json=task_data, timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("task_id")
                else:
                    self.logger.error(f"MetaAgent вернул статус {response.status}")
                    return None
            
        except Exception as e:
            self.logger.error(f"Ошибка создания задачи генерации: {e}")
            return None
    
    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        if not await self._check_authorization(update):
            await update.message.reply_text(format_message_template("access_denied"))
            return
        
        # Проверка лимитов
        if not await self._check_rate_limit(update.effective_user.id):
            await update.message.reply_text(format_message_template("rate_limit"))
            return
        
        start_time = datetime.now()
        message_text = update.message.text
        
        # Проверка длины сообщения
        max_length = MODERATION_CONFIG.get('max_message_length', 4000)
        if len(message_text) > max_length:
            await update.message.reply_text(
                f"⚠️ Сообщение слишком длинное. Максимум {max_length} символов."
            )
            return
        
        # Показать, что бот печатает
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Получение контекста разговора
            context_messages = await self._get_conversation_context(
                update.effective_chat.id, 
                update.effective_user.id
            )
            
            # Получение персональности пользователя
            personality = await self._get_user_personality(update.effective_user.id)
            
            # Генерация ответа через TextAgent
            response = await self._generate_ai_response(
                message_text, 
                context_messages, 
                personality,
                update.effective_user.first_name or "Пользователь"
            )
            
            # Отправка ответа
            await update.message.reply_text(response)
            
            # Подсчет времени ответа
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Логирование разговора
            await self._log_conversation(
                update, message_text, response, "text", 
                personality, response_time
            )
            
            # Обновление статистики
            await self._update_user_statistics(
                update.effective_user.id, 
                update.effective_chat.id,
                messages_sent=1, 
                responses_generated=1,
                response_time=response_time
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(format_message_template("error_general"))
    
    async def _handle_image_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка изображений"""
        if not await self._check_authorization(update):
            return
            
        if not self.enable_image_processing:
            await update.message.reply_text("🖼️ Обработка изображений отключена")
            return
        
        start_time = datetime.now()
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Получение изображения
            photo = update.message.photo[-1]  # Берем самое большое разрешение
            file = await context.bot.get_file(photo.file_id)
            
            # Скачивание изображения
            image_bytes = io.BytesIO()
            await file.download_to_memory(image_bytes)
            image_bytes.seek(0)
            
            # Получение персональности пользователя
            personality = await self._get_user_personality(update.effective_user.id)
            user_name = update.effective_user.first_name or "Пользователь"
            
            # Анализ изображения через VisionAgent
            caption = update.message.caption or "Что на этом изображении?"
            image_analysis = await self._analyze_image(image_bytes.getvalue(), caption)
            
            # Генерация ответа на основе анализа с учетом персональности
            response = await self._generate_image_response(
                image_analysis, caption, personality, user_name
            )
            
            await update.message.reply_text(response)
            
            # Подсчет времени ответа
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Логирование
            await self._log_conversation(
                update, f"[IMAGE] {caption}", response, "image", 
                response_time=response_time
            )
            
            # Обновление статистики
            await self._update_user_statistics(
                update.effective_user.id, 
                update.effective_chat.id,
                images_processed=1,
                response_time=response_time
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки изображения: {e}")
            await update.message.reply_text(
                "😔 Не удалось обработать изображение. Попробуйте еще раз."
            )
    
    async def _handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка голосовых сообщений"""
        await update.message.reply_text(
            "🎵 Обработка голосовых сообщений пока не реализована. "
            "Отправьте текстовое сообщение."
        )
    
    async def _generate_ai_response(
        self, 
        message: str, 
        context_messages: List[Dict], 
        personality: str,
        user_name: str
    ) -> str:
        """Генерация ответа нейросети через TextAgent"""
        try:
            # Получение конфигурации персональности
            personality_config = get_personality_config(personality)
            system_prompt = f"{personality_config['system_prompt']} Пользователя зовут {user_name}."
            
            # Формирование контекста разговора
            context_text = ""
            if context_messages:
                context_text = "\n\nКонтекст разговора:\n"
                for msg in context_messages[-5:]:  # Последние 5 сообщений для контекста
                    role = "Пользователь" if msg['is_user_message'] else "Ассистент"
                    context_text += f"{role}: {msg['message_text']}\n"
            
            # Полный промпт с учетом персональности
            full_prompt = f"{system_prompt}\n{context_text}\nПользователь: {message}\nАссистент:"
            
            # Создание задачи для TextAgent
            task_data = {
                "task_type": "text_generation",
                "data": {
                    "prompt": full_prompt,
                    "max_length": personality_config.get('max_tokens', 512),
                    "temperature": personality_config.get('temperature', 0.7),
                    "top_p": 0.9,
                    "do_sample": True
                }
            }
            
            # Отправка запроса к TextAgent
            url = "http://text_agent:8000/process_task"
            
            async with self.http_session.post(url, json=task_data, timeout=self.response_timeout) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('status') == 'success':
                        generated_text = result.get('generated_text', '').strip()
                        
                        # Очистка ответа от артефактов
                        generated_text = self._clean_ai_response(generated_text)
                        
                        if generated_text:
                            return generated_text
                
                # Логирование ошибки ответа
                self.logger.warning(f"TextAgent вернул неуспешный статус: {response.status}")
            
            # Fallback ответ в случае проблем с TextAgent
            return self._get_fallback_response(personality, user_name)
            
        except asyncio.TimeoutError:
            self.logger.error("Таймаут при обращении к TextAgent")
            return format_message_template("error_timeout")
        except Exception as e:
            self.logger.error(f"Ошибка генерации ответа: {e}")
            return format_message_template("error_general")
    
    def _clean_ai_response(self, response: str) -> str:
        """Очистка ответа от артефактов"""
        # Удаление повторений промпта
        lines = response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Пропускаем строки, которые выглядят как повторения промпта
            if not (line.startswith('Пользователь:') or line.startswith('Ассистент:')):
                cleaned_lines.append(line)
        
        cleaned_response = '\n'.join(cleaned_lines).strip()
        
        # Ограничение длины ответа
        max_length = MODERATION_CONFIG.get('max_message_length', 4000)
        if len(cleaned_response) > max_length:
            cleaned_response = cleaned_response[:max_length-3] + "..."
        
        return cleaned_response
    
    def _get_fallback_response(self, personality: str, user_name: str) -> str:
        """Получение запасного ответа при проблемах с TextAgent"""
        fallback_responses = {
            'helpful_assistant': f"Извините, {user_name}, у меня временные технические трудности. Попробуйте переформулировать вопрос.",
            'friendly_companion': f"Ой, {user_name}! 😔 У меня что-то с мыслями... Попробуй спросить еще раз, пожалуйста! 🤗",
            'professional_expert': f"{user_name}, в данный момент я испытываю технические сложности. Рекомендую повторить запрос.",
            'creative_writer': f"Прости, {user_name}, мой творческий поток временно иссяк... Попробуй вдохновить меня еще раз! ✨",
            'technical_specialist': f"{user_name}, обнаружена техническая проблема в системе генерации. Повторите запрос."
        }
        
        return fallback_responses.get(personality, fallback_responses['helpful_assistant'])
    
    async def _analyze_image(self, image_data: bytes, user_question: str = "") -> Dict[str, Any]:
        """Анализ изображения через VisionAgent"""
        try:
            # Проверка размера файла
            max_size_mb = IMAGE_PROCESSING_CONFIG.get('max_file_size_mb', 10)
            if len(image_data) > max_size_mb * 1024 * 1024:
                return {
                    "status": "error", 
                    "error": f"Файл слишком большой. Максимум {max_size_mb}MB"
                }
            
            # Конвертация в base64 для отправки
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Формирование запроса с учетом пользовательского вопроса
            analysis_type = IMAGE_PROCESSING_CONFIG.get('default_analysis_type', 'detailed_description')
            if user_question:
                analysis_type = 'question_answering'
            
            url = "http://vision_agent:8000/process_task"
            task_data = {
                "task_type": "image_analysis",
                "data": {
                    "image_data": image_b64,
                    "analysis_type": analysis_type,
                    "question": user_question if user_question else "Опиши подробно что на изображении",
                    "language": "ru"
                }
            }
            
            timeout = IMAGE_PROCESSING_CONFIG.get('analysis_timeout', 30)
            async with self.http_session.post(url, json=task_data, timeout=timeout) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('status') == 'success':
                        return result
                    else:
                        return {
                            "status": "error", 
                            "error": result.get('error', 'Неизвестная ошибка анализа')
                        }
                else:
                    return {
                        "status": "error", 
                        "error": f"VisionAgent недоступен (статус: {response.status})"
                    }
            
        except asyncio.TimeoutError:
            self.logger.error("Таймаут при анализе изображения")
            return {"status": "error", "error": "Превышено время ожидания анализа"}
        except Exception as e:
            self.logger.error(f"Ошибка анализа изображения: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _generate_image_response(
        self, 
        image_analysis: Dict[str, Any], 
        user_question: str,
        personality: str = 'helpful_assistant',
        user_name: str = 'Пользователь'
    ) -> str:
        """Генерация ответа на основе анализа изображения"""
        try:
            if image_analysis.get('status') != 'success':
                error_msg = image_analysis.get('error', 'Неизвестная ошибка')
                return f"😔 Не удалось проанализировать изображение: {error_msg}"
            
            # Получение результата анализа
            analysis_result = image_analysis.get('analysis', {})
            description = analysis_result.get('description', 'Изображение обработано')
            objects = analysis_result.get('objects', [])
            colors = analysis_result.get('colors', [])
            
            # Формирование детального описания
            detailed_info = f"Описание: {description}"
            if objects:
                detailed_info += f"\nОбъекты: {', '.join(objects)}"
            if colors:
                detailed_info += f"\nОсновные цвета: {', '.join(colors)}"
            
            # Формирование промпта с учетом персональности
            personality_config = get_personality_config(personality)
            system_prompt = f"{personality_config['system_prompt']} Пользователя зовут {user_name}."
            
            prompt = f"""{system_prompt}

Ты анализируешь изображение для пользователя. Вот результат анализа:

{detailed_info}

Пользователь спрашивает: "{user_question}"

Дай содержательный и полезный ответ на основе анализа изображения:"""

            # Генерация ответа через TextAgent с настройками персональности
            task_data = {
                "task_type": "text_generation",
                "data": {
                    "prompt": prompt,
                    "max_length": personality_config.get('max_tokens', 512),
                    "temperature": personality_config.get('temperature', 0.7),
                    "top_p": 0.9,
                    "do_sample": True
                }
            }
            
            url = "http://text_agent:8000/process_task"
            async with self.http_session.post(url, json=task_data, timeout=self.response_timeout) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('status') == 'success':
                        ai_response = result.get('generated_text', '').strip()
                        ai_response = self._clean_ai_response(ai_response)
                        
                        # Форматирование финального ответа
                        template = IMAGE_PROCESSING_CONFIG.get('response_template', 
                            "🖼️ **Анализ изображения:**\n\n{analysis}\n\n{response}")
                        
                        return template.format(
                            analysis=description,
                            response=ai_response
                        )
            
            # Fallback если TextAgent недоступен
            return f"🖼️ **Анализ изображения:**\n\n{description}"
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации ответа по изображению: {e}")
            return format_message_template("error_image_processing")
    
    async def _get_conversation_context(self, chat_id: int, user_id: int) -> List[Dict]:
        """Получение контекста разговора"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT message_text, response_text, is_user_message, processed_at
                    FROM chat_conversations 
                    WHERE chat_id = $1 AND user_id = $2 
                    ORDER BY processed_at DESC 
                    LIMIT $3
                """, chat_id, user_id, self.max_context_messages)
                
                context = []
                for row in reversed(rows):
                    if row['is_user_message']:
                        context.append({
                            'message_text': row['message_text'],
                            'is_user_message': True,
                            'timestamp': row['processed_at']
                        })
                    if row['response_text']:
                        context.append({
                            'message_text': row['response_text'],
                            'is_user_message': False,
                            'timestamp': row['processed_at']
                        })
                
                return context
                
        except Exception as e:
            self.logger.error(f"Ошибка получения контекста: {e}")
            return []
    
    async def _initialize_user(self, user_id: int, chat_id: int, user_name: str):
        """Инициализация нового пользователя"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO user_preferences (user_id, chat_id, personality, language)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id) DO NOTHING
                """, user_id, chat_id, self.default_personality, 'ru')
                
        except Exception as e:
            self.logger.error(f"Ошибка инициализации пользователя: {e}")
    
    async def _get_user_personality(self, user_id: int) -> str:
        """Получение персональности пользователя"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT personality FROM user_preferences WHERE user_id = $1",
                    user_id
                )
                return result or self.default_personality
                
        except Exception as e:
            self.logger.error(f"Ошибка получения персональности: {e}")
            return self.default_personality
    
    async def _update_user_personality(self, user_id: int, personality: str):
        """Обновление персональности пользователя"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE user_preferences 
                    SET personality = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $2
                """, personality, user_id)
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления персональности: {e}")
    
    async def _get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Получение настроек пользователя"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM user_preferences WHERE user_id = $1",
                    user_id
                )
                return dict(row) if row else {}
                
        except Exception as e:
            self.logger.error(f"Ошибка получения настроек: {e}")
            return {}
    
    async def _log_conversation(
        self, 
        update: Update, 
        message_text: str, 
        response_text: str = "", 
        message_type: str = "text",
        personality: str = None,
        response_time: int = 0
    ):
        """Логирование разговора"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO chat_conversations 
                    (chat_id, user_id, user_name, message_text, message_type, 
                     response_text, response_type, personality, response_time_ms)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, 
                    update.effective_chat.id,
                    update.effective_user.id,
                    update.effective_user.first_name or "Unknown",
                    message_text,
                    message_type,
                    response_text,
                    message_type,
                    personality or self.default_personality,
                    response_time
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка логирования разговора: {e}")
    
    async def _update_user_statistics(
        self, 
        user_id: int, 
        chat_id: int, 
        messages_sent: int = 0,
        responses_generated: int = 0,
        images_processed: int = 0,
        response_time: int = 0
    ):
        """Обновление статистики пользователя"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO chat_statistics 
                    (chat_id, user_id, messages_sent, responses_generated, 
                     images_processed, avg_response_time_ms)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (chat_id, user_id, date) DO UPDATE SET
                    messages_sent = chat_statistics.messages_sent + EXCLUDED.messages_sent,
                    responses_generated = chat_statistics.responses_generated + EXCLUDED.responses_generated,
                    images_processed = chat_statistics.images_processed + EXCLUDED.images_processed,
                    avg_response_time_ms = (chat_statistics.avg_response_time_ms + EXCLUDED.avg_response_time_ms) / 2
                """, chat_id, user_id, messages_sent, responses_generated, images_processed, response_time)
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления статистики: {e}")
    
    async def _get_user_statistics(self, user_id: int, chat_id: int) -> Dict[str, Any]:
        """Получение статистики пользователя"""
        try:
            async with self.db_pool.acquire() as conn:
                # Статистика за сегодня
                today_stats = await conn.fetchrow("""
                    SELECT messages_sent, responses_generated, images_processed, avg_response_time_ms
                    FROM chat_statistics 
                    WHERE user_id = $1 AND chat_id = $2 AND date = CURRENT_DATE
                """, user_id, chat_id)
                
                # Общая статистика
                total_stats = await conn.fetchrow("""
                    SELECT 
                        SUM(messages_sent) as total_messages,
                        SUM(responses_generated) as total_responses,
                        SUM(images_processed) as total_images,
                        AVG(avg_response_time_ms) as avg_response_time
                    FROM chat_statistics 
                    WHERE user_id = $1 AND chat_id = $2
                """, user_id, chat_id)
                
                return {
                    'messages_today': today_stats['messages_sent'] if today_stats else 0,
                    'responses_today': today_stats['responses_generated'] if today_stats else 0,
                    'images_today': today_stats['images_processed'] if today_stats else 0,
                    'avg_response_time': int(today_stats['avg_response_time_ms']) if today_stats else 0,
                    'total_messages': int(total_stats['total_messages']) if total_stats['total_messages'] else 0,
                    'total_responses': int(total_stats['total_responses']) if total_stats['total_responses'] else 0,
                    'total_images': int(total_stats['total_images']) if total_stats['total_images'] else 0,
                    'total_tokens': 0  # Можно добавить подсчет токенов
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    async def _cleanup_old_conversations(self):
        """Периодическая очистка старых диалогов"""
        while self.running:
            try:
                # Очистка каждые 6 часов
                await asyncio.sleep(6 * 3600)
                
                async with self.db_pool.acquire() as conn:
                    # Удаление разговоров старше 30 дней
                    await conn.execute("""
                        DELETE FROM chat_conversations 
                        WHERE processed_at < NOW() - INTERVAL '30 days'
                    """)
                    
                    # Удаление статистики старше 90 дней
                    await conn.execute("""
                        DELETE FROM chat_statistics 
                        WHERE date < CURRENT_DATE - INTERVAL '90 days'
                    """)
                    
                self.logger.info("Выполнена очистка старых диалогов")
                
            except Exception as e:
                self.logger.error(f"Ошибка очистки диалогов: {e}")
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задач TelegramChatAgent"""
        if task.task_type == "send_message":
            chat_id = task.data.get("chat_id")
            message = task.data.get("message")
            
            if chat_id and message:
                try:
                    await self.bot.send_message(chat_id=chat_id, text=message)
                    return {"status": "sent", "chat_id": chat_id}
                except Exception as e:
                    return {"status": "error", "error": str(e)}
        
        elif task.task_type == "broadcast_message":
            message = task.data.get("message")
            sent_count = 0
            
            for chat_id in self.allowed_chat_ids:
                try:
                    await self.bot.send_message(chat_id=chat_id, text=message)
                    sent_count += 1
                except Exception as e:
                    self.logger.error(f"Ошибка отправки в чат {chat_id}: {e}")
            
            return {"status": "broadcast_completed", "sent_count": sent_count}
        
        return {"status": "unknown_task_type"}
    
    async def _cleanup_agent(self):
        """Очистка ресурсов"""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        
        self.logger.info("TelegramChatAgent остановлен")
    
    async def send_notification(self, chat_id: int, message: str):
        """Отправка уведомления"""
        try:
            await self.bot.send_message(chat_id=chat_id, text=message)
            self.logger.info(f"Уведомление отправлено в чат {chat_id}")
        except Exception as e:
            self.logger.error(f"Ошибка отправки уведомления: {e}")