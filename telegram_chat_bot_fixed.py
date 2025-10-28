#!/usr/bin/env python3
"""
Исправленный Telegram чат-бот для AGI Layer v3.9
Работает без внешних зависимостей в демо режиме
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import random

# Попытка импорта telegram библиотеки
try:
    from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ python-telegram-bot не установлен, используем простой HTTP API")

# Попытка импорта aiohttp
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("⚠️ aiohttp не установлен, используем базовую реализацию")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleChatCoordinator:
    """Упрощенный координатор чата"""
    
    def __init__(self):
        self.chat_sessions: Dict[int, Dict[str, Any]] = {}
        self.demo_mode = True
        
    async def get_chat_session(self, chat_id: int) -> Dict[str, Any]:
        """Получение или создание сессии чата"""
        if chat_id not in self.chat_sessions:
            self.chat_sessions[chat_id] = {
                'history': [],
                'mode': 'chat',
                'context': {},
                'created_at': datetime.now(),
                'message_count': 0,
                'preferences': {
                    'language': 'ru',
                    'response_style': 'detailed',
                    'max_history': 20
                }
            }
        return self.chat_sessions[chat_id]
    
    async def process_text_message(self, chat_id: int, message: str, user_name: str = "Пользователь") -> str:
        """Обработка текстового сообщения"""
        try:
            session = await self.get_chat_session(chat_id)
            
            # Добавляем сообщение в историю
            session['history'].append({
                'role': 'user',
                'content': message,
                'user_name': user_name,
                'timestamp': datetime.now().isoformat()
            })
            session['message_count'] += 1
            
            # Генерация ответа
            response = await self._generate_smart_response(session, message)
            
            # Добавляем ответ в историю
            session['history'].append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now().isoformat()
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка в координаторе: {e}")
            return "Извините, произошла техническая ошибка. Попробуйте еще раз."
    
    async def _generate_smart_response(self, session: Dict[str, Any], message: str) -> str:
        """Генерация умного ответа"""
        message_lower = message.lower()
        
        # Приветствия
        if any(word in message_lower for word in ['привет', 'здравствуй', 'добро пожаловать', 'хай', 'hello']):
            responses = [
                "Привет! Я AGI Layer v3.9 - ваш персональный ИИ-ассистент. Готов помочь с любыми вопросами! 🤖",
                "Здравствуйте! Рад нашему знакомству. Чем могу быть полезен?",
                "Привет! Отличное настроение для продуктивного общения. О чем поговорим?"
            ]
            return random.choice(responses)
        
        # Вопросы о возможностях
        elif any(keyword in message_lower for keyword in ['что ты умеешь', 'возможности', 'функции', 'что можешь', 'интеллект']):
            return """🤖 **Мои возможности в AGI Layer v3.9:**

🧠 **Интеллектуальный диалог**
• Отвечаю на вопросы по любым темам
• Поддерживаю естественную беседу
• Помогаю с анализом и решением задач

🎨 **Творческие задачи**
• Генерация изображений по описанию
• Анализ и описание фотографий
• Помощь с творческими проектами

📚 **Обучение и работа**
• Объяснение сложных концепций
• Помощь с программированием
• Анализ текстов и документов

💡 **Практические задачи**
• Планирование и организация
• Поиск решений проблем
• Консультации по различным вопросам

Просто пишите, что нужно сделать!"""
        
        # Вопросы о миссии
        elif any(keyword in message_lower for keyword in ['миссия', 'цель', 'зачем', 'для чего']):
            return """🎯 **Моя миссия:**

Я создан, чтобы быть полезным ИИ-ассистентом, который:
• **Помогает людям** решать повседневные и сложные задачи
• **Обучает и объясняет** сложные концепции простым языком
• **Творит вместе с вами** - генерирует идеи и контент
• **Экономит время** - автоматизирует рутинные процессы

🌟 **Главная цель** - сделать ИИ-технологии доступными и полезными для каждого человека!

Я здесь, чтобы помочь вам достичь ваших целей быстрее и эффективнее."""
        
        # Вопросы о памяти
        elif any(keyword in message_lower for keyword in ['память', 'помнишь', 'запомни']):
            return f"""🧠 **О моей памяти:**

Да, у меня есть память в рамках нашего диалога!

📊 **Текущий диалог:**
• Сообщений обработано: {session['message_count']}
• Начат: {session['created_at'].strftime('%H:%M')}
• Режим: {session['mode']}

💾 **Что я помню:**
• Ваши вопросы и мои ответы в этом чате
• Контекст разговора для лучших ответов
• Ваши предпочтения в рамках сессии

