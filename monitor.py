#!/usr/bin/env python3
"""
AGI Layer v3.9 - Монитор системы
===============================

Непрерывный мониторинг всех компонентов:
- Статус моделей и агентов
- Использование ресурсов
- Производительность
- Автоматические алерты
"""

import asyncio
import json
import psutil
import subprocess
import time
from datetime import datetime
from typing import Dict

import requests


class AGIMonitor:
    """Система мониторинга AGI Layer v3.9"""
    
    def __init__(self):
        self.monitoring = True
        self.stats_history = []
        self.alert_thresholds = {
            "cpu_percent": 90,
            "memory_percent": 90,
            "disk_percent": 95,
            "response_time": 30  # секунд
        }

    async def start_monitoring(self):
        """Запуск непрерывного мониторинга"""
        print("🔍 Запуск мониторинга AGI Layer v3.9")
        print("Нажмите Ctrl+C для остановки")
        print("-" * 50)
        
        try:
            while self.monitoring:
                stats = await self.collect_stats()
                await self.display_stats(stats)
                await self.check_alerts(stats)
                
                # Сохраняем историю (последние 100 записей)
                self.stats_history.append(stats)
                if len(self.stats_history) > 100:
                    self.stats_history.pop(0)
                
                await asyncio.sleep(5)  # Обновление каждые 5 секунд
                
        except KeyboardInterrupt:
            print("\n⏹️ Мониторинг остановлен")
            await self.save_report()

    async def collect_stats(self) -> Dict:
        """Сбор статистики системы"""
        try:
            # Системные ресурсы
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Ollama модели
            ollama_models = await self.check_ollama_models()
            
            # Docker контейнеры
            docker_status = await self.check_docker_status()
            
            # API статус
            api_status = await self.check_api_status()
            
            # Web UI статус
            webui_status = await self.check_webui_status()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": memory.used / (1024**3),
                    "memory_total_gb": memory.total / (1024**3),
                    "disk_percent": (disk.used / disk.total) * 100,
                    "disk_used_gb": disk.used / (1024**3),
                    "disk_free_gb": disk.free / (1024**3)
                },
                "ollama": ollama_models,
                "docker": docker_status,
                "api": api_status,
                "webui": webui_status
            }
            
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    async def check_ollama_models(self) -> Dict:
        """Проверка статуса Ollama моделей"""
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]
                models = []
                
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            models.append({
                                "name": parts[0],
                                "size": parts[2],
                                "modified": " ".join(parts[3:]) if len(parts) > 3 else ""
                            })
                
                return {
                    "status": "healthy",
                    "models": models,
                    "total_models": len(models)
                }
            else:
                return {"status": "error", "error": "Ollama недоступен"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def check_docker_status(self) -> Dict:
        """Проверка статуса Docker контейнеров"""
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "table"],
                cwd="/root/agi-layer-v3.9",
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок
                
                containers = []
                for line in lines:
                    if line.strip():
                        # Простой парсинг статуса
                        if "Up" in line:
                            containers.append({"status": "running"})
                        else:
                            containers.append({"status": "stopped"})
                
                running_count = len([c for c in containers if c["status"] == "running"])
                
                return {
                    "status": "healthy" if running_count > 0 else "error",
                    "total_containers": len(containers),
                    "running_containers": running_count
                }
            else:
                return {"status": "error", "error": "Docker недоступен"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def check_api_status(self) -> Dict:
        """Проверка статуса API"""
        try:
            start_time = time.time()
            response = requests.get("http://localhost:8080/health", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time": round(response_time, 3),
                    "port": 8080
                }
            else:
                return {"status": "error", "http_code": response.status_code}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def check_webui_status(self) -> Dict:
        """Проверка статуса Web UI"""
        try:
            start_time = time.time()
            response = requests.get("http://localhost:8501", timeout=5)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time": round(response_time, 3),
                    "port": 8501
                }
            else:
                return {"status": "error", "http_code": response.status_code}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def display_stats(self, stats: Dict):
        """Отображение статистики в реальном времени"""
        # Очищаем экран
        print("\033[2J\033[H")
        
        print("🤖 AGI Layer v3.9 - Мониторинг")
        print(f"📅 {stats.get('timestamp', 'N/A')}")
        print("=" * 60)
        
        if "error" in stats:
            print(f"❌ Ошибка сбора статистики: {stats['error']}")
            return
        
        # Системные ресурсы
        system = stats.get("system", {})
        print(f"💻 СИСТЕМА:")
        print(f"   CPU: {system.get('cpu_percent', 0):.1f}%")
        print(f"   RAM: {system.get('memory_percent', 0):.1f}% ({system.get('memory_used_gb', 0):.1f}GB / {system.get('memory_total_gb', 0):.1f}GB)")
        print(f"   ДИСК: {system.get('disk_percent', 0):.1f}% (свободно: {system.get('disk_free_gb', 0):.0f}GB)")
        
        # Ollama модели
        ollama = stats.get("ollama", {})
        ollama_status = "✅" if ollama.get("status") == "healthy" else "❌"
        print(f"\n🧠 OLLAMA: {ollama_status}")
        if ollama.get("models"):
            for model in ollama["models"]:
                print(f"   • {model['name']} ({model['size']})")
        
        # Docker контейнеры
        docker = stats.get("docker", {})
        docker_status = "✅" if docker.get("status") == "healthy" else "❌"
        print(f"\n🐳 DOCKER: {docker_status}")
        print(f"   Контейнеров: {docker.get('running_containers', 0)}/{docker.get('total_containers', 0)}")
        
        # API и Web UI
        api = stats.get("api", {})
        api_status = "✅" if api.get("status") == "healthy" else "❌"
        print(f"\n📡 API: {api_status} ({api.get('response_time', 0):.3f}с)")
        
        webui = stats.get("webui", {})
        webui_status = "✅" if webui.get("status") == "healthy" else "❌"
        print(f"🌐 WEB UI: {webui_status} ({webui.get('response_time', 0):.3f}с)")

    async def check_alerts(self, stats: Dict):
        """Проверка алертов"""
        if "system" not in stats:
            return
        
        system = stats["system"]
        alerts = []
        
        # Проверяем пороги
        if system.get("cpu_percent", 0) > self.alert_thresholds["cpu_percent"]:
            alerts.append(f"🔥 Высокая загрузка CPU: {system['cpu_percent']:.1f}%")
        
        if system.get("memory_percent", 0) > self.alert_thresholds["memory_percent"]:
            alerts.append(f"💾 Высокое использование RAM: {system['memory_percent']:.1f}%")
        
        if system.get("disk_percent", 0) > self.alert_thresholds["disk_percent"]:
            alerts.append(f"💿 Мало места на диске: {system['disk_percent']:.1f}%")
        
        # Проверяем время ответа API
        api_time = stats.get("api", {}).get("response_time", 0)
        if api_time > self.alert_thresholds["response_time"]:
            alerts.append(f"⏰ Медленный API: {api_time:.1f}с")
        
        # Выводим алерты
        if alerts:
            print("\n🚨 АЛЕРТЫ:")
            for alert in alerts:
                print(f"   {alert}")

    async def save_report(self):
        """Сохранение итогового отчета"""
        try:
            if self.stats_history:
                report = {
                    "monitoring_session": {
                        "start_time": self.stats_history[0]["timestamp"],
                        "end_time": self.stats_history[-1]["timestamp"],
                        "total_records": len(self.stats_history)
                    },
                    "final_stats": self.stats_history[-1],
                    "history": self.stats_history
                }
                
                filename = f"/root/agi-layer-v3.9/monitoring_report_{int(time.time())}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                
                print(f"📋 Отчет мониторинга сохранен: {filename}")
                
        except Exception as e:
            print(f"❌ Ошибка сохранения отчета: {e}")


async def main():
    """Главная функция мониторинга"""
    monitor = AGIMonitor()
    await monitor.start_monitoring()


if __name__ == "__main__":
    asyncio.run(main())




