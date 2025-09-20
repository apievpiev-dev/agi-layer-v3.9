"""
MetaAgent - координатор всех агентов AGI Layer v3.9
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import asyncpg
from .base_agent import BaseAgent, Task, AgentStatus


class MetaAgent(BaseAgent):
    """Координатор всех агентов системы"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("meta_agent", config)
        self.agents_status: Dict[str, AgentStatus] = {}
        self.agents_configs = config.get('agents', {})
        self.health_check_interval = config.get('health_check_interval', 30)
        self.restart_failed_agents = config.get('restart_failed_agents', True)
        
    async def _initialize_agent(self):
        """Инициализация MetaAgent"""
        self.logger.info("Инициализация MetaAgent")
        
        # Создание таблиц в базе данных
        await self._create_database_tables()
        
        # Инициализация статуса агентов
        await self._initialize_agents_status()
        
        # Запуск мониторинга агентов
        asyncio.create_task(self._monitor_agents())
        
        # Запуск координации задач
        asyncio.create_task(self._coordinate_tasks())
        
    async def _create_database_tables(self):
        """Создание таблиц в базе данных"""
        try:
            async with self.db_pool.acquire() as conn:
                # Выполнение SQL схемы
                from config.database import CREATE_TABLES_SQL
                await conn.execute(CREATE_TABLES_SQL)
                self.logger.info("Таблицы базы данных созданы/обновлены")
        except Exception as e:
            self.logger.error(f"Ошибка создания таблиц: {e}")
            raise
    
    async def _initialize_agents_status(self):
        """Инициализация статуса агентов"""
        try:
            async with self.db_pool.acquire() as conn:
                # Получение агентов из конфигурации
                for agent_name in self.agents_configs.keys():
                    await conn.execute(
                        """
                        INSERT INTO agents (name, status, last_activity)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (name) DO UPDATE SET
                        status = EXCLUDED.status,
                        last_activity = EXCLUDED.last_activity
                        """,
                        agent_name, "stopped", datetime.now()
                    )
                    
                    # Инициализация статуса в памяти
                    self.agents_status[agent_name] = AgentStatus(
                        name=agent_name,
                        status="stopped",
                        last_activity=datetime.now(),
                        memory_usage=0.0,
                        cpu_usage=0.0,
                        tasks_completed=0,
                        errors_count=0
                    )
                    
        except Exception as e:
            self.logger.error(f"Ошибка инициализации статуса агентов: {e}")
            raise
    
    async def _monitor_agents(self):
        """Мониторинг состояния агентов"""
        while self.running:
            try:
                await self._check_agents_health()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Ошибка мониторинга агентов: {e}")
                await asyncio.sleep(5)
    
    async def _check_agents_health(self):
        """Проверка здоровья агентов"""
        for agent_name, agent_config in self.agents_configs.items():
            try:
                # Проверка через HTTP
                health_url = f"http://{agent_name}:8000/health"
                async with self.http_session.get(health_url, timeout=5) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        await self._update_agent_status(agent_name, "running", health_data)
                    else:
                        await self._handle_agent_failure(agent_name)
                        
            except Exception as e:
                self.logger.warning(f"Агент {agent_name} недоступен: {e}")
                await self._handle_agent_failure(agent_name)
    
    async def _handle_agent_failure(self, agent_name: str):
        """Обработка отказа агента"""
        self.logger.warning(f"Обнаружен отказ агента {agent_name}")
        
        await self._update_agent_status(agent_name, "error")
        
        if self.restart_failed_agents:
            self.logger.info(f"Попытка перезапуска агента {agent_name}")
            await self._restart_agent(agent_name)
    
    async def _restart_agent(self, agent_name: str):
        """Перезапуск агента"""
        try:
            # Отправка команды перезапуска через Docker API или HTTP
            restart_url = f"http://{agent_name}:8000/restart"
            async with self.http_session.post(restart_url, timeout=10) as response:
                if response.status == 200:
                    self.logger.info(f"Агент {agent_name} успешно перезапущен")
                    await self._update_agent_status(agent_name, "restarting")
                else:
                    self.logger.error(f"Не удалось перезапустить агент {agent_name}")
        except Exception as e:
            self.logger.error(f"Ошибка перезапуска агента {agent_name}: {e}")
    
    async def _update_agent_status(self, agent_name: str, status: str, health_data: Dict = None):
        """Обновление статуса агента"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE agents SET 
                    status = $1,
                    last_activity = $2,
                    memory_usage = $3,
                    cpu_usage = $4,
                    updated_at = CURRENT_TIMESTAMP
                    WHERE name = $5
                    """,
                    status,
                    datetime.now(),
                    health_data.get('memory_usage', 0.0) if health_data else 0.0,
                    health_data.get('cpu_usage', 0.0) if health_data else 0.0,
                    agent_name
                )
                
            # Обновление в памяти
            if agent_name in self.agents_status:
                self.agents_status[agent_name].status = status
                self.agents_status[agent_name].last_activity = datetime.now()
                if health_data:
                    self.agents_status[agent_name].memory_usage = health_data.get('memory_usage', 0.0)
                    self.agents_status[agent_name].cpu_usage = health_data.get('cpu_usage', 0.0)
                    
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса агента {agent_name}: {e}")
    
    async def _coordinate_tasks(self):
        """Координация задач между агентами"""
        while self.running:
            try:
                await self._distribute_tasks()
                await self._check_completed_tasks()
                await asyncio.sleep(self.config.get('coordination_interval', 5))
            except Exception as e:
                self.logger.error(f"Ошибка координации задач: {e}")
                await asyncio.sleep(5)
    
    async def _distribute_tasks(self):
        """Распределение задач между агентами"""
        try:
            async with self.db_pool.acquire() as conn:
                # Получение незавершенных задач
                rows = await conn.fetch(
                    """
                    SELECT * FROM tasks 
                    WHERE status IN ('pending', 'processing')
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 100
                    """
                )
                
                for row in rows:
                    task = Task(**dict(row))
                    
                    # Проверка, нужна ли перераспределение задачи
                    if task.status == 'processing':
                        # Проверка, жив ли агент, обрабатывающий задачу
                        if task.agent_name in self.agents_status:
                            agent_status = self.agents_status[task.agent_name]
                            if agent_status.status not in ['running', 'processing']:
                                # Переназначение задачи
                                await self._reassign_task(task)
                    else:
                        # Назначение новой задачи
                        await self._assign_task(task)
                        
        except Exception as e:
            self.logger.error(f"Ошибка распределения задач: {e}")
    
    async def _assign_task(self, task: Task):
        """Назначение задачи агенту"""
        try:
            # Поиск подходящего агента
            target_agent = await self._find_best_agent(task.task_type)
            
            if target_agent:
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE tasks SET agent_name = $1 WHERE id = $2",
                        target_agent, task.id
                    )
                self.logger.info(f"Задача {task.id} назначена агенту {target_agent}")
            else:
                self.logger.warning(f"Не найден подходящий агент для задачи {task.id}")
                
        except Exception as e:
            self.logger.error(f"Ошибка назначения задачи: {e}")
    
    async def _find_best_agent(self, task_type: str) -> Optional[str]:
        """Поиск лучшего агента для задачи"""
        # Простая логика выбора агента по типу задачи
        agent_mapping = {
            "image_generation": "image_agent",
            "text_processing": "text_agent", 
            "vision_analysis": "vision_agent",
            "ocr": "ocr_agent",
            "embedding": "embedding_agent",
            "recovery": "recovery_agent"
        }
        
        target_agent = agent_mapping.get(task_type)
        
        if target_agent and target_agent in self.agents_status:
            agent_status = self.agents_status[target_agent]
            if agent_status.status == "running":
                return target_agent
        
        return None
    
    async def _reassign_task(self, task: Task):
        """Переназначение задачи другому агенту"""
        try:
            async with self.db_pool.acquire() as conn:
                # Сброс статуса задачи
                await conn.execute(
                    "UPDATE tasks SET status = 'pending', agent_name = NULL WHERE id = $1",
                    task.id
                )
                
            self.logger.info(f"Задача {task.id} переназначена")
            
        except Exception as e:
            self.logger.error(f"Ошибка переназначения задачи: {e}")
    
    async def _check_completed_tasks(self):
        """Проверка завершенных задач"""
        try:
            async with self.db_pool.acquire() as conn:
                # Получение завершенных задач для архивирования
                rows = await conn.fetch(
                    """
                    SELECT t.*, tr.result 
                    FROM tasks t
                    LEFT JOIN task_results tr ON t.id = tr.task_id
                    WHERE t.status = 'completed' 
                    AND t.created_at < NOW() - INTERVAL '1 hour'
                    """
                )
                
                # Архивирование старых задач
                for row in rows:
                    await self._archive_task(row)
                    
        except Exception as e:
            self.logger.error(f"Ошибка проверки завершенных задач: {e}")
    
    async def _archive_task(self, task_data):
        """Архивирование задачи"""
        # Здесь можно добавить логику архивирования старых задач
        pass
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задачи MetaAgent"""
        if task.task_type == "system_status":
            return await self._get_system_status()
        elif task.task_type == "agent_restart":
            agent_name = task.data.get("agent_name")
            if agent_name:
                await self._restart_agent(agent_name)
                return {"status": "restarted", "agent": agent_name}
        elif task.task_type == "task_reassign":
            task_id = task.data.get("task_id")
            if task_id:
                await self._reassign_task(task)
                return {"status": "reassigned", "task_id": task_id}
        
        return {"status": "unknown_task_type"}
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        return {
            "agents": {name: {
                "status": status.status,
                "last_activity": status.last_activity.isoformat(),
                "memory_usage": status.memory_usage,
                "cpu_usage": status.cpu_usage,
                "tasks_completed": status.tasks_completed,
                "errors_count": status.errors_count
            } for name, status in self.agents_status.items()},
            "timestamp": datetime.now().isoformat()
        }
    
    async def _cleanup_agent(self):
        """Очистка ресурсов MetaAgent"""
        self.logger.info("Очистка ресурсов MetaAgent")
    
    async def create_task(self, task_type: str, data: Dict[str, Any], priority: int = 1) -> str:
        """Создание новой задачи"""
        import uuid
        
        task_id = str(uuid.uuid4())
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO tasks (id, agent_name, task_type, data, priority, status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    task_id, None, task_type, data, priority, "pending"
                )
                
            self.logger.info(f"Создана задача {task_id} типа {task_type}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"Ошибка создания задачи: {e}")
            raise
    
    async def get_agent_status(self, agent_name: str) -> Optional[AgentStatus]:
        """Получение статуса конкретного агента"""
        return self.agents_status.get(agent_name)
    
    async def get_all_agents_status(self) -> Dict[str, AgentStatus]:
        """Получение статуса всех агентов"""
        return self.agents_status.copy()