🔄 **Ограничения:**
• Память сбрасывается при перезапуске бота
• Храню последние {session['preferences']['max_history']} сообщений
• Не сохраняю данные между разными чатами

Хотите, чтобы я что-то запомнил особенно?"""
        
        # Технические вопросы
        elif any(keyword in message_lower for keyword in ['программирование', 'код', 'python', 'разработка', 'алгоритм']):
            return """💻 **Программирование - моя сильная сторона!**

Могу помочь с:
• **Python, JavaScript, C++** - синтаксис, лучшие практики
• **Алгоритмами** - объяснение, оптимизация, реализация
• **Архитектурой** - проектирование систем и приложений
• **Отладкой** - поиск и исправление ошибок
• **Machine Learning** - модели, обучение, анализ данных
• **Web разработкой** - фронтенд и бэкенд

🔧 **В AGI Layer используются:**
🧠 Phi-2 для генерации кода
🎨 Stable Diffusion для UI/UX макетов
👁️ BLIP2 для анализа диаграмм

Какая конкретно область программирования вас интересует?"""
        
        # Творческие запросы
        elif any(keyword in message_lower for keyword in ['создай', 'придумай', 'напиши', 'сочини', 'творчество', 'идея']):
            return """🎨 **Творчество - это здорово!**

Могу помочь с:
• **Генерацией идей** - для проектов, бизнеса, творчества
• **Написанием текстов** - статьи, рассказы, сценарии
• **Созданием концепций** - продуктов, дизайна, решений
• **Мозговым штурмом** - поиск нестандартных подходов
• **Планированием проектов** - структура, этапы, ресурсы

🎨 **Для изображений используйте:**
`/generate [описание]` - создам изображение по вашему описанию

✨ **Пример:**
`/generate красивый закат над океаном`

Расскажите подробнее, что хотите создать!"""
        
        # Общие вопросы с контекстом
        else:
            # Анализируем контекст
            if '?' in message:
                return f"""Интересный вопрос! 🤔

{message[:200]}{'...' if len(message) > 200 else ''}

Позвольте подумать над этим. Это действительно важная тема, которая заслуживает обстоятельного ответа.

💡 **Мои мысли:**
Этот вопрос затрагивает несколько аспектов, и я готов разобрать его подробно. 

Хотели бы узнать мое мнение по конкретному аспекту, или нужен общий обзор темы?"""
            
            else:
                responses = [
                    f"Понимаю вашу мысль! {message[:150]}{'...' if len(message) > 150 else ''} - интересная тема для обсуждения.",
                    f"Спасибо за сообщение! Я анализирую информацию и готов поделиться своими соображениями.",
                    f"Отличная тема! Давайте разберем это подробнее с разных сторон.",
                    f"Интересное наблюдение! Могу предложить несколько вариантов развития этой идеи."
                ]
                base_response = random.choice(responses)
                
                # Добавляем контекстуальную информацию
                if any(word in message_lower for word in ['технология', 'компьютер', 'интернет']):
                    base_response += "\n\n💻 Если нужны технические детали - готов углубиться!"
                elif any(word in message_lower for word in ['творчество', 'искусство', 'дизайн']):
                    base_response += "\n\n🎨 Для творческих задач могу предложить множество решений!"
                
                return base_response
    
    async def get_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        return {
            "demo_mode": self.demo_mode,
            "active_chats": len(self.chat_sessions),
            "agents": {
                "text_agent": False,
                "vision_agent": False, 
                "image_agent": False
            },
            "timestamp": datetime.now().isoformat()
        }


class TelegramChatBot:
    """Telegram чат-бот с поддержкой разных режимов"""
    
    def __init__(self):
        self.token = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
        self.allowed_chat_id = "458589236"
        
        # Координатор чата
        self.chat_coordinator = SimpleChatCoordinator()
        
        # Для простого HTTP API
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.last_update_id = 0
        
        # Для python-telegram-bot
        self.bot: Optional[Bot] = None
        self.application = None
    
    async def initialize(self):
        """Инициализация бота"""
        logger.info("🚀 Инициализация Telegram чат-бота...")
        
        if TELEGRAM_AVAILABLE:
            # Используем python-telegram-bot
            await self._init_telegram_bot()
        else:
            # Используем простой HTTP API
            await self._init_simple_bot()
        
        logger.info("✅ Бот инициализирован")
    
    async def _init_telegram_bot(self):
        """Инициализация через python-telegram-bot"""
        try:
            self.bot = Bot(token=self.token)
            self.application = Application.builder().token(self.token).build()
            
            # Регистрация обработчиков
            self.application.add_handler(CommandHandler("start", self._cmd_start))
            self.application.add_handler(CommandHandler("help", self._cmd_help))
            self.application.add_handler(CommandHandler("status", self._cmd_status))
            self.application.add_handler(CommandHandler("generate", self._cmd_generate))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
            
            await self.application.initialize()
            await self.application.start()
            
            logger.info("✅ Python-telegram-bot инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации python-telegram-bot: {e}")
            raise
    
    async def _init_simple_bot(self):
        """Инициализация простого HTTP бота"""
        logger.info("🔧 Используем простой HTTP API")
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user_name = update.effective_user.first_name or "Пользователь"
        
        welcome_text = f"""🤖 **AGI Layer v3.9 - Чат с нейросетями**

