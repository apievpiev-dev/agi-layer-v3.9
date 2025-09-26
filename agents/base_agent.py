"""
BaseAgent - Базовый класс для всех агентов AGI Layer v3.9
=========================================================

Содержит общую логику для всех агентов:
- Подключение к БД и Redis
- Система логирования  
- Мониторинг здоровья
- Обработка ошибок
- Межагентное взаимодействие
"""

import asyncio
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import redis
import sqlalchemy as sa
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class AgentConfig(BaseModel):
    """Конфигурация агента"""
    name: str
    type: str
    model_name: Optional[str] = None
    max_memory: str = "8G"
    max_cpu_cores: int = 2
    heartbeat_interval: int = 30
    max_retries: int = 3
    restart_delay: int = 10


class AgentMessage(BaseModel):
    """Сообщение между агентами"""
    sender: str
    receiver: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime
    message_id: str


class BaseAgent(ABC):
    """Базовый класс для всех агентов"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.type = config.type
        self.status = "initializing"
        self.last_heartbeat = datetime.now()
        
        # Настройка логирования
        self._setup_logging()
        
        # Подключения к внешним сервисам
        self.redis_client = None
        self.db_engine = None
        self.db_session = None
        
        # Состояние агента
        self.is_running = False
        self.error_count = 0
        self.last_error = None
        
        logger.info(f"Инициализация агента {self.name} типа {self.type}")

    def _setup_logging(self):
        """Настройка системы логирования"""
        log_file = f"/app/logs/{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        
        logger.add(
            log_file,
            rotation="100 MB",
            retention="30 days",
            level=os.getenv("LOG_LEVEL", "INFO"),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            backtrace=True,
            diagnose=True
        )

    async def initialize(self):
        """Инициализация агента"""
        try:
            logger.info(f"Запуск инициализации агента {self.name}")
            
            # Подключение к Redis
            await self._connect_redis()
            
            # Подключение к PostgreSQL
            await self._connect_database()
            
            # Загрузка модели (если требуется)
            await self._load_model()
            
            # Специфичная инициализация агента
            await self._agent_specific_init()
            
            self.status = "ready"
            logger.info(f"Агент {self.name} успешно инициализирован")
            
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)
            self.error_count += 1
            logger.error(f"Ошибка инициализации агента {self.name}: {e}")
            raise

    async def _connect_redis(self):
        """Подключение к Redis"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            await asyncio.to_thread(self.redis_client.ping)
            logger.info(f"Агент {self.name} подключен к Redis")
        except Exception as e:
            logger.error(f"Ошибка подключения к Redis: {e}")
            raise

    async def _connect_database(self):
        """Подключение к PostgreSQL"""
        db_url = os.getenv("POSTGRES_URL", "postgresql://agi_user:password@localhost:5432/agi_memory")
        try:
            self.db_engine = create_engine(db_url)
            Session = sessionmaker(bind=self.db_engine)
            self.db_session = Session()
            
            # Проверка соединения
            with self.db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Агент {self.name} подключен к PostgreSQL")
        except Exception as e:
            logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            raise

    @abstractmethod
    async def _load_model(self):
        """Загрузка модели агента (реализуется в наследниках)"""
        pass

    @abstractmethod
    async def _agent_specific_init(self):
        """Специфичная инициализация агента (реализуется в наследниках)"""
        pass

    @abstractmethod
    async def process_message(self, message: AgentMessage) -> Dict[str, Any]:
        """Обработка сообщения (реализуется в наследниках)"""
        pass

    async def send_message(self, receiver: str, message_type: str, content: Dict[str, Any]):
        """Отправка сообщения другому агенту"""
        message = AgentMessage(
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            content=content,
            timestamp=datetime.now(),
            message_id=f"{self.name}_{int(time.time() * 1000)}"
        )
        
        try:
            # Отправляем через Redis
            channel = f"agent_{receiver}"
            await asyncio.to_thread(
                self.redis_client.publish,
                channel,
                message.model_dump_json()
            )
            logger.debug(f"Сообщение отправлено от {self.name} к {receiver}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            raise

    async def listen_messages(self):
        """Прослушивание входящих сообщений"""
        try:
            pubsub = self.redis_client.pubsub()
            channel = f"agent_{self.name}"
            pubsub.subscribe(channel)
            
            logger.info(f"Агент {self.name} начал прослушивание канала {channel}")
            
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        agent_message = AgentMessage(**data)
                        
                        logger.debug(f"Получено сообщение: {agent_message.message_type} от {agent_message.sender}")
                        
                        # Обрабатываем сообщение
                        response = await self.process_message(agent_message)
                        
                        # Отправляем ответ если нужно
                        if response and agent_message.sender != "system":
                            await self.send_message(
                                agent_message.sender,
                                "response",
                                response
                            )
                            
                    except Exception as e:
                        logger.error(f"Ошибка обработки сообщения: {e}")
                        self.error_count += 1
                        
        except Exception as e:
            logger.error(f"Ошибка в прослушивании сообщений: {e}")
            self.status = "error"
            raise

    async def heartbeat(self):
        """Отправка сигнала о состоянии агента"""
        while self.is_running:
            try:
                heartbeat_data = {
                    "agent_name": self.name,
                    "agent_type": self.type,
                    "status": self.status,
                    "timestamp": datetime.now().isoformat(),
                    "error_count": self.error_count,
                    "last_error": self.last_error,
                    "memory_usage": await self._get_memory_usage(),
                    "cpu_usage": await self._get_cpu_usage()
                }
                
                # Сохраняем в Redis
                await asyncio.to_thread(
                    self.redis_client.setex,
                    f"heartbeat_{self.name}",
                    60,  # TTL 60 секунд
                    json.dumps(heartbeat_data)
                )
                
                self.last_heartbeat = datetime.now()
                
                await asyncio.sleep(self.config.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Ошибка в heartbeat: {e}")
                await asyncio.sleep(5)

    async def _get_memory_usage(self) -> float:
        """Получение использования памяти"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except:
            return 0.0

    async def _get_cpu_usage(self) -> float:
        """Получение использования CPU"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except:
            return 0.0

    async def save_memory(self, key: str, value: Any, memory_type: str = "short_term"):
        """Сохранение в память"""
        try:
            memory_data = {
                "agent_name": self.name,
                "key": key,
                "value": json.dumps(value) if not isinstance(value, str) else value,
                "memory_type": memory_type,
                "timestamp": datetime.now().isoformat()
            }
            
            if memory_type == "short_term":
                # Сохраняем в Redis
                await asyncio.to_thread(
                    self.redis_client.setex,
                    f"memory_{self.name}_{key}",
                    3600,  # TTL 1 час
                    json.dumps(memory_data)
                )
            else:
                # Сохраняем в PostgreSQL
                # TODO: Реализовать сохранение в БД
                pass
                
        except Exception as e:
            logger.error(f"Ошибка сохранения в память: {e}")

    async def get_memory(self, key: str, memory_type: str = "short_term") -> Optional[Any]:
        """Получение из памяти"""
        try:
            if memory_type == "short_term":
                # Получаем из Redis
                data = await asyncio.to_thread(
                    self.redis_client.get,
                    f"memory_{self.name}_{key}"
                )
                if data:
                    memory_data = json.loads(data)
                    return json.loads(memory_data["value"]) if memory_data["value"].startswith('{') else memory_data["value"]
            else:
                # Получаем из PostgreSQL
                # TODO: Реализовать получение из БД
                pass
                
        except Exception as e:
            logger.error(f"Ошибка получения из памяти: {e}")
        
        return None

    async def run(self):
        """Основной цикл работы агента"""
        try:
            # Инициализация
            await self.initialize()
            
            self.is_running = True
            self.status = "running"
            
            logger.info(f"Агент {self.name} запущен")
            
            # Запускаем фоновые задачи
            tasks = [
                asyncio.create_task(self.listen_messages()),
                asyncio.create_task(self.heartbeat()),
                asyncio.create_task(self._agent_main_loop())
            ]
            
            # Ждем завершения любой задачи
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            
            # Отменяем оставшиеся задачи
            for task in pending:
                task.cancel()
                
        except Exception as e:
            logger.error(f"Критическая ошибка в агенте {self.name}: {e}")
            self.status = "error"
            self.last_error = str(e)
        finally:
            self.is_running = False
            await self._cleanup()

    @abstractmethod
    async def _agent_main_loop(self):
        """Основной цикл агента (реализуется в наследниках)"""
        pass

    async def _cleanup(self):
        """Очистка ресурсов"""
        try:
            if self.redis_client:
                self.redis_client.close()
            if self.db_session:
                self.db_session.close()
            logger.info(f"Агент {self.name} корректно завершен")
        except Exception as e:
            logger.error(f"Ошибка при завершении агента: {e}")

    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}', type='{self.type}', status='{self.status}')>"








