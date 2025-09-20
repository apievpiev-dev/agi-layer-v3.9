"""
MetaAgent - координатор всех агентов AGI Layer v3.9
Принимает задачи, анализирует их и распределяет между специализированными агентами
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from .base_agent import BaseAgent, Task


class TaskRequest(BaseModel):
    """Модель запроса задачи"""
    task_type: str
    data: Dict[str, Any]
    priority: int = 1
    user_id: Optional[str] = None


class MetaAgent(BaseAgent):
    """Мета-агент - координатор всех агентов"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("meta_agent", config)
        
        # Карта агентов и их специализаций
        self.agent_capabilities = {
            "telegram_agent": ["telegram_message", "telegram_command", "user_interaction"],
            "image_gen_agent": ["image_generation", "text_to_image", "image_editing"],
            "vision_agent": ["image_analysis", "ocr", "visual_understanding"],
            "memory_agent": ["memory_store", "memory_retrieve", "knowledge_search"],
            "report_agent": ["report_generation", "data_analysis", "visualization"],
            "watchdog_agent": ["health_check", "service_monitoring", "restart_service"],
            "recovery_agent": ["task_recovery", "data_recovery", "system_restore"]
        }
        
        # Активные агенты
        self.active_agents = set()
        
        # FastAPI приложение для HTTP API
        self.app = FastAPI(title="MetaAgent API", version="3.9")
        self._setup_routes()
        
        # Статистика выполнения задач
        self.task_stats = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "in_progress": 0
        }
    
    def _setup_routes(self):
        """Настройка маршрутов FastAPI"""
        
        @self.app.post("/process_task")
        async def process_task_endpoint(request: TaskRequest):
            """Обработка задачи через HTTP API"""
            try:
                task = Task(
                    id=str(uuid.uuid4()),
                    agent_name="meta_agent",
                    task_type=request.task_type,
                    data=request.data,
                    priority=request.priority
                )
                
                await self.add_task(task)
                
                return {
                    "status": "accepted",
                    "task_id": task.id,
                    "message": "Задача принята к обработке"
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/status")
        async def get_status():
            """Получение статуса мета-агента"""
            return await self.health_check()
        
        @self.app.get("/agents")
        async def get_agents():
            """Получение списка активных агентов"""
            return {
                "active_agents": list(self.active_agents),
                "agent_capabilities": self.agent_capabilities,
                "task_stats": self.task_stats
            }
        
        @self.app.post("/agent/{agent_name}/task")
        async def send_task_to_agent(agent_name: str, request: TaskRequest):
            """Отправка задачи конкретному агенту"""
            try:
                if agent_name not in self.agent_capabilities:
                    raise HTTPException(status_code=404, detail=f"Агент {agent_name} не найден")
                
                result = await self.send_to_agent(agent_name, request.task_type, request.data)
                
                if result:
                    return {"status": "success", "result": result}
                else:
                    raise HTTPException(status_code=500, detail="Ошибка выполнения задачи")
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _initialize_agent(self):
        """Инициализация мета-агента"""
        self.logger.info("Инициализация MetaAgent")
        
        # Запускаем HTTP сервер
        asyncio.create_task(self._start_http_server())
        
        # Проверяем доступность других агентов
        await self._discover_agents()
        
        self.logger.info("MetaAgent инициализирован успешно")
    
    async def _start_http_server(self):
        """Запуск HTTP сервера"""
        try:
            config = uvicorn.Config(
                app=self.app,
                host="0.0.0.0",
                port=8001,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            self.logger.error(f"Ошибка запуска HTTP сервера: {e}")
    
    async def _discover_agents(self):
        """Обнаружение доступных агентов"""
        self.logger.info("Поиск доступных агентов...")
        
        for agent_name in self.agent_capabilities.keys():
            try:
                # Пытаемся отправить ping агенту
                result = await self.send_to_agent(agent_name, "ping", {})
                if result:
                    self.active_agents.add(agent_name)
                    self.logger.info(f"Агент {agent_name} доступен")
                else:
                    self.logger.warning(f"Агент {agent_name} недоступен")
            except Exception as e:
                self.logger.warning(f"Ошибка проверки агента {agent_name}: {e}")
        
        self.logger.info(f"Найдено активных агентов: {len(self.active_agents)}")
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задачи мета-агентом"""
        try:
            self.task_stats["total"] += 1
            self.task_stats["in_progress"] += 1
            
            self.logger.info(f"Обработка задачи {task.id} типа {task.task_type}")
            
            # Анализируем задачу и определяем подходящего агента
            target_agent = await self._analyze_task(task)
            
            if not target_agent:
                # Если не можем определить агента, пытаемся обработать сами
                result = await self._handle_meta_task(task)
            else:
                # Отправляем задачу целевому агенту
                result = await self._delegate_task(task, target_agent)
            
            if result and result.get("status") == "success":
                self.task_stats["completed"] += 1
            else:
                self.task_stats["failed"] += 1
            
            self.task_stats["in_progress"] -= 1
            
            return result
            
        except Exception as e:
            self.task_stats["failed"] += 1
            self.task_stats["in_progress"] -= 1
            self.logger.error(f"Ошибка обработки задачи {task.id}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _analyze_task(self, task: Task) -> Optional[str]:
        """Анализ задачи и определение подходящего агента"""
        task_type = task.task_type.lower()
        
        # Правила маршрутизации задач
        routing_rules = {
            # Telegram задачи
            "telegram": "telegram_agent",
            "message": "telegram_agent",
            "command": "telegram_agent",
            
            # Генерация изображений
            "image_generation": "image_gen_agent",
            "generate_image": "image_gen_agent",
            "text_to_image": "image_gen_agent",
            "create_image": "image_gen_agent",
            
            # Анализ изображений
            "image_analysis": "vision_agent",
            "analyze_image": "vision_agent",
            "ocr": "vision_agent",
            "visual": "vision_agent",
            
            # Память и знания
            "memory": "memory_agent",
            "remember": "memory_agent",
            "recall": "memory_agent",
            "search": "memory_agent",
            
            # Отчеты
            "report": "report_agent",
            "analyze": "report_agent",
            "statistics": "report_agent",
            
            # Системные задачи
            "health": "watchdog_agent",
            "monitor": "watchdog_agent",
            "restart": "watchdog_agent",
            
            # Восстановление
            "recovery": "recovery_agent",
            "restore": "recovery_agent",
            "recover": "recovery_agent"
        }
        
        # Ищем подходящего агента
        for keyword, agent_name in routing_rules.items():
            if keyword in task_type:
                if agent_name in self.active_agents:
                    return agent_name
                else:
                    self.logger.warning(f"Агент {agent_name} недоступен для задачи {task_type}")
        
        # Дополнительный анализ по содержимому
        data = task.data
        
        if "image" in str(data).lower() or "picture" in str(data).lower():
            if "generate" in str(data).lower() or "create" in str(data).lower():
                return "image_gen_agent" if "image_gen_agent" in self.active_agents else None
            else:
                return "vision_agent" if "vision_agent" in self.active_agents else None
        
        if "telegram" in str(data).lower() or "chat" in str(data).lower():
            return "telegram_agent" if "telegram_agent" in self.active_agents else None
        
        return None
    
    async def _delegate_task(self, task: Task, target_agent: str) -> Dict[str, Any]:
        """Делегирование задачи целевому агенту"""
        try:
            self.logger.info(f"Делегирование задачи {task.id} агенту {target_agent}")
            
            # Отправляем задачу агенту
            result = await self.send_to_agent(target_agent, task.task_type, task.data)
            
            if result:
                self.logger.info(f"Задача {task.id} выполнена агентом {target_agent}")
                return {
                    "status": "success",
                    "result": result,
                    "processed_by": target_agent,
                    "task_id": task.id
                }
            else:
                self.logger.error(f"Агент {target_agent} не смог обработать задачу {task.id}")
                return {
                    "status": "error",
                    "error": f"Агент {target_agent} недоступен или не смог обработать задачу",
                    "task_id": task.id
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка делегирования задачи {task.id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "task_id": task.id
            }
    
    async def _handle_meta_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задач самим мета-агентом"""
        task_type = task.task_type.lower()
        
        if task_type == "ping":
            return {"status": "success", "message": "pong", "agent": "meta_agent"}
        
        elif task_type == "status":
            return await self.health_check()
        
        elif task_type == "list_agents":
            return {
                "status": "success",
                "active_agents": list(self.active_agents),
                "agent_capabilities": self.agent_capabilities
            }
        
        elif task_type == "task_stats":
            return {
                "status": "success",
                "stats": self.task_stats
            }
        
        elif task_type == "complex_task":
            # Обработка сложных задач, требующих координации нескольких агентов
            return await self._handle_complex_task(task)
        
        else:
            return {
                "status": "error",
                "error": f"Неизвестный тип задачи для мета-агента: {task_type}"
            }
    
    async def _handle_complex_task(self, task: Task) -> Dict[str, Any]:
        """Обработка сложных задач, требующих нескольких агентов"""
        try:
            data = task.data
            subtasks = data.get("subtasks", [])
            
            if not subtasks:
                return {"status": "error", "error": "Не указаны подзадачи для комплексной задачи"}
            
            results = []
            
            for subtask_data in subtasks:
                subtask = Task(
                    id=str(uuid.uuid4()),
                    agent_name="meta_agent",
                    task_type=subtask_data.get("type", "unknown"),
                    data=subtask_data.get("data", {}),
                    priority=subtask_data.get("priority", 1)
                )
                
                # Обрабатываем каждую подзадачу
                result = await self.process_task(subtask)
                results.append({
                    "subtask_id": subtask.id,
                    "subtask_type": subtask.task_type,
                    "result": result
                })
            
            return {
                "status": "success",
                "message": "Комплексная задача выполнена",
                "results": results,
                "total_subtasks": len(subtasks)
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_metrics(self) -> Dict[str, Any]:
        """Получение метрик мета-агента"""
        base_metrics = await super()._get_metrics()
        
        base_metrics.update({
            "active_agents": len(self.active_agents),
            "agent_capabilities": len(self.agent_capabilities),
            "task_stats": self.task_stats,
            "http_server_running": True  # Заглушка
        })
        
        return base_metrics
    
    async def _cleanup_agent(self):
        """Очистка ресурсов мета-агента"""
        self.logger.info("Очистка ресурсов MetaAgent")
        # Здесь можно добавить специфичную очистку


# Функция для запуска мета-агента
async def run_meta_agent(config: Dict[str, Any]):
    """Запуск мета-агента"""
    agent = MetaAgent(config)
    await agent.initialize()
    await agent.start()
    
    try:
        # Держим агента запущенным
        while agent.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Получен сигнал остановки")
    finally:
        await agent.stop()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    config = {
        'postgres_host': os.getenv('POSTGRES_HOST', 'localhost'),
        'postgres_port': int(os.getenv('POSTGRES_PORT', 5432)),
        'postgres_db': os.getenv('POSTGRES_DB', 'agi_layer'),
        'postgres_user': os.getenv('POSTGRES_USER', 'agi_user'),
        'postgres_password': os.getenv('POSTGRES_PASSWORD', 'agi_password')
    }
    
    asyncio.run(run_meta_agent(config))