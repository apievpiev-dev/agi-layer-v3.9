#!/usr/bin/env python3
"""
Расширенный Telegram чат-бот для AGI Layer v3.9
Интеграция со всеми нейросетевыми агентами
"""

import asyncio
import logging
import aiohttp
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

# Импорты агентов
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from config.settings import settings
from agents.chat_coordinator import ChatCoordinator

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AGITelegramBot:
    """Расширенный Telegram бот с интеграцией нейросетей"""
    
    def __init__(self):
        self.token = settings.TELEGRAM_TOKEN or "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
        self.allowed_chat_id = settings.TELEGRAM_CHAT_ID or "458589236"
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        
        # Координатор чата с нейросетями
        self.chat_coordinator: Optional[ChatCoordinator] = None
        
        # Состояние активных задач
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        
        # HTTP сессия для API запросов
        self.http_session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """Инициализация бота и агентов"""
        logger.info("🚀 Инициализация AGI Telegram бота...")
        
        # Создание HTTP сессии
        self.http_session = aiohttp.ClientSession()
        
        # Инициализация Telegram бота
        self.bot = Bot(token=self.token)
        self.application = Application.builder().token(self.token).build()
        
        # Регистрация обработчиков
        await self._register_handlers()
        
        # Инициализация координатора чата
        await self._initialize_chat_coordinator()
        
        logger.info("✅ AGI Telegram бот инициализирован")
    
    async def _register_handlers(self):
        """Регистрация обработчиков команд и сообщений"""
        # Команды
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("help", self._cmd_help))
        self.application.add_handler(CommandHandler("chat", self._cmd_chat))
        self.application.add_handler(CommandHandler("generate", self._cmd_generate))
        self.application.add_handler(CommandHandler("analyze", self._cmd_analyze))
        self.application.add_handler(CommandHandler("status", self._cmd_status))
        self.application.add_handler(CommandHandler("clear", self._cmd_clear))
        self.application.add_handler(CommandHandler("models", self._cmd_models))
        
        # Обработка обычных сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_message))
        self.application.add_handler(MessageHandler(filters.PHOTO, self._handle_photo_message))
        self.application.add_handler(MessageHandler(filters.Document.IMAGE, self._handle_image_document))
        
        # Обработка callback запросов от inline кнопок
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
    
    async def _initialize_chat_coordinator(self):
        """Инициализация координатора чата"""
        try:
            logger.info("🤖 Инициализация ChatCoordinator...")
            
            # Конфигурация для координатора
            coordinator_config = {
                'models_path': settings.MODELS_PATH,
                'output_path': '/workspace/output',
                'postgres': {
                    'host': settings.POSTGRES_HOST,
                    'port': settings.POSTGRES_PORT,
                    'database': settings.POSTGRES_DB,
                    'user': settings.POSTGRES_USER,
                    'password': settings.POSTGRES_PASSWORD
                }
            }
            
            # Создание и инициализация координатора
            self.chat_coordinator = ChatCoordinator(coordinator_config)
            await self.chat_coordinator.initialize()
            
            logger.info("✅ ChatCoordinator инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации ChatCoordinator: {e}")
            logger.info("Работаем в базовом режиме")
    
    async def _check_authorization(self, update: Update) -> bool:
        """Проверка авторизации пользователя"""
        if not self.allowed_chat_id:
            return True
        
        chat_id = str(update.effective_chat.id)
        return chat_id == self.allowed_chat_id
    
    async def _get_chat_session(self, chat_id: int) -> Dict[str, Any]:
        """Получение или создание сессии чата через координатор"""
        if self.chat_coordinator:
            return await self.chat_coordinator.get_chat_session(chat_id)
        else:
            # Fallback для случая если координатор не инициализирован
            return {
                'history': [],
                'mode': 'chat',
                'context': {},
                'created_at': datetime.now(),
                'message_count': 0
            }
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        if not await self._check_authorization(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        user_name = update.effective_user.first_name or "Пользователь"
        
        welcome_text = f"""🤖 **AGI Layer v3.9 - Чат с нейросетями**

Привет, {user_name}! Я - ваш персональный ИИ-ассистент с доступом к нескольким нейросетям.

**🧠 Доступные возможности:**
• 💬 Чат с текстовой нейросетью (Phi-2)
• 🎨 Генерация изображений (Stable Diffusion)
• 👁️ Анализ изображений (BLIP2)
• 📊 Анализ текста и документов

**🚀 Команды:**
/chat - Начать диалог с нейросетью
/generate [описание] - Генерация изображения
/analyze - Анализ изображения (пришлите фото)
/status - Статус системы
/models - Информация о моделях
/clear - Очистить историю
/help - Помощь

**Просто пишите мне, и я буду отвечать как умная нейросеть!** ✨"""
        
        keyboard = [
            [
                InlineKeyboardButton("💬 Начать чат", callback_data="mode_chat"),
                InlineKeyboardButton("🎨 Генерация", callback_data="mode_generate")
            ],
            [
                InlineKeyboardButton("👁️ Анализ", callback_data="mode_analyze"),
                InlineKeyboardButton("📊 Статус", callback_data="status")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        if not await self._check_authorization(update):
            return
        
        help_text = """🤖 **AGI Layer v3.9 - Справка**

**📝 Команды:**
• `/start` - Главное меню
• `/chat` - Режим чата с нейросетью
• `/generate [описание]` - Генерация изображения
• `/analyze` - Анализ изображения (отправьте фото)
• `/status` - Статус всех систем
• `/models` - Информация о нейросетях
• `/clear` - Очистить историю диалога

**💬 Режимы работы:**
1. **Чат** - Общение с текстовой нейросетью Phi-2
2. **Генерация** - Создание изображений через Stable Diffusion
3. **Анализ** - Описание изображений через BLIP2

**🎯 Примеры использования:**
• `Расскажи мне про космос`
• `/generate красивый закат над морем`
• Отправить фото + `/analyze`

**⚡ Быстрые действия:**
Просто пишите сообщения - я автоматически выберу лучший режим ответа!"""
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def _cmd_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /chat - переключение в режим чата"""
        if not await self._check_authorization(update):
            return
        
        chat_id = update.effective_chat.id
        session = await self._get_chat_session(chat_id)
        session['mode'] = 'chat'
        
        await update.message.reply_text(
            "💬 **Режим чата активирован!**\n\n"
            "Теперь я буду отвечать на ваши сообщения как умная нейросеть. "
            "Задавайте любые вопросы, и я постараюсь дать развернутые ответы!\n\n"
            "🧠 *Используется модель: Phi-2*",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _cmd_generate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /generate - генерация изображения"""
        if not await self._check_authorization(update):
            return
        
        prompt = " ".join(context.args) if context.args else ""
        
        if not prompt:
            keyboard = [
                [InlineKeyboardButton("🌅 Закат", callback_data="gen_beautiful sunset over ocean")],
                [InlineKeyboardButton("🏔️ Горы", callback_data="gen_majestic mountains landscape")],
                [InlineKeyboardButton("🌸 Цветы", callback_data="gen_beautiful flowers garden")],
                [InlineKeyboardButton("🚗 Автомобиль", callback_data="gen_futuristic sports car")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🎨 **Генерация изображений**\n\n"
                "Опишите, что хотите создать:\n"
                "`/generate красивый закат над морем`\n\n"
                "Или выберите готовый вариант:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            return
        
        await self._generate_image(update, prompt)
    
    async def _cmd_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /analyze - анализ изображения"""
        if not await self._check_authorization(update):
            return
        
        chat_id = update.effective_chat.id
        session = await self._get_chat_session(chat_id)
        session['mode'] = 'analyze'
        
        await update.message.reply_text(
            "👁️ **Режим анализа изображений активирован!**\n\n"
            "Пришлите мне изображение, и я опишу что на нем изображено.\n\n"
            "🧠 *Используется модель: BLIP2*\n\n"
            "Поддерживаемые форматы: JPG, PNG, WebP",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status - статус системы"""
        if not await self._check_authorization(update):
            return
        
        # Получаем статус от координатора
        if self.chat_coordinator:
            coordinator_status = await self.chat_coordinator.get_status()
        else:
            coordinator_status = {"demo_mode": True, "active_chats": 0, "agents": {}}
        
        status_text = "📊 **Статус AGI Layer v3.9**\n\n"
        
        # Статус агентов
        demo_mode = coordinator_status.get("demo_mode", True)
        mode_text = "🟡 Демо режим" if demo_mode else "🟢 Активен"
        
        agents_status = {
            "🤖 Chat Coordinator": "🟢 Активен",
            "📝 Text Agent (Phi-2)": mode_text,
            "🎨 Image Agent (SD1.5)": mode_text, 
            "👁️ Vision Agent (BLIP2)": mode_text,
            "📱 Telegram Bot": "🟢 Активен"
        }
        
        for agent, status in agents_status.items():
            status_text += f"{agent}: {status}\n"
        
        status_text += f"\n📈 **Статистика:**\n"
        status_text += f"• Активных чатов: {coordinator_status.get('active_chats', 0)}\n"
        status_text += f"• Режим работы: {'Демо' if demo_mode else 'Полный'}\n"
        status_text += f"• Время: {datetime.now().strftime('%H:%M:%S')}\n"
        status_text += f"• Версия: v3.9.0\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="refresh_status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            status_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def _cmd_models(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /models - информация о моделях"""
        if not await self._check_authorization(update):
            return
        
        models_text = """🧠 **Нейросетевые модели AGI Layer**

**📝 Текстовая модель:**
• **Phi-2** - Microsoft
• Параметры: 2.7B
• Назначение: Генерация текста, диалог
• Режим: CPU-only

**🎨 Генерация изображений:**
• **Stable Diffusion 1.5** - RunwayML
• Разрешение: 512x512
• Назначение: Создание изображений по тексту
• Режим: CPU-only

**👁️ Анализ изображений:**
• **BLIP2** - Salesforce
• Параметры: 2.7B (OPT)
• Назначение: Описание изображений, VQA
• Режим: CPU-only

**⚡ Особенности:**
• Все модели оптимизированы для CPU
• Быстрая инициализация
• Экономное использование памяти
• Поддержка русского языка"""
        
        await update.message.reply_text(models_text, parse_mode=ParseMode.MARKDOWN)
    
    async def _cmd_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /clear - очистка истории"""
        if not await self._check_authorization(update):
            return
        
        chat_id = update.effective_chat.id
        if chat_id in self.chat_sessions:
            del self.chat_sessions[chat_id]
        
        await update.message.reply_text(
            "🧹 **История диалога очищена!**\n\n"
            "Начинаем с чистого листа. Используйте /start для выбора режима.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        if not await self._check_authorization(update):
            return
        
        chat_id = update.effective_chat.id
        session = await self._get_chat_session(chat_id)
        message_text = update.message.text
        
        # Показываем индикатор печати
        await context.bot.send_chat_action(chat_id=chat_id, action='typing')
        
        # Обработка в зависимости от режима
        if session['mode'] == 'generate' or message_text.lower().startswith(('создай', 'нарисуй', 'сгенерируй')):
            await self._generate_image(update, message_text)
        else:
            # Режим чата по умолчанию - используем координатор
            await self._process_chat_message(update, message_text)
    
    async def _process_chat_message(self, update: Update, message: str):
        """Обработка сообщения в режиме чата"""
        try:
            chat_id = update.effective_chat.id
            user_name = update.effective_user.first_name or "Пользователь"
            
            if self.chat_coordinator:
                # Используем координатор для обработки сообщения
                response = await self.chat_coordinator.process_text_message(chat_id, message, user_name)
            else:
                # Fallback - базовый ответ
                response = "Система инициализируется. Попробуйте еще раз через несколько секунд."
            
            # Отправляем ответ
            await update.message.reply_text(
                f"🤖 {response}",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке сообщения. Попробуйте еще раз."
            )
    
    
    async def _generate_image(self, update: Update, prompt: str):
        """Генерация изображения"""
        try:
            chat_id = update.effective_chat.id
            
            # Показываем индикатор загрузки
            await update.message.reply_text(
                f"🎨 **Генерирую изображение...**\n\n"
                f"📝 Описание: `{prompt}`\n"
                f"⏳ Это может занять некоторое время...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            if self.chat_coordinator:
                # Используем координатор для генерации изображения
                result = await self.chat_coordinator.process_image_generation(chat_id, prompt)
                
                if result["status"] == "success":
                    # Реальная генерация успешна
                    demo_text = f"""✅ **Изображение создано!** 🎨

📝 **Промпт:** {prompt}
🤖 **Модель:** Stable Diffusion 1.5
📁 **Файл:** {result.get('filename', 'generated_image.png')}
📅 **Создано:** {datetime.now().strftime('%H:%M:%S')}

Изображение сохранено и готово к использованию!"""
                    
                elif result["status"] == "demo":
                    # Демо режим
                    demo_text = f"""✅ **Изображение готово!** 🎨

📝 **Промпт:** {prompt}
🤖 **Модель:** Stable Diffusion 1.5
⚙️ **Параметры:** 512x512, 20 steps
📅 **Создано:** {datetime.now().strftime('%H:%M:%S')}

*В демо режиме изображения не генерируются, но вся система готова к работе!*

🚀 **Для полной функциональности запустите полную систему:**
`docker-compose up -d`"""
                    
                else:
                    # Ошибка
                    demo_text = f"❌ Ошибка генерации: {result.get('error', 'Неизвестная ошибка')}"
            else:
                # Fallback
                demo_text = "⚠️ Система генерации изображений недоступна"
            
            keyboard = [
                [
                    InlineKeyboardButton("🎨 Еще изображение", callback_data="mode_generate"),
                    InlineKeyboardButton("💬 В чат", callback_data="mode_chat")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                demo_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации изображения: {e}")
            await update.message.reply_text(
                f"❌ Ошибка генерации изображения: {str(e)}"
            )
    
    async def _handle_photo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка фотографий"""
        if not await self._check_authorization(update):
            return
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        try:
            chat_id = update.effective_chat.id
            
            # Получаем файл изображения
            photo = update.message.photo[-1]  # Берем самое большое разрешение
            file = await context.bot.get_file(photo.file_id)
            
            # Скачиваем файл (для демо просто получаем путь)
            file_path = f"/tmp/photo_{photo.file_id}.jpg"
            # await file.download_to_drive(file_path)
            
            if self.chat_coordinator:
                # Используем координатор для анализа изображения
                result = await self.chat_coordinator.process_image_analysis(chat_id, file_path)
                
                if result["status"] == "success":
                    # Реальный анализ успешен
                    analysis_text = f"""👁️ **Анализ изображения завершен!**

📷 **Изображение:** {photo.width}x{photo.height}
🤖 **Модель:** BLIP2 (Salesforce)
📅 **Время:** {datetime.now().strftime('%H:%M:%S')}

🔍 **Описание:** {result.get('caption', 'Анализ выполнен')}

Изображение успешно проанализировано!"""
                    
                elif result["status"] == "demo":
                    # Демо режим
                    analysis_text = f"""👁️ **Анализ изображения**

📷 **Получено:** Изображение {photo.width}x{photo.height}
🤖 **Модель:** BLIP2 (Salesforce)
📅 **Время:** {datetime.now().strftime('%H:%M:%S')}

🔍 **Возможности анализа:**
• Описание содержимого изображения
• Ответы на вопросы об изображении  
• Классификация объектов
• Определение сцены и контекста

*В демо режиме анализ недоступен, но система готова к работе!*

🚀 **Для полной функциональности запустите:**
`docker-compose up -d`"""
                    
                else:
                    # Ошибка
                    analysis_text = f"❌ Ошибка анализа: {result.get('error', 'Неизвестная ошибка')}"
            else:
                # Fallback
                analysis_text = "⚠️ Система анализа изображений недоступна"
            
            keyboard = [
                [
                    InlineKeyboardButton("📷 Еще фото", callback_data="mode_analyze"),
                    InlineKeyboardButton("💬 В чат", callback_data="mode_chat")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                analysis_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Ошибка анализа изображения: {e}")
            await update.message.reply_text(
                f"❌ Ошибка анализа изображения: {str(e)}"
            )
    
    async def _handle_image_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка изображений, отправленных как документы"""
        await self._handle_photo_message(update, context)
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на inline кнопки"""
        query = update.callback_query
        await query.answer()
        
        chat_id = query.message.chat_id
        data = query.data
        
        if data.startswith("mode_"):
            # Переключение режима
            mode = data.split("_")[1]
            session = await self._get_chat_session(chat_id)
            session['mode'] = mode
            
            mode_messages = {
                'chat': "💬 Режим чата активирован! Пишите сообщения.",
                'generate': "🎨 Режим генерации активирован! Опишите что создать.",
                'analyze': "👁️ Режим анализа активирован! Пришлите изображение."
            }
            
            await query.edit_message_text(
                mode_messages.get(mode, "Режим изменен"),
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif data.startswith("gen_"):
            # Быстрая генерация
            prompt = data[4:]  # Убираем префикс "gen_"
            await self._generate_image_from_callback(query, prompt)
            
        elif data == "status":
            # Обновление статуса
            await self._show_status_callback(query)
            
        elif data == "refresh_status":
            # Обновление статуса
            await self._show_status_callback(query)
    
    async def _generate_image_from_callback(self, query, prompt: str):
        """Генерация изображения из callback"""
        await query.edit_message_text(
            f"🎨 Генерирую: {prompt}...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Имитируем генерацию
        await asyncio.sleep(2)
        
        result_text = f"""✅ **Изображение готово!**

📝 **Описание:** {prompt}
🤖 **Модель:** Stable Diffusion 1.5
📅 **Время:** {datetime.now().strftime('%H:%M:%S')}

*Демо режим - полная генерация доступна при запуске через Docker*"""
        
        keyboard = [
            [InlineKeyboardButton("🎨 Еще", callback_data="mode_generate")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            result_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def _show_status_callback(self, query):
        """Показ статуса через callback"""
        # Получаем статус от координатора
        if self.chat_coordinator:
            coordinator_status = await self.chat_coordinator.get_status()
        else:
            coordinator_status = {"demo_mode": True, "active_chats": 0, "agents": {}}
        
        demo_mode = coordinator_status.get("demo_mode", True)
        mode_text = "🟡 Демо режим" if demo_mode else "🟢 Активен"
        
        status_text = f"""📊 **Статус AGI Layer v3.9**

🤖 **Агенты:**
• Chat Coordinator: 🟢 Активен
• Text Agent: {mode_text}
• Image Agent: {mode_text}
• Vision Agent: {mode_text}
• Telegram Bot: 🟢 Активен

📈 **Статистика:**
• Активных чатов: {coordinator_status.get('active_chats', 0)}
• Режим: {'Демо' if demo_mode else 'Полный'}
• Время: {datetime.now().strftime('%H:%M:%S')}
• Версия: v3.9.0"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="refresh_status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            status_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def run(self):
        """Запуск бота"""
        try:
            logger.info("🚀 Запуск AGI Telegram бота...")
            
            await self.application.initialize()
            await self.application.start()
            
            # Отправка уведомления о запуске
            if self.allowed_chat_id:
                try:
                    await self.bot.send_message(
                        chat_id=int(self.allowed_chat_id),
                        text="🚀 **AGI Layer v3.9 запущен!**\n\nБот готов к работе. Используйте /start для начала.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.warning(f"Не удалось отправить уведомление о запуске: {e}")
            
            # Запуск polling
            logger.info("✅ Бот запущен и готов к работе!")
            await self.application.updater.start_polling(drop_pending_updates=True)
            
            # Ожидание завершения
            await self.application.updater.idle()
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Очистка ресурсов"""
        logger.info("🧹 Очистка ресурсов...")
        
        if self.chat_coordinator:
            await self.chat_coordinator.cleanup()
        
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        
        if self.http_session:
            await self.http_session.close()
        
        logger.info("✅ Ресурсы очищены")


async def main():
    """Основная функция"""
    bot = AGITelegramBot()
    
    try:
        await bot.initialize()
        await bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал завершения")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await bot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())