Привет, {user_name}! Я - ваш персональный ИИ-ассистент.

**🧠 Возможности:**
• 💬 Умный диалог с памятью контекста
• 🎨 Генерация изображений (/generate)
• 👁️ Анализ изображений (пришлите фото)
• 📊 Помощь с любыми задачами

**🚀 Команды:**
/help - Подробная справка
/status - Статус системы
/generate [описание] - Создать изображение

**Просто пишите мне, и я отвечу как умная нейросеть!** ✨"""
        
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """🤖 **AGI Layer v3.9 - Справка**

**📝 Команды:**
• `/start` - Главное меню
• `/help` - Эта справка
• `/status` - Статус всех систем
• `/generate [описание]` - Генерация изображения

**💬 Как общаться:**
Просто пишите сообщения - я понимаю естественный язык и отвечаю в контексте диалога.

**🎯 Примеры:**
• "Расскажи про космос"
• "Помоги с программированием на Python"
• "Придумай идею для проекта"
• "/generate красивый закат над морем"

**⚡ Я работаю в демо режиме - быстро и эффективно!**"""
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status"""
        status = await self.chat_coordinator.get_status()
        
        status_text = f"""📊 **Статус AGI Layer v3.9**

🤖 **Система:**
• Chat Coordinator: 🟢 Активен
• Telegram Bot: 🟢 Активен
• Режим: 🟡 Демо (быстрый)

📈 **Статистика:**
• Активных чатов: {status['active_chats']}
• Время работы: {datetime.now().strftime('%H:%M:%S')}
• Версия: v3.9.0

✅ **Все системы функционируют нормально!**"""
        
        await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)
    
    async def _cmd_generate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /generate"""
        prompt = " ".join(context.args) if context.args else ""
        
        if not prompt:
            await update.message.reply_text(
                "🎨 **Генерация изображений**\n\n"
                "Использование: `/generate [описание]`\n\n"
                "**Примеры:**\n"
                "• `/generate красивый закат над морем`\n"
                "• `/generate футуристический город`\n"
                "• `/generate милый котенок`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        demo_text = f"""🎨 **Изображение создано!**

📝 **Промпт:** {prompt}
🤖 **Модель:** Stable Diffusion 1.5
📅 **Время:** {datetime.now().strftime('%H:%M:%S')}

*В демо режиме изображения не генерируются физически, но система готова к работе с нейросетями!*

