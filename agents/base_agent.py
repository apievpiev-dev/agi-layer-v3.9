"""
BaseAgent - базовый класс для всех агентов AGI Layer v3.9
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
import aiohttp
import asyncpg
from pydantic import BaseModel


@dataclass
class AgentStatus:
    """Статус агента"""
    name: str
    status: str  # running, stopped, error, restarting
    last_activity: datetime
    memory_usage: float
    cpu_usage: float
    tasks_completed: int
    errors_count: int


class Task(BaseModel):
    """Задача для агента"""
    id: str
    agent_name: str
    task_type: str
    data: Dict[str, Any]
    priority: int = 1
    created_at: datetime = datetime.now()
    status: str = "pending"  # pending, processing, completed, failed


class BaseAgent(ABC):
    """Базовый класс для всех агентов"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.status = AgentStatus(
            name=name,
            status="stopped",
            last_activity=datetime.now(),
            memory_usage=0.0,
            cpu_usage=0.0,
            tasks_completed=0,
            errors_count=0
        )
        self.logger = logging.getLogger(f"agent.{name}")
        self.db_pool: Optional[asyncpg.Pool] = None
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.running = False
        
    async def initialize(self):
        """Инициализация агента"""
        try:
            self.logger.info(f"Инициализация агента {self.name}")
            
            # Подключение к PostgreSQL
            self.db_pool = await asyncpg.create_pool(
                host=self.config['postgres']['host'],
                port=self.config['postgres']['port'],
                database=self.config['postgres']['database'],
                user=self.config['postgres']['user'],
                password=self.config['postgres']['password']
            )
            
            # HTTP сессия для взаимодействия с другими агентами
            self.http_session = aiohttp.ClientSession()
            
            # Инициализация конкретного агента
            await self._initialize_agent()
            
            self.status.status = "running"
            self.logger.info(f"Агент {self.name} успешно инициализирован")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации агента {self.name}: {e}")
            self.status.status = "error"
            self.status.errors_count += 1
            raise
    
    @abstractmethod
    async def _initialize_agent(self):
        """Инициализация конкретного агента - должен быть переопределен"""
        pass
    
    async def start(self):
        """Запуск агента"""
        try:
            if not self.running:
                await self.initialize()
                self.running = True
                self.status.status = "running"
                
                # Запуск основного цикла агента
                asyncio.create_task(self._main_loop())
                
                self.logger.info(f"Агент {self.name} запущен")
        except Exception as e:
            self.logger.error(f"Ошибка запуска агента {self.name}: {e}")
            self.status.status = "error"
            self.status.errors_count += 1
    
    async def stop(self):
        """Остановка агента"""
        try:
            self.running = False
            self.status.status = "stopped"
            
            # Закрытие соединений
            if self.http_session:
                await self.http_session.close()
            if self.db_pool:
                await self.db_pool.close()
            
            await self._cleanup_agent()
            
            self.logger.info(f"Агент {self.name} остановлен")
        except Exception as e:
            self.logger.error(f"Ошибка остановки агента {self.name}: {e}")
    
    @abstractmethod
    async def _cleanup_agent(self):
        """Очистка ресурсов конкретного агента"""
        pass
    
    async def _main_loop(self):
        """Основной цикл агента"""
        while self.running:
            try:
                # Получение задач из очереди
                task = await self._get_next_task()
                
                if task:
                    await self._process_task(task)
                else:
                    # Если нет задач, выполнить фоновые операции
                    await self._background_work()
                
                # Обновление статуса
                self.status.last_activity = datetime.now()
                
                # Пауза между циклами
                await asyncio.sleep(self.config.get('loop_interval', 1.0))
                
            except Exception as e:
                self.logger.error(f"Ошибка в основном цикле агента {self.name}: {e}")
                self.status.errors_count += 1
                await asyncio.sleep(5.0)  # Пауза при ошибке
    
    async def _get_next_task(self) -> Optional[Task]:
        """Получение следующей задачи из базы данных"""
        if not self.db_pool:
            return None
            
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM tasks 
                    WHERE agent_name = $1 AND status = 'pending'
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                    """,
                    self.name
                )
                
                if row:
                    return Task(**dict(row))
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка получения задачи: {e}")
            return None
    
    async def _process_task(self, task: Task):
        """Обработка задачи"""
        try:
            # Обновление статуса задачи
            await self._update_task_status(task.id, "processing")
            
            # Выполнение задачи
            result = await self.process_task(task)
            
            # Сохранение результата
            await self._save_task_result(task.id, result)
            await self._update_task_status(task.id, "completed")
            
            self.status.tasks_completed += 1
            self.logger.info(f"Задача {task.id} выполнена агентом {self.name}")
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки задачи {task.id}: {e}")
            await self._update_task_status(task.id, "failed")
            self.status.errors_count += 1
    
    @abstractmethod
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка конкретной задачи - должен быть переопределен"""
        pass
    
    async def _background_work(self):
        """Фоновые операции агента"""
        pass
    
    async def _update_task_status(self, task_id: str, status: str):
        """Обновление статуса задачи"""
        if not self.db_pool:
            return
            
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE tasks SET status = $1 WHERE id = $2",
                    status, task_id
                )
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса задачи: {e}")
    
    async def _save_task_result(self, task_id: str, result: Dict[str, Any]):
        """Сохранение результата задачи"""
        if not self.db_pool:
            return
            
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO task_results (task_id, result, created_at)
                    VALUES ($1, $2, $3)
                    """,
                    task_id, json.dumps(result), datetime.now()
                )
        except Exception as e:
            self.logger.error(f"Ошибка сохранения результата задачи: {e}")
    
    async def send_message_to_agent(self, agent_name: str, message: Dict[str, Any]):
        """Отправка сообщения другому агенту"""
        if not self.http_session:
            return
            
        try:
            url = f"http://{agent_name}:8000/message"
            async with self.http_session.post(url, json=message) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            self.logger.error(f"Ошибка отправки сообщения агенту {agent_name}: {e}")
    
    def get_status(self) -> AgentStatus:
        """Получение статуса агента"""
        return self.status
    
    def log_activity(self, message: str, level: str = "info"):
        """Логирование активности агента"""
        log_data = {
            "agent": self.name,
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat(),
            "status": self.status.status
        }
        
        # Логирование в файл
        if level == "error":
            self.logger.error(message)
        elif level == "warning":
            self.logger.warning(message)
        else:
            self.logger.info(message)
        
        # Сохранение в базу данных
        asyncio.create_task(self._save_log(log_data))
    
    async def _save_log(self, log_data: Dict[str, Any]):
        """Сохранение лога в базу данных"""
        if not self.db_pool:
            return
            
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO agent_logs (agent_name, message, level, timestamp, status)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    log_data["agent"],
                    log_data["message"],
                    log_data["level"],
                    log_data["timestamp"],
                    log_data["status"]
                )
        except Exception as e:
            print(f"Ошибка сохранения лога: {e}")  # Fallback logging

