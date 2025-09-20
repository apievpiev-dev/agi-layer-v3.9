#!/usr/bin/env python3
"""
AGI Layer v3.9 - Главный файл запуска
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Добавление корневой директории в путь
sys.path.append(str(Path(__file__).parent))

from config.settings import settings
from agents.meta_agent import MetaAgent
from agents.telegram_agent import TelegramAgent
from agents.image_agent import ImageAgent
from agents.text_agent import TextAgent
from agents.vision_agent import VisionAgent
from agents.ocr_agent import OCRAgent
from agents.embedding_agent import EmbeddingAgent
from agents.recovery_agent import RecoveryAgent


# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(settings.LOG_PATH, 'agi_layer.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def get_agent_config() -> dict:
    """Получение конфигурации агентов"""
    return {
        'postgres': {
            'host': settings.POSTGRES_HOST,
            'port': settings.POSTGRES_PORT,
            'database': settings.POSTGRES_DB,
            'user': settings.POSTGRES_USER,
            'password': settings.POSTGRES_PASSWORD
        },
        'chroma': {
            'host': settings.CHROMA_HOST,
            'port': settings.CHROMA_PORT,
            'collection': settings.CHROMA_COLLECTION
        },
        'redis': {
            'host': settings.REDIS_HOST,
            'port': settings.REDIS_PORT,
            'password': settings.REDIS_PASSWORD
        },
        'telegram_token': settings.TELEGRAM_TOKEN,
        'telegram_chat_id': settings.TELEGRAM_CHAT_ID,
        'models_path': settings.MODELS_PATH,
        'logs_path': settings.LOG_PATH,
        'agents': {
            'meta_agent': {'loop_interval': settings.AGENT_LOOP_INTERVAL},
            'telegram_agent': {'telegram_token': settings.TELEGRAM_TOKEN},
            'image_agent': {'models_path': settings.MODELS_PATH},
            'text_agent': {'models_path': settings.MODELS_PATH},
            'vision_agent': {'models_path': settings.MODELS_PATH},
            'ocr_agent': {'models_path': settings.MODELS_PATH},
            'embedding_agent': {'models_path': settings.MODELS_PATH},
            'recovery_agent': {'logs_path': settings.LOG_PATH}
        }
    }


async def start_agent(agent_name: str, config: dict):
    """Запуск конкретного агента"""
    try:
        logger.info(f"Запуск агента {agent_name}")
        
        agent_config = config.copy()
        agent_config.update(config['agents'].get(agent_name, {}))
        
        if agent_name == 'meta_agent':
            agent = MetaAgent(agent_config)
        elif agent_name == 'telegram_agent':
            agent = TelegramAgent(agent_config)
        elif agent_name == 'image_agent':
            agent = ImageAgent(agent_config)
        elif agent_name == 'text_agent':
            agent = TextAgent(agent_config)
        elif agent_name == 'vision_agent':
            agent = VisionAgent(agent_config)
        elif agent_name == 'ocr_agent':
            agent = OCRAgent(agent_config)
        elif agent_name == 'embedding_agent':
            agent = EmbeddingAgent(agent_config)
        elif agent_name == 'recovery_agent':
            agent = RecoveryAgent(agent_config)
        else:
            logger.error(f"Неизвестный агент: {agent_name}")
            return None
        
        await agent.start()
        return agent
        
    except Exception as e:
        logger.error(f"Ошибка запуска агента {agent_name}: {e}")
        return None


async def main():
    """Основная функция"""
    logger.info("🚀 Запуск AGI Layer v3.9")
    
    # Получение конфигурации
    config = get_agent_config()
    
    # Определение агента для запуска из переменной окружения
    agent_name = os.getenv('AGENT_NAME', 'meta_agent')
    
    if agent_name == 'all':
        # Запуск всех агентов (для разработки)
        agents = [
            'meta_agent',
            'telegram_agent',
            'image_agent',
            'text_agent',
            'vision_agent',
            'ocr_agent',
            'embedding_agent',
            'recovery_agent'
        ]
        
        running_agents = []
        for agent in agents:
            agent_instance = await start_agent(agent, config)
            if agent_instance:
                running_agents.append(agent_instance)
        
        logger.info(f"Запущено {len(running_agents)} агентов")
        
        # Ожидание завершения
        try:
            await asyncio.gather(*[agent.stop() for agent in running_agents])
        except KeyboardInterrupt:
            logger.info("Получен сигнал завершения")
            for agent in running_agents:
                await agent.stop()
    
    else:
        # Запуск одного агента
        agent = await start_agent(agent_name, config)
        
        if agent:
            logger.info(f"Агент {agent_name} запущен")
            
            try:
                # Ожидание завершения
                while agent.running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Получен сигнал завершения")
                await agent.stop()
        else:
            logger.error(f"Не удалось запустить агент {agent_name}")
            sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Система остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

