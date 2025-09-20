"""
WatchdogService - контроль контейнеров и автоматическое восстановление
"""

import asyncio
import logging
import docker
from typing import Dict, Any, List
from datetime import datetime, timedelta


class WatchdogService:
    """Сервис контроля контейнеров"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = docker.from_env()
        self.monitored_containers = [
            "agi_meta_agent",
            "agi_telegram_agent", 
            "agi_image_agent",
            "agi_text_agent",
            "agi_vision_agent",
            "agi_ocr_agent",
            "agi_embedding_agent",
            "agi_recovery_agent",
            "agi_web_ui"
        ]
        self.restart_threshold = config.get('restart_threshold', 3)
        self.check_interval = config.get('check_interval', 30)
        
    async def start_monitoring(self):
        """Запуск мониторинга контейнеров"""
        self.logger.info("Запуск мониторинга контейнеров")
        
        while True:
            try:
                await self._check_containers()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Ошибка мониторинга: {e}")
                await asyncio.sleep(5)
    
    async def _check_containers(self):
        """Проверка состояния контейнеров"""
        try:
            containers = self.client.containers.list(all=True)
            
            for container_name in self.monitored_containers:
                container = None
                for c in containers:
                    if c.name == container_name:
                        container = c
                        break
                
                if container:
                    await self._check_container_health(container)
                else:
                    self.logger.warning(f"Контейнер {container_name} не найден")
                    
        except Exception as e:
            self.logger.error(f"Ошибка проверки контейнеров: {e}")
    
    async def _check_container_health(self, container):
        """Проверка здоровья контейнера"""
        try:
            status = container.status
            
            if status != 'running':
                self.logger.warning(f"Контейнер {container.name} не запущен (статус: {status})")
                
                # Попытка перезапуска
                if status in ['exited', 'dead']:
                    await self._restart_container(container)
                    
        except Exception as e:
            self.logger.error(f"Ошибка проверки контейнера {container.name}: {e}")
    
    async def _restart_container(self, container):
        """Перезапуск контейнера"""
        try:
            self.logger.info(f"Перезапуск контейнера {container.name}")
            
            # Остановка контейнера
            if container.status == 'running':
                container.stop(timeout=10)
            
            # Запуск контейнера
            container.start()
            
            self.logger.info(f"Контейнер {container.name} успешно перезапущен")
            
        except Exception as e:
            self.logger.error(f"Ошибка перезапуска контейнера {container.name}: {e}")


async def main():
    """Основная функция Watchdog"""
    config = {
        'restart_threshold': 3,
        'check_interval': 30
    }
    
    watchdog = WatchdogService(config)
    await watchdog.start_monitoring()


if __name__ == "__main__":
    asyncio.run(main())

