"""
TelegramAgent - интеграция с Telegram для управления AGI Layer v3.9
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
import asyncpg
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from .base_agent import BaseAgent, Task


class TelegramAgent(BaseAgent):
    """Агент для интеграции с Telegram"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("telegram_agent", config)
        self.bot_token = config.get('telegram_token')
        self.allowed_chat_id = config.get('telegram_chat_id')
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        
    async def _initialize_agent(self):
        """Инициализация Telegram бота"""
        if not self.bot_token:
            raise ValueError("Telegram token не настроен")
            
        self.bot = Bot(token=self.bot_token)
        self.application = Application.builder().token(self.bot_token).build()
        
        # Регистрация обработчиков команд
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("status", self._cmd_status))
        self.application.add_handler(CommandHandler("generate", self._cmd_generate))
        self.application.add_handler(CommandHandler("report", self._cmd_report))
        self.application.add_handler(CommandHandler("reboot", self._cmd_reboot))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Запуск бота
        await self.application.initialize()
        await self.application.start()
        
        # Запуск polling
        asyncio.create_task(self._run_polling())
        
        self.logger.info("Telegram бот инициализирован")
    
    async def _run_polling(self):
        """Запуск polling для получения сообщений"""
        try:
            await self.application.updater.start_polling()
        except Exception as e:
            self.logger.error(f"Ошибка polling: {e}")
    
    async def _check_authorization(self, update: Update) -> bool:
        """Проверка авторизации пользователя"""
        if not self.allowed_chat_id:
            return True  # Если не настроен, разрешаем всем
            
        chat_id = str(update.effective_chat.id)
        return chat_id == self.allowed_chat_id
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        if not await self._check_authorization(update):
            await update.message.reply_text("Доступ запрещен")
            return
            
        await self._log_telegram_message(update, "start")
        
        welcome_text = """
🤖 AGI Layer v3.9 - Система управления

Доступные команды:
/start - Показать это сообщение
/status - Статус системы и агентов
/generate [prompt] - Генерация изображения
/report - Отчет о работе системы
/reboot - Перезапуск системы

Система готова к работе!
        """
        
        await update.message.reply_text(welcome_text)
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /status"""
        if not await self._check_authorization(update):
            await update.message.reply_text("Доступ запрещен")
            return
            
        await self._log_telegram_message(update, "status")
        
        try:
            # Получение статуса системы от MetaAgent
            status_data = await self._get_system_status()
            
            status_text = "📊 Статус системы AGI Layer v3.9:\n\n"
            
            for agent_name, agent_data in status_data.get('agents', {}).items():
                status_emoji = {
                    'running': '🟢',
                    'stopped': '🔴', 
                    'error': '🔴',
                    'restarting': '🟡'
                }.get(agent_data['status'], '⚪')
                
                status_text += f"{status_emoji} {agent_name}: {agent_data['status']}\n"
                status_text += f"   Задач выполнено: {agent_data['tasks_completed']}\n"
                status_text += f"   Ошибок: {agent_data['errors_count']}\n"
                status_text += f"   CPU: {agent_data['cpu_usage']:.1f}%\n"
                status_text += f"   RAM: {agent_data['memory_usage']:.1f}MB\n\n"
            
            await update.message.reply_text(status_text)
            
        except Exception as e:
            await update.message.reply_text(f"Ошибка получения статуса: {e}")
            self.logger.error(f"Ошибка получения статуса: {e}")
    
    async def _cmd_generate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /generate"""
        if not await self._check_authorization(update):
            await update.message.reply_text("Доступ запрещен")
            return
            
        # Получение промпта из команды
        prompt = " ".join(context.args) if context.args else "beautiful landscape"
        
        await self._log_telegram_message(update, "generate", prompt)
        
        try:
            # Создание задачи генерации изображения
            task_id = await self._create_image_generation_task(prompt, update.effective_chat.id)
            
            await update.message.reply_text(
                f"🎨 Генерация изображения запущена!\n"
                f"Промпт: {prompt}\n"
                f"ID задачи: {task_id}\n"
                f"Ожидайте результат..."
            )
            
        except Exception as e:
            await update.message.reply_text(f"Ошибка создания задачи: {e}")
            self.logger.error(f"Ошибка создания задачи генерации: {e}")
    
    async def _cmd_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /report"""
        if not await self._check_authorization(update):
            await update.message.reply_text("Доступ запрещен")
            return
            
        await self._log_telegram_message(update, "report")
        
        try:
            # Получение отчета о работе системы
            report_data = await self._generate_system_report()
            
            report_text = f"""
📈 Отчет о работе системы AGI Layer v3.9

📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🤖 Агенты:
"""
            
            for agent_name, stats in report_data.get('agents_stats', {}).items():
                report_text += f"• {agent_name}: {stats['tasks_completed']} задач, {stats['errors_count']} ошибок\n"
            
            report_text += f"\n📊 Общая статистика:\n"
            report_text += f"• Всего задач: {report_data.get('total_tasks', 0)}\n"
            report_text += f"• Завершено: {report_data.get('completed_tasks', 0)}\n"
            report_text += f"• Ошибок: {report_data.get('total_errors', 0)}\n"
            report_text += f"• Время работы: {report_data.get('uptime', 'N/A')}\n"
            
            await update.message.reply_text(report_text)
            
        except Exception as e:
            await update.message.reply_text(f"Ошибка генерации отчета: {e}")
            self.logger.error(f"Ошибка генерации отчета: {e}")
    
    async def _cmd_reboot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /reboot"""
        if not await self._check_authorization(update):
            await update.message.reply_text("Доступ запрещен")
            return
            
        await self._log_telegram_message(update, "reboot")
        
        try:
            # Создание задачи перезапуска системы
            task_id = await self._create_reboot_task()
            
            await update.message.reply_text(
                f"🔄 Перезапуск системы инициирован!\n"
                f"ID задачи: {task_id}\n"
                f"Система будет перезапущена..."
            )
            
        except Exception as e:
            await update.message.reply_text(f"Ошибка инициирования перезапуска: {e}")
            self.logger.error(f"Ошибка инициирования перезапуска: {e}")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка обычных сообщений"""
        if not await self._check_authorization(update):
            await update.message.reply_text("Доступ запрещен")
            return
            
        message_text = update.message.text
        await self._log_telegram_message(update, "message", message_text)
        
        # Простая обработка сообщений - можно расширить
        response = await self._process_user_message(message_text)
        await update.message.reply_text(response)
    
    async def _process_user_message(self, message: str) -> str:
        """Обработка пользовательского сообщения"""
        # Простая логика - можно интегрировать с TextAgent
        if "статус" in message.lower():
            return "Используйте команду /status для получения статуса системы"
        elif "генерация" in message.lower() or "изображение" in message.lower():
            return "Используйте команду /generate [описание] для генерации изображения"
        else:
            return "Используйте команды для управления системой. /start для списка команд."
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы от MetaAgent"""
        try:
            url = "http://meta_agent:8000/status"
            async with self.http_session.get(url) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса системы: {e}")
        
        return {"agents": {}}
    
    async def _create_image_generation_task(self, prompt: str, chat_id: int) -> str:
        """Создание задачи генерации изображения"""
        try:
            url = "http://meta_agent:8000/create_task"
            data = {
                "task_type": "image_generation",
                "data": {
                    "prompt": prompt,
                    "chat_id": chat_id,
                    "user_request": True
                },
                "priority": 2
            }
            
            async with self.http_session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("task_id", "unknown")
        except Exception as e:
            self.logger.error(f"Ошибка создания задачи генерации: {e}")
            
        raise Exception("Не удалось создать задачу генерации")
    
    async def _create_reboot_task(self) -> str:
        """Создание задачи перезапуска системы"""
        try:
            url = "http://meta_agent:8000/create_task"
            data = {
                "task_type": "system_reboot",
                "data": {
                    "reason": "telegram_command",
                    "user_request": True
                },
                "priority": 3
            }
            
            async with self.http_session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("task_id", "unknown")
        except Exception as e:
            self.logger.error(f"Ошибка создания задачи перезапуска: {e}")
            
        raise Exception("Не удалось создать задачу перезапуска")
    
    async def _generate_system_report(self) -> Dict[str, Any]:
        """Генерация отчета о работе системы"""
        try:
            async with self.db_pool.acquire() as conn:
                # Статистика агентов
                agents_stats = {}
                rows = await conn.fetch("SELECT * FROM agents")
                for row in rows:
                    agents_stats[row['name']] = {
                        'tasks_completed': row['tasks_completed'],
                        'errors_count': row['errors_count'],
                        'status': row['status']
                    }
                
                # Общая статистика
                total_tasks = await conn.fetchval("SELECT COUNT(*) FROM tasks")
                completed_tasks = await conn.fetchval("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
                total_errors = await conn.fetchval("SELECT SUM(errors_count) FROM agents")
                
                return {
                    'agents_stats': agents_stats,
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'total_errors': total_errors,
                    'uptime': 'N/A'  # Можно добавить расчет времени работы
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка генерации отчета: {e}")
            return {}
    
    async def _log_telegram_message(self, update: Update, message_type: str, message_text: str = ""):
        """Логирование сообщения Telegram"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO telegram_messages 
                    (chat_id, user_id, message_text, message_type, processed_at)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    update.effective_chat.id,
                    update.effective_user.id,
                    message_text,
                    message_type,
                    datetime.now()
                )
        except Exception as e:
            self.logger.error(f"Ошибка логирования Telegram сообщения: {e}")
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задач TelegramAgent"""
        if task.task_type == "send_notification":
            chat_id = task.data.get("chat_id")
            message = task.data.get("message")
            
            if chat_id and message:
                try:
                    await self.bot.send_message(chat_id=chat_id, text=message)
                    return {"status": "sent", "chat_id": chat_id}
                except Exception as e:
                    return {"status": "error", "error": str(e)}
        
        return {"status": "unknown_task_type"}
    
    async def _cleanup_agent(self):
        """Очистка ресурсов TelegramAgent"""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        
        self.logger.info("Telegram бот остановлен")
    
    async def send_notification(self, chat_id: int, message: str):
        """Отправка уведомления пользователю"""
        try:
            await self.bot.send_message(chat_id=chat_id, text=message)
            self.logger.info(f"Уведомление отправлено в чат {chat_id}")
        except Exception as e:
            self.logger.error(f"Ошибка отправки уведомления: {e}")

