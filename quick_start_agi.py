#!/usr/bin/env python3
"""
Быстрый запуск AGI Layer v3.9 без Docker и PostgreSQL
Все агенты работают в одном процессе для простоты
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Добавляем путь к агентам
sys.path.append('/workspace')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/logs/agi_quick_start.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AGI_QuickStart")

class QuickAGISystem:
    """Упрощенная AGI система для быстрого запуска"""
    
    def __init__(self):
        self.agents = {}
        self.running = False
        
        # Конфигурация без PostgreSQL
        self.config = {
            'telegram_token': os.getenv('TELEGRAM_TOKEN', '8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw'),
            'telegram_chat_ids': [458589236],
            'models_path': '/workspace/models',
            'memory_path': '/workspace/memory',
            'data_path': '/workspace/data'
        }
        
        # Создаем необходимые директории
        for path in ['/workspace/logs', '/workspace/models', '/workspace/memory', '/workspace/data']:
            os.makedirs(path, exist_ok=True)
    
    async def initialize_simple_agents(self):
        """Инициализация упрощенных агентов"""
        try:
            logger.info("🚀 Инициализация упрощенных агентов...")
            
            # Простой Telegram агент
            self.agents['telegram'] = SimpleTelegramAgent(self.config)
            await self.agents['telegram'].initialize()
            
            # Простой агент генерации изображений
            self.agents['image_gen'] = SimpleImageGenAgent(self.config)
            await self.agents['image_gen'].initialize()
            
            # Простой агент анализа изображений
            self.agents['vision'] = SimpleVisionAgent(self.config)
            await self.agents['vision'].initialize()
            
            # Простая память
            self.agents['memory'] = SimpleMemoryAgent(self.config)
            await self.agents['memory'].initialize()
            
            logger.info("✅ Все агенты инициализированы")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации агентов: {e}")
            return False
    
    async def start_system(self):
        """Запуск системы"""
        logger.info("🚀 Запуск AGI Layer v3.9 (Quick Start)")
        
        if not await self.initialize_simple_agents():
            return False
        
        self.running = True
        
        # Запускаем все агенты
        tasks = []
        for name, agent in self.agents.items():
            tasks.append(asyncio.create_task(agent.run()))
            logger.info(f"✅ Агент {name} запущен")
        
        # Отправляем уведомление о запуске
        await self.agents['telegram'].send_startup_message()
        
        logger.info("🎯 AGI Layer v3.9 полностью запущен и готов к работе!")
        
        # Ждем завершения всех задач
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("⏹️ Получен сигнал остановки")
        finally:
            await self.stop_system()
    
    async def stop_system(self):
        """Остановка системы"""
        logger.info("🛑 Остановка AGI Layer v3.9")
        
        self.running = False
        
        for name, agent in self.agents.items():
            try:
                await agent.stop()
                logger.info(f"✅ Агент {name} остановлен")
            except Exception as e:
                logger.error(f"❌ Ошибка остановки агента {name}: {e}")


class SimpleTelegramAgent:
    """Упрощенный Telegram агент"""
    
    def __init__(self, config):
        self.config = config
        self.token = config['telegram_token']
        self.chat_ids = config['telegram_chat_ids']
        self.running = False
        
        # Импортируем интеллектуального бота
        from intelligent_telegram_bot import IntelligentAGI
        self.agi_bot = IntelligentAGI()
    
    async def initialize(self):
        """Инициализация"""
        logger.info("💬 Инициализация TelegramAgent")
        await self.agi_bot.initialize_ai_models()
        logger.info("✅ TelegramAgent готов")
    
    async def run(self):
        """Запуск агента"""
        self.running = True
        logger.info("💬 TelegramAgent запущен")
        
        try:
            await self.agi_bot.run()
        except Exception as e:
            logger.error(f"Ошибка TelegramAgent: {e}")
    
    async def stop(self):
        """Остановка"""
        self.running = False
        logger.info("💬 TelegramAgent остановлен")
    
    async def send_startup_message(self):
        """Отправка сообщения о запуске"""
        message = """🚀 **AGI Layer v3.9 запущен!**

Система полностью готова к работе:
✅ Интеллектуальный чат
✅ Генерация изображений  
✅ Анализ фотографий
✅ Векторная память
✅ Все агенты активны

Просто общайтесь со мной естественно! 🤖"""
        
        await self.agi_bot.send_message(message)


class SimpleImageGenAgent:
    """Упрощенный агент генерации изображений"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
    
    async def initialize(self):
        """Инициализация"""
        logger.info("🎨 Инициализация ImageGenAgent")
        # Модель уже загружена в intelligent_telegram_bot
        logger.info("✅ ImageGenAgent готов")
    
    async def run(self):
        """Запуск агента"""
        self.running = True
        logger.info("🎨 ImageGenAgent запущен")
        
        while self.running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """Остановка"""
        self.running = False
        logger.info("🎨 ImageGenAgent остановлен")


class SimpleVisionAgent:
    """Упрощенный агент анализа изображений"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
    
    async def initialize(self):
        """Инициализация"""
        logger.info("👁️ Инициализация VisionAgent")
        # Модель уже загружена в intelligent_telegram_bot
        logger.info("✅ VisionAgent готов")
    
    async def run(self):
        """Запуск агента"""
        self.running = True
        logger.info("👁️ VisionAgent запущен")
        
        while self.running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """Остановка"""
        self.running = False
        logger.info("👁️ VisionAgent остановлен")


class SimpleMemoryAgent:
    """Упрощенный агент памяти"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
        self.memory_file = '/workspace/memory/simple_memory.json'
        
        # Создаем файл памяти если его нет
        os.makedirs('/workspace/memory', exist_ok=True)
        if not os.path.exists(self.memory_file):
            import json
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    async def initialize(self):
        """Инициализация"""
        logger.info("🧠 Инициализация MemoryAgent")
        logger.info("✅ MemoryAgent готов")
    
    async def run(self):
        """Запуск агента"""
        self.running = True
        logger.info("🧠 MemoryAgent запущен")
        
        while self.running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """Остановка"""
        self.running = False
        logger.info("🧠 MemoryAgent остановлен")


async def main():
    """Основная функция"""
    system = QuickAGISystem()
    
    try:
        await system.start_system()
    except KeyboardInterrupt:
        logger.info("⏹️ Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await system.stop_system()


if __name__ == "__main__":
    print("🚀 Запуск AGI Layer v3.9 Quick Start")
    print("📱 Telegram бот будет доступен через несколько секунд")
    print("⏹️ Нажмите Ctrl+C для остановки")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Система остановлена")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")