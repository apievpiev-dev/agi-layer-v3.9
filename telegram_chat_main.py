#!/usr/bin/env python3
"""
Запуск TelegramChatAgent для AGI Layer v3.9
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавление корневой директории в путь
sys.path.append(str(Path(__file__).parent))

from agents.telegram_chat_agent import TelegramChatAgent
from config.settings import settings
from config.chat_config import validate_chat_config

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"{settings.LOG_PATH}/telegram_chat_agent.log")
    ]
)

logger = logging.getLogger(__name__)


def check_environment():
    """Проверка переменных окружения"""
    required_vars = {
        'TELEGRAM_TOKEN': settings.TELEGRAM_TOKEN,
        'POSTGRES_HOST': settings.POSTGRES_HOST,
        'POSTGRES_DB': settings.POSTGRES_DB,
        'POSTGRES_USER': settings.POSTGRES_USER,
        'POSTGRES_PASSWORD': settings.POSTGRES_PASSWORD
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if not var_value:
            missing_vars.append(var_name)
    
    if missing_vars:
        logger.error(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
        return False
    
    return True


def validate_configuration():
    """Проверка конфигурации чата"""
    logger.info("Проверка конфигурации чата...")
    
    config_checks = validate_chat_config()
    
    failed_checks = [
        check_name for check_name, passed in config_checks.items() 
        if not passed
    ]
    
    if failed_checks:
        logger.error(f"Ошибки конфигурации: {', '.join(failed_checks)}")
        return False
    
    logger.info("✅ Конфигурация чата валидна")
    return True


async def main():
    """Основная функция запуска"""
    logger.info("🤖 Запуск TelegramChatAgent для AGI Layer v3.9")
    
    # Проверка окружения
    if not check_environment():
        logger.error("❌ Проверка окружения не пройдена")
        sys.exit(1)
    
    # Проверка конфигурации
    if not validate_configuration():
        logger.error("❌ Проверка конфигурации не пройдена")
        sys.exit(1)
    
    # Создание директорий
    os.makedirs(settings.LOG_PATH, exist_ok=True)
    os.makedirs(settings.MODELS_PATH, exist_ok=True)
    
    # Конфигурация агента
    agent_config = {
        'telegram_token': settings.TELEGRAM_TOKEN,
        'postgres_host': settings.POSTGRES_HOST,
        'postgres_port': settings.POSTGRES_PORT,
        'postgres_db': settings.POSTGRES_DB,
        'postgres_user': settings.POSTGRES_USER,
        'postgres_password': settings.POSTGRES_PASSWORD,
        'max_context_messages': settings.MAX_CONTEXT_MESSAGES,
        'response_timeout': settings.CHAT_RESPONSE_TIMEOUT,
        'enable_image_processing': settings.ENABLE_IMAGE_PROCESSING,
        'enable_voice_messages': settings.ENABLE_VOICE_MESSAGES,
        'default_personality': settings.DEFAULT_PERSONALITY
    }
    
    # Создание и запуск агента
    try:
        agent = TelegramChatAgent(agent_config)
        
        logger.info("🚀 Инициализация TelegramChatAgent...")
        await agent.initialize()
        
        logger.info("✅ TelegramChatAgent успешно запущен!")
        logger.info("📱 Бот готов к приему сообщений в Telegram")
        
        # Запуск агента
        await agent.run()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
    finally:
        if 'agent' in locals():
            logger.info("🛑 Остановка TelegramChatAgent...")
            await agent.cleanup()
        
        logger.info("👋 TelegramChatAgent остановлен")


if __name__ == "__main__":
    try:
        # Запуск в event loop
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}")
        sys.exit(1)