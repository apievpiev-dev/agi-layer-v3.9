"""
MetaAgent - Координатор всех агентов AGI Layer v3.9
==================================================

Отвечает за:
- Координацию работы всех агентов
- Распределение задач
- Мониторинг состояния системы
- Восстановление после сбоев
- Масштабирование агентов
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import redis
from loguru import logger

from base_agent import BaseAgent, AgentConfig, AgentMessage


class MetaAgent(BaseAgent):
    """Мета-агент для координации других агентов"""
    
    def __init__(self):
        config = AgentConfig(
            name="meta_agent",
            type="coordinator",
            max_memory="4G",
            max_cpu_cores=2
        )
        super().__init__(config)
        
        # Реестр агентов
        self.registered_agents: Dict[str, Dict] = {}
        self.agent_queues: Dict[str, List] = {}
        
        # Статистика системы
        self.system_stats = {
            "total_agents": 0,
            "active_agents": 0,
            "failed_agents": 0,
            "total_messages": 0,
            "uptime": datetime.now()
        }

    async def _load_model(self):
        """MetaAgent не использует ML модели"""
        pass

    async def _agent_specific_init(self):
        """Специфичная инициализация MetaAgent"""
        # Создаем базовые каналы в Redis
        channels = [
            "agent_registration",
            "agent_tasks",
            "agent_status",
            "system_commands"
        ]
        
        for channel in channels:
            await asyncio.to_thread(
                self.redis_client.delete, channel
            )
        
        logger.info("MetaAgent: каналы Redis инициализированы")

    async def _agent_main_loop(self):
        """Основной цикл MetaAgent"""
        while self.is_running:
            try:
                # Проверяем состояние всех агентов
                await self._check_agents_health()
                
                # Обрабатываем очереди задач
                await self._process_task_queues()
                
                # Обновляем статистику
                await self._update_system_stats()
                
                # Пауза между циклами
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Ошибка в главном цикле MetaAgent: {e}")
                await asyncio.sleep(5)

    async def _check_agents_health(self):
        """Проверка здоровья всех агентов"""
        try:
            # Получаем все heartbeat записи
            pattern = "heartbeat_*"
            keys = await asyncio.to_thread(
                self.redis_client.keys, pattern
            )
            
            current_time = datetime.now()
            healthy_agents = 0
            
            for key in keys:
                try:
                    data = await asyncio.to_thread(
                        self.redis_client.get, key
                    )
                    if data:
                        heartbeat = json.loads(data)
                        agent_name = heartbeat["agent_name"]
                        last_heartbeat = datetime.fromisoformat(heartbeat["timestamp"])
                        
                        # Проверяем, не устарел ли heartbeat (больше 2 минут)
                        if (current_time - last_heartbeat).seconds > 120:
                            logger.warning(f"Агент {agent_name} не отвечает более 2 минут")
                            await self._restart_agent(agent_name)
                        else:
                            healthy_agents += 1
                            
                        # Обновляем реестр агентов
                        self.registered_agents[agent_name] = heartbeat
                        
                except Exception as e:
                    logger.error(f"Ошибка обработки heartbeat {key}: {e}")
            
            self.system_stats["active_agents"] = healthy_agents
            
        except Exception as e:
            logger.error(f"Ошибка проверки здоровья агентов: {e}")

    async def _restart_agent(self, agent_name: str):
        """Перезапуск упавшего агента"""
        try:
            logger.info(f"Попытка перезапуска агента {agent_name}")
            
            # Отправляем команду на перезапуск через Redis
            restart_command = {
                "command": "restart",
                "agent_name": agent_name,
                "timestamp": datetime.now().isoformat(),
                "requested_by": self.name
            }
            
            await asyncio.to_thread(
                self.redis_client.publish,
                "system_commands",
                json.dumps(restart_command)
            )
            
            logger.info(f"Команда перезапуска отправлена для {agent_name}")
            
        except Exception as e:
            logger.error(f"Ошибка перезапуска агента {agent_name}: {e}")

    async def _process_task_queues(self):
        """Обработка очередей задач"""
        try:
            # Получаем задачи из очереди
            tasks_key = "pending_tasks"
            task_data = await asyncio.to_thread(
                self.redis_client.lpop, tasks_key
            )
            
            if task_data:
                task = json.loads(task_data)
                await self._assign_task(task)
                
        except Exception as e:
            logger.error(f"Ошибка обработки очередей задач: {e}")

    async def _assign_task(self, task: Dict):
        """Назначение задачи подходящему агенту"""
        try:
            task_type = task.get("type")
            
            # Определяем подходящий тип агента
            agent_mapping = {
                "text_generation": "llm_agent",
                "image_analysis": "vision_agent", 
                "image_generation": "image_gen_agent",
                "speech_synthesis": "tts_agent",
                "speech_recognition": "stt_agent"
            }
            
            target_agent = agent_mapping.get(task_type)
            
            if target_agent and target_agent in self.registered_agents:
                # Отправляем задачу агенту
                await self.send_message(
                    target_agent,
                    "task",
                    task
                )
                logger.info(f"Задача {task.get('id')} назначена агенту {target_agent}")
            else:
                logger.warning(f"Не найден подходящий агент для задачи типа {task_type}")
                
        except Exception as e:
            logger.error(f"Ошибка назначения задачи: {e}")

    async def _update_system_stats(self):
        """Обновление статистики системы"""
        try:
            self.system_stats.update({
                "total_agents": len(self.registered_agents),
                "active_agents": len([a for a in self.registered_agents.values() if a.get("status") == "running"]),
                "failed_agents": len([a for a in self.registered_agents.values() if a.get("status") == "error"]),
                "last_update": datetime.now().isoformat()
            })
            
            # Сохраняем статистику в Redis
            await asyncio.to_thread(
                self.redis_client.setex,
                "system_stats",
                300,  # TTL 5 минут
                json.dumps(self.system_stats)
            )
            
        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")

    async def process_message(self, message: AgentMessage) -> Dict[str, any]:
        """Обработка входящих сообщений"""
        try:
            if message.message_type == "registration":
                # Регистрация нового агента
                agent_info = message.content
                self.registered_agents[message.sender] = agent_info
                logger.info(f"Зарегистрирован новый агент: {message.sender}")
                
                return {"status": "registered", "message": "Агент успешно зарегистрирован"}
                
            elif message.message_type == "task_request":
                # Запрос на выполнение задачи
                task = message.content
                await self._assign_task(task)
                
                return {"status": "assigned", "message": "Задача назначена"}
                
            elif message.message_type == "status_update":
                # Обновление статуса агента
                if message.sender in self.registered_agents:
                    self.registered_agents[message.sender].update(message.content)
                
                return {"status": "updated", "message": "Статус обновлен"}
                
            else:
                logger.warning(f"Неизвестный тип сообщения: {message.message_type}")
                return {"status": "unknown", "message": "Неизвестный тип сообщения"}
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения в MetaAgent: {e}")
            return {"status": "error", "message": str(e)}

    async def get_system_status(self) -> Dict:
        """Получение полного статуса системы"""
        return {
            "meta_agent": {
                "name": self.name,
                "status": self.status,
                "uptime": (datetime.now() - self.system_stats["uptime"]).total_seconds(),
                "last_heartbeat": self.last_heartbeat.isoformat()
            },
            "agents": self.registered_agents,
            "statistics": self.system_stats
        }


if __name__ == "__main__":
    # Запуск MetaAgent
    async def main():
        meta_agent = MetaAgent()
        await meta_agent.run()
    
    asyncio.run(main())