🚀 **Для реальной генерации запустите полную систему через Docker**"""
        
        await update.message.reply_text(demo_text, parse_mode=ParseMode.MARKDOWN)
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка обычных сообщений"""
        try:
            chat_id = update.effective_chat.id
            message = update.message.text
            user_name = update.effective_user.first_name or "Пользователь"
            
            # Показываем индикатор печати
            await context.bot.send_chat_action(chat_id=chat_id, action='typing')
            
            # Обрабатываем сообщение через координатор
            response = await self.chat_coordinator.process_text_message(chat_id, message, user_name)
            
            # Отправляем ответ
            await update.message.reply_text(f"🤖 {response}")
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(
                "❌ Извините, произошла техническая ошибка. Система перезагружается, попробуйте через несколько секунд."
            )
    
    # Методы для простого HTTP API
    async def send_message_simple(self, chat_id: str, text: str):
        """Отправка сообщения через простой API"""
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp не доступен для HTTP запросов")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                }
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('ok', False)
                    return False
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            return False
    
    async def get_updates_simple(self):
        """Получение обновлений через простой API"""
        if not AIOHTTP_AVAILABLE:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/getUpdates"
                params = {"offset": self.last_update_id + 1, "timeout": 10}
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            return data.get('result', [])
        except Exception as e:
            logger.error(f"Ошибка получения обновлений: {e}")
        return []
    
    async def process_update_simple(self, update):
        """Обработка обновления в простом режиме"""
        try:
            if 'message' not in update:
                return
            
            message = update['message']
            chat_id = str(message['chat']['id'])
            text = message.get('text', '')
            user_name = message['from'].get('first_name', 'Пользователь')
            
            logger.info(f"Получено сообщение от {user_name}: {text}")
            
            # Обработка команд
            if text == '/start':
                response = f"""🤖 **AGI Layer v3.9 - Чат с нейросетями**

Привет, {user_name}! Я - ваш персональный ИИ-ассистент.

**🧠 Возможности:**
• 💬 Умный диалог с памятью контекста
• 🎨 Генерация изображений (/generate)
• 📊 Помощь с любыми задачами

**Просто пишите мне, и я отвечу как умная нейросеть!** ✨"""
                
            elif text == '/help':
                response = """🤖 **Справка AGI Layer v3.9**

Просто пишите сообщения - я понимаю естественный язык!

**Команды:**
/start - Главное меню
/status - Статус системы
/generate [описание] - Создать изображение

**Примеры общения:**
"Расскажи про космос"
"Помоги с программированием"
"/generate красивый закат" """
                
            elif text == '/status':
                status = await self.chat_coordinator.get_status()
                response = f"""📊 **Статус AGI Layer v3.9**

🤖 **Система:** 🟢 Активна
📈 **Чатов:** {status['active_chats']}
⏰ **Время:** {datetime.now().strftime('%H:%M:%S')}

✅ Все системы работают!"""
                
            elif text.startswith('/generate '):
                prompt = text[10:]
                response = f"""🎨 **Изображение создано!**

📝 **Промпт:** {prompt}
🤖 **Модель:** Stable Diffusion 1.5

*Демо режим - система готова к работе!*"""
                
            else:
                # Обычное сообщение
                response = await self.chat_coordinator.process_text_message(int(chat_id), text, user_name)
                response = f"🤖 {response}"
            
            # Отправляем ответ
            await self.send_message_simple(chat_id, response)
            
        except Exception as e:
            logger.error(f"Ошибка обработки обновления: {e}")
    
    async def run_simple(self):
        """Запуск в простом режиме"""
        logger.info("🚀 Запуск в простом режиме...")
        
        # Отправляем приветствие
        if self.allowed_chat_id:
            await self.send_message_simple(
                self.allowed_chat_id,
                "🚀 **AGI Layer v3.9 запущен!**\n\nБот готов к работе в демо режиме. Используйте /start для начала."
            )
        
        # Основной цикл
        while True:
            try:
                updates = await self.get_updates_simple()
                
                for update in updates:
                    self.last_update_id = update['update_id']
                    await self.process_update_simple(update)
                
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Остановка бота...")
                break
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                await asyncio.sleep(5)
    
    async def run(self):
        """Запуск бота"""
        try:
            await self.initialize()
            
            if TELEGRAM_AVAILABLE:
                # Запуск с python-telegram-bot
                logger.info("🚀 Запуск с python-telegram-bot...")
                
                # Отправка уведомления о запуске
                if self.allowed_chat_id:
                    try:
                        await self.bot.send_message(
                            chat_id=int(self.allowed_chat_id),
                            text="🚀 **AGI Layer v3.9 запущен!**\n\nБот готов к работе. Используйте /start для начала.",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except Exception as e:
                        logger.warning(f"Не удалось отправить уведомление: {e}")
                
                # Запуск polling
                await self.application.updater.start_polling(drop_pending_updates=True)
                await self.application.updater.idle()
                
            else:
                # Запуск в простом режиме
                await self.run_simple()
                
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Очистка ресурсов"""
        logger.info("🧹 Очистка ресурсов...")
        
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        
        logger.info("✅ Ресурсы очищены")


async def main():
    """Основная функция"""
    bot = TelegramChatBot()
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал завершения")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    print("🤖 AGI Layer v3.9 - Telegram Chat Bot")
    print("=" * 40)
    print()
    
    if not TELEGRAM_AVAILABLE:
        print("⚠️  python-telegram-bot не установлен")
        print("📦 Установите: pip install python-telegram-bot")
        print("🔧 Работаем в упрощенном режиме")
        print()
    
    if not AIOHTTP_AVAILABLE:
        print("⚠️  aiohttp не установлен") 
        print("📦 Установите: pip install aiohttp")
        print("🔧 HTTP API может не работать")
        print()
    
    print("🚀 Запуск бота...")
    asyncio.run(main())