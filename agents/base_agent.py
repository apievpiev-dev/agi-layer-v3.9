"""
BaseAgent - базовый класс для всех агентов AGI Layer v3.9
Все агенты наследуются от этого класса
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import aiohttp
import os
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor


@dataclass
class Task:
    """Структура задачи для агентов"""
    id: str
    agent_name: str
    task_type: str
    data: Dict[str, Any]
    priority: int = 1
    created_at: Optional[datetime] = None
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class BaseAgent(ABC):
    """Базовый класс для всех агентов"""
    
    def __init__(self, agent_name: str, config: Dict[str, Any]):
        self.agent_name = agent_name
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.status = "initializing"
        self.tasks_queue = asyncio.Queue()
        self.running = False
        
        # Настройка логирования
        self.logger = logging.getLogger(f"AGI.{agent_name}")
        self.logger.setLevel(logging.INFO)
        
        # Создаем handler для файла если его нет
        if not self.logger.handlers:
            handler = logging.FileHandler(f"/workspace/logs/{agent_name}.log")
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Конфигурация БД
        self.db_config = {
            'host': config.get('postgres_host', 'localhost'),
            'port': config.get('postgres_port', 5432),
            'database': config.get('postgres_db', 'agi_layer'),
            'user': config.get('postgres_user', 'agi_user'),
            'password': config.get('postgres_password', 'agi_password')
        }
        
        # HTTP клиент для межагентного взаимодействия
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        self.logger.info(f"Агент {agent_name} инициализирован с ID: {self.agent_id}")
    
    async def initialize(self):
        """Инициализация агента"""
        try:
            self.logger.info(f"Инициализация агента {self.agent_name}")
            
            # Создаем HTTP сессию
            self.http_session = aiohttp.ClientSession()
            
            # Инициализация БД
            await self._init_database()
            
            # Специфичная инициализация агента
            await self._initialize_agent()
            
            self.status = "ready"
            self.logger.info(f"Агент {self.agent_name} готов к работе")
            
        except Exception as e:
            self.status = "error"
            self.logger.error(f"Ошибка инициализации агента {self.agent_name}: {e}")
            raise
    
    async def _init_database(self):
        """Инициализация подключения к базе данных"""
        try:
            # Создаем таблицы если их нет
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Таблица задач
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id VARCHAR(36) PRIMARY KEY,
                    agent_name VARCHAR(100) NOT NULL,
                    task_type VARCHAR(100) NOT NULL,
                    data JSONB NOT NULL,
                    priority INTEGER DEFAULT 1,
                    status VARCHAR(50) DEFAULT 'pending',
                    result JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица логов агентов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_logs (
                    id SERIAL PRIMARY KEY,
                    agent_name VARCHAR(100) NOT NULL,
                    agent_id VARCHAR(36) NOT NULL,
                    level VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица статуса агентов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_status (
                    agent_name VARCHAR(100) PRIMARY KEY,
                    agent_id VARCHAR(36) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    config JSONB,
                    metrics JSONB
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.logger.info("База данных инициализирована")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации БД: {e}")
            raise
    
    @abstractmethod
    async def _initialize_agent(self):
        """Специфичная инициализация агента (переопределяется в наследниках)"""
        pass
    
    @abstractmethod
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задачи (переопределяется в наследниках)"""
        pass
    
    async def start(self):
        """Запуск агента"""
        if self.running:
            return
        
        self.running = True
        self.logger.info(f"Запуск агента {self.agent_name}")
        
        # Обновляем статус в БД
        await self._update_status("running")
        
        # Запускаем основной цикл обработки задач
        asyncio.create_task(self._main_loop())
        
        # Запускаем heartbeat
        asyncio.create_task(self._heartbeat_loop())
    
    async def stop(self):
        """Остановка агента"""
        self.running = False
        self.logger.info(f"Остановка агента {self.agent_name}")
        
        await self._update_status("stopped")
        
        if self.http_session:
            await self.http_session.close()
        
        # Очистка ресурсов агента
        await self._cleanup_agent()
    
    async def _main_loop(self):
        """Основной цикл обработки задач"""
        while self.running:
            try:
                # Получаем задачу из очереди (с таймаутом)
                try:
                    task = await asyncio.wait_for(self.tasks_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                self.logger.info(f"Обработка задачи {task.id} типа {task.task_type}")
                
                # Обновляем статус задачи
                await self._update_task_status(task.id, "processing")
                
                try:
                    # Обрабатываем задачу
                    result = await self.process_task(task)
                    
                    # Сохраняем результат
                    await self._save_task_result(task.id, result, "completed")
                    
                    self.logger.info(f"Задача {task.id} выполнена успешно")
                    
                except Exception as e:
                    self.logger.error(f"Ошибка обработки задачи {task.id}: {e}")
                    await self._save_task_result(task.id, {"error": str(e)}, "failed")
                
                # Отмечаем задачу как выполненную
                self.tasks_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Ошибка в основном цикле агента {self.agent_name}: {e}")
                await asyncio.sleep(5)  # Пауза при ошибке
    
    async def _heartbeat_loop(self):
        """Цикл отправки heartbeat"""
        while self.running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(30)  # Heartbeat каждые 30 секунд
            except Exception as e:
                self.logger.error(f"Ошибка heartbeat: {e}")
                await asyncio.sleep(10)
    
    async def add_task(self, task: Task):
        """Добавление задачи в очередь"""
        # Сохраняем задачу в БД
        await self._save_task(task)
        
        # Добавляем в очередь
        await self.tasks_queue.put(task)
        
        self.logger.info(f"Задача {task.id} добавлена в очередь агента {self.agent_name}")
    
    async def _save_task(self, task: Task):
        """Сохранение задачи в БД"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO tasks (id, agent_name, task_type, data, priority, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    data = EXCLUDED.data,
                    priority = EXCLUDED.priority,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                task.id,
                task.agent_name,
                task.task_type,
                json.dumps(task.data),
                task.priority,
                task.status,
                task.created_at
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения задачи: {e}")
    
    async def _update_task_status(self, task_id: str, status: str):
        """Обновление статуса задачи"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE tasks SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (status, task_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса задачи: {e}")
    
    async def _save_task_result(self, task_id: str, result: Dict[str, Any], status: str):
        """Сохранение результата задачи"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE tasks SET result = %s, status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (json.dumps(result), status, task_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения результата задачи: {e}")
    
    async def _update_status(self, status: str):
        """Обновление статуса агента в БД"""
        try:
            self.status = status
            
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO agent_status (agent_name, agent_id, status, last_heartbeat, config)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s)
                ON CONFLICT (agent_name) DO UPDATE SET
                    agent_id = EXCLUDED.agent_id,
                    status = EXCLUDED.status,
                    last_heartbeat = CURRENT_TIMESTAMP,
                    config = EXCLUDED.config
            """, (
                self.agent_name,
                self.agent_id,
                status,
                json.dumps(self.config)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса агента: {e}")
    
    async def _send_heartbeat(self):
        """Отправка heartbeat"""
        try:
            # Получаем метрики агента
            metrics = await self._get_metrics()
            
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE agent_status SET 
                    last_heartbeat = CURRENT_TIMESTAMP,
                    metrics = %s
                WHERE agent_name = %s
            """, (json.dumps(metrics), self.agent_name))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки heartbeat: {e}")
    
    async def _get_metrics(self) -> Dict[str, Any]:
        """Получение метрик агента"""
        return {
            "status": self.status,
            "queue_size": self.tasks_queue.qsize(),
            "agent_id": self.agent_id,
            "uptime": (datetime.now() - datetime.now()).total_seconds()  # Заглушка
        }
    
    async def send_to_agent(self, agent_name: str, task_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Отправка задачи другому агенту"""
        try:
            if not self.http_session:
                self.http_session = aiohttp.ClientSession()
            
            # URL агента (предполагаем, что агенты слушают на портах)
            agent_ports = {
                "meta_agent": 8001,
                "telegram_agent": 8002,
                "image_gen_agent": 8003,
                "vision_agent": 8004,
                "memory_agent": 8005,
                "report_agent": 8006,
                "watchdog_agent": 8007,
                "recovery_agent": 8008
            }
            
            port = agent_ports.get(agent_name, 8000)
            url = f"http://{agent_name}:{port}/process_task"
            
            task_data = {
                "id": str(uuid.uuid4()),
                "agent_name": agent_name,
                "task_type": task_type,
                "data": data,
                "sender": self.agent_name
            }
            
            async with self.http_session.post(url, json=task_data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    self.logger.error(f"Ошибка отправки задачи агенту {agent_name}: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Ошибка отправки задачи агенту {agent_name}: {e}")
            return None
    
    async def _cleanup_agent(self):
        """Очистка ресурсов агента (переопределяется в наследниках)"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья агента"""
        return {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "status": self.status,
            "running": self.running,
            "queue_size": self.tasks_queue.qsize(),
            "timestamp": datetime.now().isoformat()
        }
    
    def log_to_db(self, level: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Логирование в базу данных"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO agent_logs (agent_name, agent_id, level, message, data)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                self.agent_name,
                self.agent_id,
                level,
                message,
                json.dumps(data) if data else None
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Ошибка записи в БД лог: {e}")