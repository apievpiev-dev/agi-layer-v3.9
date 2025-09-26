#!/usr/bin/env python3
"""
Простой API для тестирования AGI Layer v3.9
==========================================

Быстрый FastAPI сервер для связи Web UI с Ollama моделями
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime
from typing import Dict, Optional, Any

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    prompt: str
    model: str = "llama3.2:3b"
    max_tokens: int = 512


class GenerateResponse(BaseModel):
    generated_text: str
    model: str
    timestamp: str
    tokens_generated: int


# Создаем FastAPI приложение
app = FastAPI(
    title="AGI Layer v3.9 Test API",
    description="Простой API для тестирования нейросетей",
    version="3.9.0"
)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "AGI Layer v3.9 Test API",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья системы"""
    try:
        # Проверяем Ollama по HTTP
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        models: list[str] = []
        if resp.ok:
            data = resp.json()
            # формат: {"models": [{"name": "llama3.2:3b", ...}, ...]}
            models = [m.get("name") for m in data.get("models", []) if m.get("name")]
            return {
                "status": "healthy",
                "ollama": "healthy",
                "available_models": models,
                "timestamp": datetime.now().isoformat()
            }
        return {"status": "error", "error": "ollama http error", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}


@app.get("/models")
async def list_models():
    """Список доступных моделей"""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        if not resp.ok:
            raise HTTPException(status_code=500, detail="Ollama недоступен")
        data = resp.json()
        models = [{"name": m.get("name", ""), "modified": m.get("modified_at", ""), "size": m.get("size", 0)} for m in data.get("models", [])]
        return {"models": models, "total": len(models), "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения моделей: {str(e)}")


