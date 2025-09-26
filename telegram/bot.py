"""
AGI Layer v3.9 - Telegram Bot
=============================

Telegram бот для управления AGI системой:
- /start - приветствие и инструкции
- /status - статус всех агентов
- /generate <текст> - генерация текста
- /image <описание> - создание изображения
- /logs [агент] - просмотр логов
- /reboot - перезапуск системы
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Optional

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler, 
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class AGITelegramBot:
    """Telegram бот для AGI Layer v3.9"""
    
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.allowed_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = "http://api-server:8080"
        
        if not self.token:
            raise ValueError("TELEGRAM_TOKEN не установлен в .env")
        
        if not self.allowed_chat_id:
            raise ValueError("TELEGRAM_CHAT_ID не установлен в .env")
        
        self.allowed_chat_id = int(self.allowed_chat_id)
    
    def check_authorization(self, update: Update) -> bool:
        """Проверка авторизации пользователя"""
        chat_id = update.effective_chat.id
        if chat_id != self.allowed_chat_id:
            logger.warning(f"Неавторизованный доступ от chat_id: {chat_id}")
            return False
        return True
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        if not self.check_authorization(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        welcome_text = """
🤖 **AGI Layer v3.9 - Добро пожаловать!**

🔧 **Доступные команды:**
• `/status` - статус всех агентов
• `/generate <текст>` - генерация текста с помощью LLM
• `/image <описание>` - создание изображения
• `/logs [агент]` - просмотр логов
• `/reboot` - перезапуск системы
• `/help` - справка

📊 **Web интерфейс:** http://ваш-сервер:8501

💡 **Примеры использования:**
• `Напиши стихотворение о природе`
• `/image красивый закат над океаном`
• `/logs llm_agent`

🚀 Система готова к работе!
        """
        
        # Клавиатура быстрых действий
        keyboard = [
            [InlineKeyboardButton("📊 Статус", callback_data="status")],
            [InlineKeyboardButton("🤖 Агенты", callback_data="agents")],
            [InlineKeyboardButton("📝 Логи", callback_data="logs")],
            [InlineKeyboardButton("🔄 Перезапуск", callback_data="reboot")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status"""
        if not self.check_authorization(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        try:
            # Получаем статус через API
            response = requests.get(f"{self.api_url}/status", timeout=10)
            
            if response.status_code == 200:
                status = response.json()
                
                # Формируем отчет
                report = "📊 **Статус AGI Layer v3.9**\n\n"
                
                # Meta Agent
                meta = status.get("meta_agent", {})
                uptime_seconds = meta.get("uptime", 0)
                uptime_minutes = int(uptime_seconds // 60)
                report += f"🎯 **Meta Agent:** {meta.get('status', 'unknown')}\n"
                report += f"⏱️ **Время работы:** {uptime_minutes} мин\n\n"
                
                # Статистика
                stats = status.get("statistics", {})
                report += f"📈 **Статистика:**\n"
                report += f"• Всего агентов: {stats.get('total_agents', 0)}\n"
                report += f"• Активных: {stats.get('active_agents', 0)}\n"
                report += f"• Ошибок: {stats.get('failed_agents', 0)}\n\n"
                
                # Агенты
                agents = status.get("agents", {})
                if agents:
                    report += "🤖 **Агенты:**\n"
                    for name, info in agents.items():
                        status_emoji = "✅" if info.get("status") == "running" else "❌"
                        report += f"{status_emoji} {name}: {info.get('status', 'unknown')}\n"
                
            else:
                report = "❌ Не удалось получить статус системы"
                
        except Exception as e:
            report = f"❌ Ошибка получения статуса: {str(e)}"
        
        await update.message.reply_text(report, parse_mode="Markdown")
    
    async def generate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /generate"""
        if not self.check_authorization(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        # Получаем текст после команды
        prompt = update.message.text.replace("/generate", "").strip()
        
        if not prompt:
            await update.message.reply_text(
                "📝 Использование: `/generate ваш текст`\n\n"
                "Пример: `/generate Напиши стихотворение о космосе`"
            )
            return
        
        try:
            # Отправляем сообщение о начале генерации
            status_message = await update.message.reply_text("🤖 Генерирую ответ...")
            
            # Делаем запрос к LLM агенту через API
            response = requests.post(
                f"{self.api_url}/generate",
                json={"prompt": prompt, "max_tokens": 1024},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("generated_text", "Ошибка генерации")
                
                # Обновляем сообщение с результатом
                await status_message.edit_text(f"🤖 **Ответ:**\n\n{generated_text}")
                
            else:
                await status_message.edit_text("❌ Ошибка генерации текста")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    async def logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /logs"""
        if not self.check_authorization(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        # Получаем имя агента
        args = context.args
        agent_name = args[0] if args else "meta_agent"
        
        try:
            response = requests.get(f"{self.api_url}/agents/{agent_name}/logs", timeout=10)
            
            if response.status_code == 200:
                logs = response.json().get("logs", [])
                
                # Берем последние 20 строк логов
                recent_logs = logs[-20:] if len(logs) > 20 else logs
                
                logs_text = f"📝 **Логи {agent_name}** (последние 20 строк):\n\n"
                logs_text += "```\n"
                logs_text += "\n".join(recent_logs)
                logs_text += "\n```"
                
                await update.message.reply_text(logs_text, parse_mode="Markdown")
                
            else:
                await update.message.reply_text(f"❌ Не удалось получить логи агента {agent_name}")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения логов: {str(e)}")
    
    async def reboot_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /reboot"""
        if not self.check_authorization(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        # Подтверждение перезапуска
        keyboard = [
            [InlineKeyboardButton("✅ Да, перезапустить", callback_data="reboot_confirm")],
            [InlineKeyboardButton("❌ Отмена", callback_data="reboot_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ **Подтверждение перезапуска**\n\n"
            "Это перезапустит все агенты и сервисы.\n"
            "Процесс займет 1-2 минуты.\n\n"
            "Продолжить?",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий кнопок"""
        query = update.callback_query
        await query.answer()
        
        if not self.check_authorization(update):
            await query.edit_message_text("❌ Доступ запрещен")
            return
        
        if query.data == "status":
            await self.status_command(update, context)
        
        elif query.data == "reboot_confirm":
            try:
                await query.edit_message_text("🔄 Перезапуск системы...")
                
                # Отправляем команду перезапуска
                response = requests.post(f"{self.api_url}/system/reboot", timeout=5)
                
                if response.status_code == 200:
                    await query.edit_message_text("✅ Система перезапускается. Проверьте статус через 2 минуты.")
                else:
                    await query.edit_message_text("❌ Ошибка перезапуска системы")
                    
            except Exception as e:
                await query.edit_message_text(f"❌ Ошибка: {str(e)}")
        
        elif query.data == "reboot_cancel":
            await query.edit_message_text("❌ Перезапуск отменен")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        if not self.check_authorization(update):
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        user_text = update.message.text
        
        # Если сообщение не команда, обрабатываем как запрос к LLM
        if not user_text.startswith("/"):
            try:
                # Отправляем запрос к LLM агенту
                response = requests.post(
                    f"{self.api_url}/generate",
                    json={"prompt": user_text, "max_tokens": 512},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    generated_text = result.get("generated_text", "Ошибка генерации")
                    await update.message.reply_text(f"🤖 {generated_text}")
                else:
                    await update.message.reply_text("❌ LLM агент недоступен")
                    
            except Exception as e:
                await update.message.reply_text(f"❌ Ошибка: {str(e)}")

    def run(self):
        """Запуск Telegram бота"""
        try:
            # Создаем приложение
            application = Application.builder().token(self.token).build()
            
            # Регистрируем обработчики команд
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("status", self.status_command))
            application.add_handler(CommandHandler("generate", self.generate_command))
            application.add_handler(CommandHandler("logs", self.logs_command))
            application.add_handler(CommandHandler("reboot", self.reboot_command))
            
            # Обработчик кнопок
            application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Обработчик текстовых сообщений
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
            
            logger.info("🚀 Telegram бот запускается...")
            logger.info(f"📱 Авторизованный chat_id: {self.allowed_chat_id}")
            
            # Запускаем бота
            application.run_polling(drop_pending_updates=True)
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска Telegram бота: {e}")
            raise


if __name__ == "__main__":
    bot = AGITelegramBot()
    bot.run()







