"""
TelegramAgent - агент для работы с Telegram Bot API
Обрабатывает команды пользователей и взаимодействует с другими агентами
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from .base_agent import BaseAgent, Task


class TelegramMessage(BaseModel):
    """Модель Telegram сообщения"""
    chat_id: str
    text: str
    message_type: str = "text"
    reply_markup: Optional[Dict] = None


class TelegramAgent(BaseAgent):
    """Агент для работы с Telegram"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("telegram_agent", config)
        
        # Конфигурация Telegram
        self.bot_token = config.get('telegram_token')
        self.allowed_chat_ids = config.get('telegram_chat_ids', [])
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_TOKEN не найден в конфигурации")
        
        # Telegram Bot
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        
        # FastAPI для HTTP API
        self.app = FastAPI(title="TelegramAgent API", version="3.9")
        self._setup_routes()
        
        # Статистика
        self.message_stats = {
            "received": 0,
            "sent": 0,
            "commands": 0,
            "errors": 0
        }
        
        # Контекст разговоров
        self.conversation_context = {}
    
    def _setup_routes(self):
        """Настройка FastAPI маршрутов"""
        
        @self.app.post("/send_message")
        async def send_message_endpoint(message: TelegramMessage):
            """Отправка сообщения через HTTP API"""
            try:
                await self._send_telegram_message(
                    chat_id=message.chat_id,
                    text=message.text,
                    reply_markup=message.reply_markup
                )
                return {"status": "sent"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/status")
        async def get_status():
            """Статус агента"""
            return await self.health_check()
        
        @self.app.post("/process_task")
        async def process_task_endpoint(task_data: Dict[str, Any]):
            """Обработка задачи через HTTP API"""
            try:
                task = Task(
                    id=task_data["id"],
                    agent_name=task_data["agent_name"],
                    task_type=task_data["task_type"],
                    data=task_data["data"]
                )
                
                result = await self.process_task(task)
                return result
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _initialize_agent(self):
        """Инициализация Telegram агента"""
        self.logger.info("Инициализация TelegramAgent")
        
        # Создаем бота
        self.bot = Bot(token=self.bot_token)
        
        # Создаем приложение
        self.application = Application.builder().token(self.bot_token).build()
        
        # Регистрируем обработчики
        self._register_handlers()
        
        # Запускаем HTTP сервер
        asyncio.create_task(self._start_http_server())
        
        # Запускаем Telegram бота
        asyncio.create_task(self._start_telegram_bot())
        
        self.logger.info("TelegramAgent инициализирован")
    
    async def _start_http_server(self):
        """Запуск HTTP сервера"""
        try:
            config = uvicorn.Config(
                app=self.app,
                host="0.0.0.0",
                port=8002,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            self.logger.error(f"Ошибка запуска HTTP сервера: {e}")
    
    async def _start_telegram_bot(self):
        """Запуск Telegram бота"""
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.logger.info("Telegram бот запущен")
            
            # Отправляем уведомление о запуске
            if self.allowed_chat_ids:
                for chat_id in self.allowed_chat_ids:
                    await self._send_telegram_message(
                        chat_id=str(chat_id),
                        text="🤖 AGI Layer v3.9 запущен и готов к работе!\n\nИспользуйте /help для списка команд."
                    )
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска Telegram бота: {e}")
    
    def _register_handlers(self):
        """Регистрация обработчиков Telegram"""
        
        # Команды
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("status", self._handle_status))
        self.application.add_handler(CommandHandler("generate", self._handle_generate))
        self.application.add_handler(CommandHandler("report", self._handle_report))
        self.application.add_handler(CommandHandler("memory", self._handle_memory))
        
        # Обычные сообщения
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Фотографии
        self.application.add_handler(MessageHandler(filters.PHOTO, self._handle_photo))
        
        # Callback кнопки
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
    
    async def _handle_start(self, update: Update, context):
        """Обработка команды /start"""
        try:
            chat_id = str(update.effective_chat.id)
            
            if not self._is_authorized(chat_id):
                await update.message.reply_text("❌ У вас нет доступа к этому боту.")
                return
            
            self.message_stats["commands"] += 1
            
            welcome_text = """🤖 **AGI Layer v3.9** - Добро пожаловать!
            
Я интеллектуальная система с множественными агентами:

🎨 **Генерация изображений** - создаю картинки по описанию
👁️ **Анализ изображений** - понимаю содержимое фото
🧠 **Память и знания** - запоминаю и ищу информацию
📊 **Отчеты** - анализирую данные и создаю визуализации
⚙️ **Мониторинг** - слежу за работой системы

**Команды:**
/help - список всех команд
/status - статус системы
/generate [описание] - генерация изображения
/report - создать отчет
/memory [запрос] - работа с памятью

Просто отправьте мне сообщение или фото - я пойму что делать! 🚀"""
            
            keyboard = [
                [InlineKeyboardButton("📊 Статус системы", callback_data="status")],
                [InlineKeyboardButton("🎨 Генерация изображения", callback_data="generate")],
                [InlineKeyboardButton("📈 Отчет", callback_data="report")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                welcome_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки /start: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке команды.")
    
    async def _handle_help(self, update: Update, context):
        """Обработка команды /help"""
        try:
            chat_id = str(update.effective_chat.id)
            
            if not self._is_authorized(chat_id):
                return
            
            self.message_stats["commands"] += 1
            
            help_text = """📖 **Справка по командам AGI Layer v3.9**

**🎨 Генерация изображений:**
`/generate красивый закат над океаном`
`/generate портрет девушки в стиле ренессанс`

**👁️ Анализ изображений:**
Просто отправьте фото - я его проанализирую

**🧠 Память и знания:**
`/memory запомни что сегодня хорошая погода`
`/memory найди информацию о Python`

**📊 Отчеты и аналитика:**
`/report создай отчет по задачам за неделю`
`/report статистика использования системы`

**⚙️ Системные команды:**
`/status` - статус всех агентов
`/help` - эта справка

**💬 Естественное общение:**
Можете просто писать мне как обычному собеседнику - я пойму ваши намерения и выполню нужные действия!

**Примеры:**
• "Нарисуй кота в космосе" → генерация изображения
• "Что на этом фото?" + фото → анализ изображения  
• "Запомни мой любимый цвет - синий" → сохранение в память
• "Какая погода была вчера?" → поиск в памяти"""
            
            await update.message.reply_text(help_text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки /help: {e}")
    
    async def _handle_status(self, update: Update, context):
        """Обработка команды /status"""
        try:
            chat_id = str(update.effective_chat.id)
            
            if not self._is_authorized(chat_id):
                return
            
            self.message_stats["commands"] += 1
            
            # Запрашиваем статус у MetaAgent
            result = await self.send_to_agent("meta_agent", "list_agents", {})
            
            if result and result.get("status") == "success":
                active_agents = result.get("active_agents", [])
                
                status_text = f"""📊 **Статус AGI Layer v3.9**

**Активные агенты:** {len(active_agents)}/7

"""
                
                agent_names = {
                    "meta_agent": "🧠 MetaAgent (координатор)",
                    "telegram_agent": "💬 TelegramAgent (этот бот)",
                    "image_gen_agent": "🎨 ImageGenAgent (генерация)",
                    "vision_agent": "👁️ VisionAgent (анализ изображений)",
                    "memory_agent": "🧠 MemoryAgent (память)",
                    "report_agent": "📊 ReportAgent (отчеты)",
                    "watchdog_agent": "⚙️ WatchdogAgent (мониторинг)"
                }
                
                for agent, description in agent_names.items():
                    status = "🟢 Работает" if agent in active_agents else "🔴 Не активен"
                    status_text += f"{description}: {status}\n"
                
                status_text += f"\n**Статистика сообщений:**\n"
                status_text += f"📥 Получено: {self.message_stats['received']}\n"
                status_text += f"📤 Отправлено: {self.message_stats['sent']}\n"
                status_text += f"⚡ Команд: {self.message_stats['commands']}\n"
                status_text += f"❌ Ошибок: {self.message_stats['errors']}\n"
                
            else:
                status_text = "❌ Не удалось получить статус системы"
            
            await update.message.reply_text(status_text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки /status: {e}")
            self.message_stats["errors"] += 1
    
    async def _handle_generate(self, update: Update, context):
        """Обработка команды /generate"""
        try:
            chat_id = str(update.effective_chat.id)
            
            if not self._is_authorized(chat_id):
                return
            
            self.message_stats["commands"] += 1
            
            # Получаем описание изображения
            prompt = " ".join(context.args) if context.args else ""
            
            if not prompt:
                await update.message.reply_text(
                    "❓ Укажите описание изображения:\n`/generate красивый закат над океаном`",
                    parse_mode='Markdown'
                )
                return
            
            # Отправляем уведомление о начале генерации
            status_message = await update.message.reply_text(
                f"🎨 Генерирую изображение: *{prompt}*\n⏳ Это может занять 1-2 минуты...",
                parse_mode='Markdown'
            )
            
            # Отправляем задачу на генерацию
            result = await self.send_to_agent("image_gen_agent", "generate_image", {
                "prompt": prompt,
                "chat_id": chat_id,
                "user_id": str(update.effective_user.id)
            })
            
            if result and result.get("status") == "success":
                # Удаляем статусное сообщение
                await status_message.delete()
                
                # Отправляем результат
                image_path = result.get("image_path")
                if image_path and os.path.exists(image_path):
                    with open(image_path, 'rb') as photo:
                        await update.message.reply_photo(
                            photo=photo,
                            caption=f"🎨 *{prompt}*\n\n✨ Изображение создано AGI Layer v3.9",
                            parse_mode='Markdown'
                        )
                else:
                    await update.message.reply_text(
                        f"✅ Изображение создано!\n🎨 *{prompt}*",
                        parse_mode='Markdown'
                    )
            else:
                await status_message.edit_text(
                    f"❌ Ошибка генерации изображения: {result.get('error', 'Неизвестная ошибка')}"
                )
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки /generate: {e}")
            self.message_stats["errors"] += 1
    
    async def _handle_report(self, update: Update, context):
        """Обработка команды /report"""
        try:
            chat_id = str(update.effective_chat.id)
            
            if not self._is_authorized(chat_id):
                return
            
            self.message_stats["commands"] += 1
            
            # Отправляем задачу на создание отчета
            result = await self.send_to_agent("report_agent", "generate_report", {
                "report_type": "system_status",
                "chat_id": chat_id
            })
            
            if result and result.get("status") == "success":
                report_text = result.get("report", "Отчет создан успешно")
                await update.message.reply_text(
                    f"📊 **Системный отчет**\n\n{report_text}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Ошибка создания отчета")
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки /report: {e}")
    
    async def _handle_memory(self, update: Update, context):
        """Обработка команды /memory"""
        try:
            chat_id = str(update.effective_chat.id)
            
            if not self._is_authorized(chat_id):
                return
            
            self.message_stats["commands"] += 1
            
            query = " ".join(context.args) if context.args else ""
            
            if not query:
                await update.message.reply_text(
                    "❓ Укажите запрос для работы с памятью:\n`/memory запомни что сегодня хорошая погода`\n`/memory найди информацию о Python`",
                    parse_mode='Markdown'
                )
                return
            
            # Определяем тип операции
            if query.lower().startswith(("запомни", "сохрани", "remember")):
                task_type = "memory_store"
                data = {"content": query, "user_id": str(update.effective_user.id)}
            else:
                task_type = "memory_search"
                data = {"query": query, "user_id": str(update.effective_user.id)}
            
            result = await self.send_to_agent("memory_agent", task_type, data)
            
            if result and result.get("status") == "success":
                response = result.get("response", "Операция выполнена")
                await update.message.reply_text(f"🧠 {response}")
            else:
                await update.message.reply_text("❌ Ошибка работы с памятью")
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки /memory: {e}")
    
    async def _handle_message(self, update: Update, context):
        """Обработка обычных сообщений"""
        try:
            chat_id = str(update.effective_chat.id)
            
            if not self._is_authorized(chat_id):
                return
            
            self.message_stats["received"] += 1
            
            message_text = update.message.text
            user_id = str(update.effective_user.id)
            
            # Анализируем намерение пользователя
            intent = await self._analyze_message_intent(message_text)
            
            if intent == "image_generation":
                # Генерация изображения
                await self._handle_natural_generate(update, message_text)
            elif intent == "question":
                # Поиск в памяти или общий ответ
                await self._handle_natural_question(update, message_text)
            elif intent == "memory_store":
                # Сохранение в память
                await self._handle_natural_memory(update, message_text)
            else:
                # Общее взаимодействие
                await self._handle_natural_conversation(update, message_text)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения: {e}")
            self.message_stats["errors"] += 1
    
    async def _handle_photo(self, update: Update, context):
        """Обработка фотографий"""
        try:
            chat_id = str(update.effective_chat.id)
            
            if not self._is_authorized(chat_id):
                return
            
            self.message_stats["received"] += 1
            
            # Получаем фото
            photo = update.message.photo[-1]  # Берем самое большое разрешение
            file = await photo.get_file()
            
            # Сохраняем временно
            photo_path = f"/workspace/data/temp_photo_{datetime.now().timestamp()}.jpg"
            await file.download_to_drive(photo_path)
            
            # Отправляем на анализ
            status_message = await update.message.reply_text("👁️ Анализирую изображение...")
            
            result = await self.send_to_agent("vision_agent", "analyze_image", {
                "image_path": photo_path,
                "chat_id": chat_id
            })
            
            if result and result.get("status") == "success":
                analysis = result.get("analysis", "Изображение проанализировано")
                await status_message.edit_text(f"👁️ **Анализ изображения:**\n\n{analysis}")
            else:
                await status_message.edit_text("❌ Ошибка анализа изображения")
            
            # Удаляем временный файл
            if os.path.exists(photo_path):
                os.remove(photo_path)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки фото: {e}")
    
    async def _handle_callback(self, update: Update, context):
        """Обработка callback кнопок"""
        try:
            query = update.callback_query
            await query.answer()
            
            chat_id = str(query.message.chat.id)
            
            if not self._is_authorized(chat_id):
                return
            
            data = query.data
            
            if data == "status":
                await self._handle_status(update, context)
            elif data == "generate":
                await query.message.reply_text(
                    "🎨 Для генерации изображения используйте:\n`/generate [описание]`\n\nНапример: `/generate красивый закат`",
                    parse_mode='Markdown'
                )
            elif data == "report":
                await self._handle_report(update, context)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки callback: {e}")
    
    async def _analyze_message_intent(self, message: str) -> str:
        """Анализ намерения пользователя"""
        message_lower = message.lower()
        
        # Генерация изображений
        if any(word in message_lower for word in [
            "нарисуй", "создай", "сгенерируй", "изображение", "картинку", "фото"
        ]):
            return "image_generation"
        
        # Сохранение в память
        if any(word in message_lower for word in [
            "запомни", "сохрани", "remember", "note"
        ]):
            return "memory_store"
        
        # Вопросы
        if any(word in message_lower for word in [
            "что", "как", "где", "когда", "почему", "зачем", "?"
        ]):
            return "question"
        
        return "conversation"
    
    async def _handle_natural_generate(self, update: Update, message_text: str):
        """Естественная генерация изображения"""
        # Извлекаем описание
        prompt = message_text
        for word in ["нарисуй", "создай", "сгенерируй", "изображение", "картинку"]:
            prompt = prompt.replace(word, "").strip()
        
        # Вызываем генерацию
        context = type('Context', (), {'args': prompt.split()})()
        await self._handle_generate(update, context)
    
    async def _handle_natural_question(self, update: Update, message_text: str):
        """Обработка естественных вопросов"""
        result = await self.send_to_agent("memory_agent", "memory_search", {
            "query": message_text,
            "user_id": str(update.effective_user.id)
        })
        
        if result and result.get("status") == "success":
            response = result.get("response", "Информация найдена")
            await update.message.reply_text(f"🧠 {response}")
        else:
            await update.message.reply_text("🤔 Интересный вопрос! Пока не могу на него ответить, но запомню его.")
    
    async def _handle_natural_memory(self, update: Update, message_text: str):
        """Естественное сохранение в память"""
        result = await self.send_to_agent("memory_agent", "memory_store", {
            "content": message_text,
            "user_id": str(update.effective_user.id)
        })
        
        if result and result.get("status") == "success":
            await update.message.reply_text("✅ Запомнил!")
        else:
            await update.message.reply_text("❌ Не удалось сохранить в память")
    
    async def _handle_natural_conversation(self, update: Update, message_text: str):
        """Естественный разговор"""
        responses = [
            "Понимаю! Это интересная тема.",
            "Хорошо, учту это.",
            "Спасибо за информацию!",
            "Интересно! Расскажите подробнее.",
            "Понял вас. Чем еще могу помочь?"
        ]
        
        import random
        response = random.choice(responses)
        await update.message.reply_text(response)
    
    def _is_authorized(self, chat_id: str) -> bool:
        """Проверка авторизации пользователя"""
        if not self.allowed_chat_ids:
            return True  # Если список пуст, разрешаем всем
        
        try:
            return int(chat_id) in self.allowed_chat_ids
        except ValueError:
            return False
    
    async def _send_telegram_message(self, chat_id: str, text: str, reply_markup=None):
        """Отправка сообщения в Telegram"""
        try:
            if self.bot:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                self.message_stats["sent"] += 1
        except Exception as e:
            self.logger.error(f"Ошибка отправки сообщения: {e}")
            self.message_stats["errors"] += 1
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задач от других агентов"""
        try:
            if task.task_type == "send_message":
                data = task.data
                await self._send_telegram_message(
                    chat_id=data.get("chat_id"),
                    text=data.get("text"),
                    reply_markup=data.get("reply_markup")
                )
                return {"status": "success", "message": "Сообщение отправлено"}
            
            elif task.task_type == "ping":
                return {"status": "success", "message": "pong"}
            
            else:
                return {"status": "error", "error": f"Неизвестный тип задачи: {task.task_type}"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _cleanup_agent(self):
        """Очистка ресурсов"""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()


# Функция запуска
async def run_telegram_agent(config: Dict[str, Any]):
    """Запуск Telegram агента"""
    agent = TelegramAgent(config)
    await agent.initialize()
    await agent.start()
    
    try:
        while agent.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Получен сигнал остановки")
    finally:
        await agent.stop()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    config = {
        'telegram_token': os.getenv('TELEGRAM_TOKEN'),
        'telegram_chat_ids': [int(x.strip()) for x in os.getenv('TELEGRAM_CHAT_IDS', '').split(',') if x.strip()],
        'postgres_host': os.getenv('POSTGRES_HOST', 'localhost'),
        'postgres_port': int(os.getenv('POSTGRES_PORT', 5432)),
        'postgres_db': os.getenv('POSTGRES_DB', 'agi_layer'),
        'postgres_user': os.getenv('POSTGRES_USER', 'agi_user'),
        'postgres_password': os.getenv('POSTGRES_PASSWORD', 'agi_password')
    }
    
    asyncio.run(run_telegram_agent(config))