@app.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """Генерация текста через Ollama"""
    try:
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": False,
            "options": {"num_predict": request.max_tokens}
        }
        resp = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=180)
        if not resp.ok:
            raise HTTPException(status_code=500, detail=f"HTTP {resp.status_code}: {resp.text}")
        data = resp.json()
        generated_text = data.get("response", "").strip()
        return GenerateResponse(
            generated_text=generated_text,
            model=request.model,
            timestamp=datetime.now().isoformat(),
            tokens_generated=len(generated_text.split())
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")


@app.get("/status")
async def system_status():
    """Статус всей системы"""
    try:
        # Проверяем Docker контейнеры
        docker_result = subprocess.run(
            ["docker-compose", "ps", "--format", "json"], 
            cwd="/root/agi-layer-v3.9",
            capture_output=True, 
            text=True
        )
        
        containers = []
        if docker_result.returncode == 0:
            try:
                # Парсим JSON вывод
                for line in docker_result.stdout.strip().split('\n'):
                    if line.strip():
                        container = json.loads(line)
                        containers.append({
                            "name": container.get("Name", "unknown"),
                            "state": container.get("State", "unknown"),
                            "status": container.get("Status", "unknown")
                        })
            except:
                # Fallback если JSON парсинг не работает
                pass
        
        # Проверяем Ollama модели
        ollama_result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        ollama_models = []
        if ollama_result.returncode == 0:
            lines = ollama_result.stdout.strip().split('\n')[1:]
            ollama_models = [line.split()[0] for line in lines if line.strip()]
        
        return {
            "meta_agent": {
                "status": "running" if containers else "starting",
                "uptime": 600  # 10 минут примерно
            },
            "agents": {
                "llm_agent": {
                    "status": "running" if ollama_models else "starting",
                    "available_models": ollama_models,
                    "memory_usage": 2048,  # MB
                    "error_count": 0
                }
            },
            "statistics": {
                "total_agents": len(containers),
                "active_agents": len([c for c in containers if c.get("state") == "Up"]),
                "failed_agents": len([c for c in containers if c.get("state") != "Up"]),
                "total_models": len(ollama_models)
            },
            "containers": containers,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


class ImageGenerateRequest(BaseModel):
    """Запрос генерации изображения"""
    prompt: str
    width: int = 512
    height: int = 512
    num_images: int = 1


@app.post("/generate/image")
async def generate_image(request: ImageGenerateRequest):
    """Генерация изображения через ImageGenAgent (через Redis очередь)"""
    try:
        import redis, json, time
        task_id = f"img_{int(time.time()*1000)}"

        # Отправляем задачу в очередь image_gen_agent
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)
        task_payload = {
            "id": task_id,
            "prompt": request.prompt,
            "width": request.width,
            "height": request.height,
            "num_images": request.num_images,
        }
        r.lpush("tasks_image_gen_agent", json.dumps(task_payload))

        # Ждем результата с таймаутом
        deadline = time.time() + 180  # до 3 минут на CPU
        result_key = f"results_{task_id}"
        result = None
        while time.time() < deadline:
            data = r.lpop(result_key)
            if data:
                result = json.loads(data)
                break
            time.sleep(1)

        if not result:
            raise HTTPException(status_code=504, detail="Таймаут генерации изображения")

        if result.get("status") != "completed":
            raise HTTPException(status_code=500, detail=result.get("message", "Ошибка генерации"))

        # Вернем только превью первой картинки
        first = None
        images = result.get("images")
        if isinstance(images, list) and images:
            first = images[0].get("data")

        return {
            "status": "completed",
            "prompt": request.prompt,
            "width": request.width,
            "height": request.height,
            "image_base64": first,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации изображения: {str(e)}")


@app.get("/models/test")
async def test_all_models():
    """Тестирование всех доступных моделей"""
    try:
        results = {}
        
        # Тестируем Ollama модели
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        if resp.ok:
            data = resp.json()
            ollama_models = [m.get("name") for m in data.get("models", []) if m.get("name")]
            
            for model in ollama_models:
                try:
                    # Быстрый тест каждой модели
                    test_prompt = "Скажи привет"
                    payload = {"model": model, "prompt": test_prompt, "stream": False, "options": {"num_predict": 32}}
                    resp = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=60)
                    if resp.ok:
                        response = resp.json().get("response", "")[:100] + "..."
                        results[model] = {
                            "status": "working",
                            "test_response": response,
                            "response_time": "<30s"
                        }
                    else:
                        results[model] = {
                            "status": "error",
                            "error": resp.text
                        }
                        
                except Exception as e:
                    results[model] = {
                        "status": "error",
                        "error": str(e)
                    }
        
        return {
            "total_models_tested": len(results),
            "working_models": len([r for r in results.values() if r["status"] == "working"]),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка тестирования: {str(e)}")


class MemoryStoreRequest(BaseModel):
    content: str
    metadata: Dict[str, Any] | None = None


class MemorySearchRequest(BaseModel):
    query: str
    n_results: int = 5


@app.post("/memory/store")
async def memory_store(req: MemoryStoreRequest):
    try:
        import redis, json, time
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)
        task_id = f"mem_store_{int(time.time()*1000)}"
        payload = {"id": task_id, "content": req.content, "metadata": req.metadata or {}}
        r.lpush("tasks_memory_agent", json.dumps({"type": "store_memory", **payload}))
        deadline = time.time() + 30
        result_key = f"results_{task_id}"
        result = None
        while time.time() < deadline:
            data = r.lpop(result_key)
            if data:
                result = json.loads(data)
                break
            time.sleep(0.5)
        if not result:
            raise HTTPException(status_code=504, detail="Таймаут сохранения памяти")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/search")
async def memory_search(req: MemorySearchRequest):
    try:
        import redis, json, time
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)
        task_id = f"mem_search_{int(time.time()*1000)}"
        payload = {"id": task_id, "query": req.query, "n_results": req.n_results}
        r.lpush("tasks_memory_agent", json.dumps({"type": "retrieve_memory", **payload}))
        deadline = time.time() + 30
        result_key = f"results_{task_id}"
        result = None
        while time.time() < deadline:
            data = r.lpop(result_key)
            if data:
                result = json.loads(data)
                break
            time.sleep(0.5)
        if not result:
            raise HTTPException(status_code=504, detail="Таймаут поиска памяти")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("🚀 Запуск AGI Layer v3.9 Test API")
    print("📡 API будет доступен на: http://0.0.0.0:8080")
    print("📖 Документация: http://0.0.0.0:8080/docs")
    print("🧪 Тестирование моделей: http://0.0.0.0:8080/models/test")
    
    uvicorn.run(
        "test_api:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )



