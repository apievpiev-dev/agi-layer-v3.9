#!/usr/bin/env python3
"""
AGI Layer v3.9 - Простой запуск без Docker
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agi_layer_simple.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_folders():
    """Создание необходимых папок"""
    folders = ['logs', 'models', 'output', 'output/images']
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Папка создана: {folder}")

def check_env():
    """Проверка .env файла"""
    if not Path('.env').exists():
        logger.warning("❌ Файл .env не найден")
        return False
    logger.info("✅ Файл .env найден")
    return True

def show_system_info():
    """Показать информацию о системе"""
    logger.info("🚀 AGI Layer v3.9 - Простой запуск")
    logger.info(f"📍 Папка проекта: {Path.cwd()}")
    logger.info(f"🐍 Python версия: {sys.version}")
    logger.info(f"💻 Платформа: {sys.platform}")

async def start_simple_agent():
    """Запуск простого агента для демонстрации"""
    logger.info("🤖 Запуск простого AGI агента...")
    
    # Симуляция работы агента
    for i in range(5):
        await asyncio.sleep(1)
        logger.info(f"🔄 Агент работает... Цикл {i+1}/5")
    
    logger.info("✅ Простой агент завершил работу")

async def main():
    """Главная функция"""
    try:
        show_system_info()
        create_folders()
        
        if not check_env():
            logger.warning("⚠️ Создайте .env файл для полной функциональности")
        
        # Запуск простого агента
        await start_simple_agent()
        
        logger.info("🎉 AGI Layer v3.9 готов к работе!")
        logger.info("📖 Для полного запуска используйте Docker или установите все зависимости")
        
    except KeyboardInterrupt:
        logger.info("🛑 Система остановлена пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
