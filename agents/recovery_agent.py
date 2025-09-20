"""
RecoveryAgent - восстановление системы из логов и ChromaDB
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncpg
from .base_agent import BaseAgent, Task


class RecoveryAgent(BaseAgent):
    """Агент для восстановления системы"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("recovery_agent", config)
        self.logs_path = config.get('logs_path', '/app/logs')
        self.recovery_interval = config.get('recovery_interval', 300)  # 5 минут
        self.max_recovery_age = config.get('max_recovery_age', 3600)  # 1 час
        
    async def _initialize_agent(self):
        """Инициализация RecoveryAgent"""
        self.logger.info("Инициализация RecoveryAgent")
        
        # Создание директории для логов
        os.makedirs(self.logs_path, exist_ok=True)
        
        # Запуск периодического восстановления
        asyncio.create_task(self._periodic_recovery())
        
        self.logger.info("RecoveryAgent успешно инициализирован")
    
    async def _periodic_recovery(self):
        """Периодическое восстановление системы"""
        while self.running:
            try:
                await self._check_and_recover()
                await asyncio.sleep(self.recovery_interval)
            except Exception as e:
                self.logger.error(f"Ошибка периодического восстановления: {e}")
                await asyncio.sleep(60)  # Пауза при ошибке
    
    async def _check_and_recover(self):
        """Проверка и восстановление системы"""
        try:
            self.logger.info("Проверка системы на необходимость восстановления")
            
            # Проверка незавершенных задач
            await self._recover_unfinished_tasks()
            
            # Проверка ошибок агентов
            await self._recover_failed_agents()
            
            # Восстановление из логов
            await self._recover_from_logs()
            
            # Очистка старых данных
            await self._cleanup_old_data()
            
        except Exception as e:
            self.logger.error(f"Ошибка восстановления системы: {e}")
    
    async def _recover_unfinished_tasks(self):
        """Восстановление незавершенных задач"""
        try:
            async with self.db_pool.acquire() as conn:
                # Поиск задач в статусе "processing" старше 5 минут
                cutoff_time = datetime.now() - timedelta(minutes=5)
                
                rows = await conn.fetch(
                    """
                    SELECT * FROM tasks 
                    WHERE status = 'processing' 
                    AND updated_at < $1
                    """,
                    cutoff_time
                )
                
                if rows:
                    self.logger.info(f"Найдено {len(rows)} незавершенных задач для восстановления")
                    
                    for row in rows:
                        await self._recover_task(row)
                        
        except Exception as e:
            self.logger.error(f"Ошибка восстановления незавершенных задач: {e}")
    
    async def _recover_task(self, task_row):
        """Восстановление конкретной задачи"""
        try:
            task_id = task_row['id']
            agent_name = task_row['agent_name']
            
            self.logger.info(f"Восстановление задачи {task_id} от агента {agent_name}")
            
            async with self.db_pool.acquire() as conn:
                # Проверка, жив ли агент
                agent_status = await conn.fetchval(
                    "SELECT status FROM agents WHERE name = $1",
                    agent_name
                )
                
                if agent_status and agent_status == "running":
                    # Агент жив - сбрасываем задачу в pending
                    await conn.execute(
                        "UPDATE tasks SET status = 'pending', updated_at = CURRENT_TIMESTAMP WHERE id = $1",
                        task_id
                    )
                    self.logger.info(f"Задача {task_id} сброшена в pending")
                else:
                    # Агент мертв - переназначаем задачу
                    await conn.execute(
                        "UPDATE tasks SET agent_name = NULL, status = 'pending', updated_at = CURRENT_TIMESTAMP WHERE id = $1",
                        task_id
                    )
                    self.logger.info(f"Задача {task_id} переназначена")
                    
        except Exception as e:
            self.logger.error(f"Ошибка восстановления задачи {task_row.get('id', 'unknown')}: {e}")
    
    async def _recover_failed_agents(self):
        """Восстановление отказавших агентов"""
        try:
            async with self.db_pool.acquire() as conn:
                # Поиск агентов в статусе "error"
                rows = await conn.fetch(
                    "SELECT * FROM agents WHERE status = 'error'"
                )
                
                if rows:
                    self.logger.info(f"Найдено {len(rows)} отказавших агентов")
                    
                    for row in rows:
                        await self._attempt_agent_recovery(row)
                        
        except Exception as e:
            self.logger.error(f"Ошибка восстановления отказавших агентов: {e}")
    
    async def _attempt_agent_recovery(self, agent_row):
        """Попытка восстановления агента"""
        try:
            agent_name = agent_row['name']
            error_count = agent_row['errors_count']
            
            # Проверка, не слишком ли много ошибок
            if error_count > 10:
                self.logger.warning(f"Агент {agent_name} имеет слишком много ошибок ({error_count})")
                return
            
            self.logger.info(f"Попытка восстановления агента {agent_name}")
            
            # Отправка команды перезапуска через MetaAgent
            recovery_task = Task(
                id=f"recovery_{agent_name}_{datetime.now().timestamp()}",
                agent_name="meta_agent",
                task_type="agent_restart",
                data={"agent_name": agent_name}
            )
            
            # Создание задачи восстановления
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO tasks (id, agent_name, task_type, data, priority, status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    recovery_task.id,
                    recovery_task.agent_name,
                    recovery_task.task_type,
                    recovery_task.data,
                    3,  # Высокий приоритет
                    "pending"
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка попытки восстановления агента {agent_row.get('name', 'unknown')}: {e}")
    
    async def _recover_from_logs(self):
        """Восстановление из логов"""
        try:
            # Поиск логов с ошибками
            error_logs = await self._find_error_logs()
            
            if error_logs:
                self.logger.info(f"Найдено {len(error_logs)} логов с ошибками")
                
                for log_entry in error_logs:
                    await self._process_error_log(log_entry)
                    
        except Exception as e:
            self.logger.error(f"Ошибка восстановления из логов: {e}")
    
    async def _find_error_logs(self) -> List[Dict[str, Any]]:
        """Поиск логов с ошибками"""
        error_logs = []
        
        try:
            # Поиск в базе данных
            async with self.db_pool.acquire() as conn:
                cutoff_time = datetime.now() - timedelta(hours=1)
                
                rows = await conn.fetch(
                    """
                    SELECT * FROM agent_logs 
                    WHERE level = 'error' 
                    AND timestamp > $1
                    ORDER BY timestamp DESC
                    LIMIT 100
                    """,
                    cutoff_time
                )
                
                for row in rows:
                    error_logs.append({
                        "agent": row['agent_name'],
                        "message": row['message'],
                        "timestamp": row['timestamp'],
                        "status": row['status']
                    })
            
            # Поиск в файловых логах
            log_files = await self._find_log_files()
            for log_file in log_files:
                file_errors = await self._parse_log_file(log_file)
                error_logs.extend(file_errors)
                
        except Exception as e:
            self.logger.error(f"Ошибка поиска логов: {e}")
        
        return error_logs
    
    async def _find_log_files(self) -> List[str]:
        """Поиск файлов логов"""
        log_files = []
        
        try:
            if os.path.exists(self.logs_path):
                for filename in os.listdir(self.logs_path):
                    if filename.endswith('.log') or filename.endswith('.json'):
                        log_files.append(os.path.join(self.logs_path, filename))
        except Exception as e:
            self.logger.error(f"Ошибка поиска файлов логов: {e}")
        
        return log_files
    
    async def _parse_log_file(self, log_file: str) -> List[Dict[str, Any]]:
        """Парсинг файла лога"""
        errors = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Поиск ошибок в JSON логах
                    if line.startswith('{'):
                        try:
                            log_entry = json.loads(line)
                            if log_entry.get('level') == 'ERROR':
                                errors.append({
                                    "agent": log_entry.get('agent', 'unknown'),
                                    "message": log_entry.get('message', ''),
                                    "timestamp": log_entry.get('timestamp', ''),
                                    "file": log_file,
                                    "line": line_num
                                })
                        except json.JSONDecodeError:
                            continue
                    
                    # Поиск ошибок в текстовых логах
                    elif 'ERROR' in line or 'CRITICAL' in line:
                        errors.append({
                            "agent": "unknown",
                            "message": line,
                            "timestamp": "",
                            "file": log_file,
                            "line": line_num
                        })
                        
        except Exception as e:
            self.logger.error(f"Ошибка парсинга файла лога {log_file}: {e}")
        
        return errors
    
    async def _process_error_log(self, log_entry: Dict[str, Any]):
        """Обработка лога с ошибкой"""
        try:
            agent_name = log_entry.get('agent')
            message = log_entry.get('message', '')
            
            # Анализ типа ошибки и определение действий
            if 'connection' in message.lower() or 'timeout' in message.lower():
                await self._handle_connection_error(agent_name, message)
            elif 'memory' in message.lower() or 'oom' in message.lower():
                await self._handle_memory_error(agent_name, message)
            elif 'model' in message.lower() or 'load' in message.lower():
                await self._handle_model_error(agent_name, message)
            else:
                await self._handle_generic_error(agent_name, message)
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки лога: {e}")
    
    async def _handle_connection_error(self, agent_name: str, message: str):
        """Обработка ошибок соединения"""
        self.logger.info(f"Обработка ошибки соединения для агента {agent_name}")
        # Можно добавить логику повторного подключения
    
    async def _handle_memory_error(self, agent_name: str, message: str):
        """Обработка ошибок памяти"""
        self.logger.info(f"Обработка ошибки памяти для агента {agent_name}")
        # Можно добавить логику очистки памяти
    
    async def _handle_model_error(self, agent_name: str, message: str):
        """Обработка ошибок модели"""
        self.logger.info(f"Обработка ошибки модели для агента {agent_name}")
        # Можно добавить логику перезагрузки модели
    
    async def _handle_generic_error(self, agent_name: str, message: str):
        """Обработка общих ошибок"""
        self.logger.info(f"Обработка общей ошибки для агента {agent_name}")
        # Можно добавить общую логику восстановления
    
    async def _cleanup_old_data(self):
        """Очистка старых данных"""
        try:
            async with self.db_pool.acquire() as conn:
                # Очистка старых логов
                cutoff_time = datetime.now() - timedelta(days=7)
                
                deleted_logs = await conn.execute(
                    "DELETE FROM agent_logs WHERE timestamp < $1",
                    cutoff_time
                )
                
                # Очистка старых завершенных задач
                cutoff_tasks = datetime.now() - timedelta(days=1)
                
                deleted_tasks = await conn.execute(
                    "DELETE FROM tasks WHERE status = 'completed' AND created_at < $1",
                    cutoff_tasks
                )
                
                self.logger.info(f"Очистка: удалено логов и задач")
                
        except Exception as e:
            self.logger.error(f"Ошибка очистки старых данных: {e}")
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задач восстановления"""
        if task.task_type == "manual_recovery":
            return await self._manual_recovery(task)
        elif task.task_type == "system_health_check":
            return await self._system_health_check(task)
        elif task.task_type == "backup_data":
            return await self._backup_data(task)
        
        return {"status": "unknown_task_type"}
    
    async def _manual_recovery(self, task: Task) -> Dict[str, Any]:
        """Ручное восстановление системы"""
        try:
            self.logger.info("Выполнение ручного восстановления системы")
            
            # Принудительная проверка и восстановление
            await self._check_and_recover()
            
            return {
                "status": "success",
                "message": "Ручное восстановление выполнено",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка ручного восстановления: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _system_health_check(self, task: Task) -> Dict[str, Any]:
        """Проверка здоровья системы"""
        try:
            async with self.db_pool.acquire() as conn:
                # Статистика агентов
                agents_stats = await conn.fetch("SELECT name, status, errors_count, tasks_completed FROM agents")
                
                # Статистика задач
                tasks_stats = await conn.fetch(
                    "SELECT status, COUNT(*) as count FROM tasks GROUP BY status"
                )
                
                # Статистика ошибок
                error_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM agent_logs WHERE level = 'error' AND timestamp > $1",
                    datetime.now() - timedelta(hours=1)
                )
                
                health_report = {
                    "agents": [dict(row) for row in agents_stats],
                    "tasks": [dict(row) for row in tasks_stats],
                    "recent_errors": error_count,
                    "timestamp": datetime.now().isoformat()
                }
                
                return {
                    "status": "success",
                    "health_report": health_report
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка проверки здоровья системы: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _backup_data(self, task: Task) -> Dict[str, Any]:
        """Создание резервной копии данных"""
        try:
            backup_path = task.data.get("backup_path", "/app/backups")
            os.makedirs(backup_path, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_path, f"recovery_backup_{timestamp}.json")
            
            # Экспорт данных
            async with self.db_pool.acquire() as conn:
                # Экспорт агентов
                agents = await conn.fetch("SELECT * FROM agents")
                
                # Экспорт задач
                tasks = await conn.fetch("SELECT * FROM tasks WHERE status != 'completed'")
                
                backup_data = {
                    "timestamp": timestamp,
                    "agents": [dict(row) for row in agents],
                    "tasks": [dict(row) for row in tasks]
                }
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
            
            return {
                "status": "success",
                "backup_file": backup_file,
                "agents_count": len(backup_data["agents"]),
                "tasks_count": len(backup_data["tasks"])
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка создания резервной копии: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _cleanup_agent(self):
        """Очистка ресурсов RecoveryAgent"""
        self.logger.info("RecoveryAgent очищен")
    
    async def get_recovery_status(self) -> Dict[str, Any]:
        """Получение статуса восстановления"""
        return {
            "agent_name": self.name,
            "recovery_interval": self.recovery_interval,
            "logs_path": self.logs_path,
            "last_recovery": datetime.now().isoformat()
        }

