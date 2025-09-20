"""
MemoryAgent - агент для работы с векторной памятью и знаниями
Использует ChromaDB для хранения и поиска эмбеддингов
"""

import asyncio
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from .base_agent import BaseAgent, Task


class MemoryRequest(BaseModel):
    """Модель запроса к памяти"""
    content: str
    operation: str  # store, search, delete
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MemoryAgent(BaseAgent):
    """Агент для работы с векторной памятью"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("memory_agent", config)
        
        # Конфигурация ChromaDB
        self.chroma_host = config.get('chroma_host', 'localhost')
        self.chroma_port = config.get('chroma_port', 8000)
        self.memory_path = config.get('memory_path', '/workspace/memory')
        
        # ChromaDB клиент
        self.chroma_client: Optional[chromadb.Client] = None
        self.collection: Optional[chromadb.Collection] = None
        
        # SentenceTransformer для эмбеддингов
        self.embedding_model: Optional[SentenceTransformer] = None
        self.embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
        
        # Статистика
        self.memory_stats = {
            "total_stored": 0,
            "total_searches": 0,
            "successful_searches": 0,
            "failed_operations": 0,
            "collection_size": 0
        }
        
        # FastAPI приложение
        self.app = FastAPI(title="MemoryAgent API", version="3.9")
        self._setup_routes()
        
        self.logger.info("MemoryAgent инициализирован")
    
    def _setup_routes(self):
        """Настройка FastAPI маршрутов"""
        
        @self.app.post("/memory")
        async def memory_operation(request: MemoryRequest):
            """Операции с памятью через HTTP API"""
            try:
                task = Task(
                    id=f"memory_{datetime.now().timestamp()}",
                    agent_name="memory_agent",
                    task_type=f"memory_{request.operation}",
                    data={
                        "content": request.content,
                        "user_id": request.user_id,
                        "metadata": request.metadata
                    }
                )
                
                result = await self.process_task(task)
                return result
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/status")
        async def get_status():
            """Статус агента"""
            return await self.health_check()
        
        @self.app.get("/stats")
        async def get_stats():
            """Статистика памяти"""
            return {
                "stats": self.memory_stats,
                "chroma_connected": self.chroma_client is not None,
                "embedding_model_loaded": self.embedding_model is not None,
                "collection_name": "agi_memory" if self.collection else None
            }
        
        @self.app.post("/process_task")
        async def process_task_endpoint(task_data: Dict[str, Any]):
            """Обработка задачи через HTTP API"""
            try:
                task = Task(
                    id=task_data["id"],
                    agent_name=task_data["agent_name"],
                    task_type=task_data["task_type"],
                    data=task_data["data"]
                )
                
                result = await self.process_task(task)
                return result
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _initialize_agent(self):
        """Инициализация агента памяти"""
        self.logger.info("Инициализация MemoryAgent")
        
        # Инициализация ChromaDB
        await self._init_chromadb()
        
        # Загрузка модели эмбеддингов
        await self._load_embedding_model()
        
        # Запуск HTTP сервера
        asyncio.create_task(self._start_http_server())
        
        self.logger.info("MemoryAgent инициализирован")
    
    async def _start_http_server(self):
        """Запуск HTTP сервера"""
        try:
            config = uvicorn.Config(
                app=self.app,
                host="0.0.0.0",
                port=8005,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            self.logger.error(f"Ошибка запуска HTTP сервера: {e}")
    
    async def _init_chromadb(self):
        """Инициализация ChromaDB"""
        try:
            self.logger.info("Подключение к ChromaDB...")
            
            # Создаем директорию для локального хранения
            os.makedirs(self.memory_path, exist_ok=True)
            
            # Пытаемся подключиться к удаленному ChromaDB
            try:
                self.chroma_client = chromadb.HttpClient(
                    host=self.chroma_host,
                    port=self.chroma_port
                )
                # Проверяем подключение
                self.chroma_client.heartbeat()
                self.logger.info(f"✅ Подключен к ChromaDB: {self.chroma_host}:{self.chroma_port}")
                
            except Exception as e:
                self.logger.warning(f"Не удалось подключиться к удаленному ChromaDB: {e}")
                # Используем локальную версию
                self.chroma_client = chromadb.PersistentClient(
                    path=self.memory_path,
                    settings=Settings(anonymized_telemetry=False)
                )
                self.logger.info(f"✅ Используем локальный ChromaDB: {self.memory_path}")
            
            # Создаем или получаем коллекцию
            try:
                self.collection = self.chroma_client.get_collection("agi_memory")
                self.logger.info("Коллекция 'agi_memory' найдена")
            except Exception:
                self.collection = self.chroma_client.create_collection(
                    name="agi_memory",
                    metadata={"description": "AGI Layer v3.9 Memory Collection"}
                )
                self.logger.info("Коллекция 'agi_memory' создана")
            
            # Обновляем статистику
            try:
                count = self.collection.count()
                self.memory_stats["collection_size"] = count
                self.logger.info(f"Размер коллекции: {count} записей")
            except Exception as e:
                self.logger.warning(f"Не удалось получить размер коллекции: {e}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации ChromaDB: {e}")
            # Создаем заглушку
            self.chroma_client = "fallback"
            self.collection = "fallback"
    
    async def _load_embedding_model(self):
        """Загрузка модели для создания эмбеддингов"""
        try:
            self.logger.info("Загрузка модели эмбеддингов...")
            
            model_cache_path = os.path.join('/workspace/models', 'sentence_transformer')
            
            if os.path.exists(model_cache_path):
                self.logger.info(f"Загрузка модели из кеша: {model_cache_path}")
                self.embedding_model = SentenceTransformer(model_cache_path)
            else:
                self.logger.info(f"Загрузка модели из HuggingFace: {self.embedding_model_name}")
                self.embedding_model = SentenceTransformer(
                    self.embedding_model_name,
                    cache_folder='/workspace/models'
                )
                # Сохраняем локально
                os.makedirs(model_cache_path, exist_ok=True)
                self.embedding_model.save(model_cache_path)
            
            self.logger.info("✅ Модель эмбеддингов загружена")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели эмбеддингов: {e}")
            self.embedding_model = "fallback"
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задач памяти"""
        try:
            if task.task_type == "memory_store":
                return await self._store_memory(task)
            elif task.task_type == "memory_search":
                return await self._search_memory(task)
            elif task.task_type == "memory_delete":
                return await self._delete_memory(task)
            elif task.task_type == "memory_retrieve":
                return await self._retrieve_memory(task)
            elif task.task_type == "ping":
                return {"status": "success", "message": "pong"}
            else:
                return {"status": "error", "error": f"Неизвестный тип задачи: {task.task_type}"}
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки задачи: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _store_memory(self, task: Task) -> Dict[str, Any]:
        """Сохранение информации в память"""
        try:
            data = task.data
            content = data.get("content", "")
            user_id = data.get("user_id", "system")
            metadata = data.get("metadata", {})
            
            if not content:
                return {"status": "error", "error": "Пустое содержимое для сохранения"}
            
            self.logger.info(f"Сохранение в память: {content[:100]}...")
            
            if self.collection == "fallback" or self.embedding_model == "fallback":
                return await self._store_memory_fallback(content, user_id, metadata)
            
            # Создаем эмбеддинг
            embedding = self.embedding_model.encode([content])[0].tolist()
            
            # Генерируем уникальный ID
            memory_id = str(uuid.uuid4())
            
            # Подготавливаем метаданные
            full_metadata = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "content_length": len(content),
                **metadata
            }
            
            # Сохраняем в ChromaDB
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[full_metadata],
                ids=[memory_id]
            )
            
            self.memory_stats["total_stored"] += 1
            self.memory_stats["collection_size"] = self.collection.count()
            
            self.logger.info(f"✅ Память сохранена с ID: {memory_id}")
            
            return {
                "status": "success",
                "memory_id": memory_id,
                "content": content,
                "metadata": full_metadata,
                "message": "Информация сохранена в память"
            }
            
        except Exception as e:
            self.memory_stats["failed_operations"] += 1
            self.logger.error(f"Ошибка сохранения в память: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _search_memory(self, task: Task) -> Dict[str, Any]:
        """Поиск информации в памяти"""
        try:
            data = task.data
            query = data.get("content", data.get("query", ""))
            user_id = data.get("user_id", "system")
            limit = data.get("limit", 5)
            
            if not query:
                return {"status": "error", "error": "Пустой поисковый запрос"}
            
            self.memory_stats["total_searches"] += 1
            self.logger.info(f"Поиск в памяти: {query}")
            
            if self.collection == "fallback" or self.embedding_model == "fallback":
                return await self._search_memory_fallback(query, user_id)
            
            # Создаем эмбеддинг запроса
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            # Поиск в ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where={"user_id": user_id} if user_id != "system" else None
            )
            
            if not results['documents'][0]:
                return {
                    "status": "success",
                    "query": query,
                    "results": [],
                    "total_found": 0,
                    "message": "Информация не найдена"
                }
            
            # Форматируем результаты
            formatted_results = []
            for i, doc in enumerate(results['documents'][0]):
                result_item = {
                    "content": doc,
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i],
                    "id": results['ids'][0][i]
                }
                formatted_results.append(result_item)
            
            self.memory_stats["successful_searches"] += 1
            
            # Создаем ответ на основе найденной информации
            response = self._generate_search_response(query, formatted_results)
            
            self.logger.info(f"✅ Найдено {len(formatted_results)} результатов")
            
            return {
                "status": "success",
                "query": query,
                "response": response,
                "results": formatted_results,
                "total_found": len(formatted_results)
            }
            
        except Exception as e:
            self.memory_stats["failed_operations"] += 1
            self.logger.error(f"Ошибка поиска в памяти: {e}")
            return {"status": "error", "error": str(e)}
    
    def _generate_search_response(self, query: str, results: List[Dict]) -> str:
        """Генерация ответа на основе найденной информации"""
        if not results:
            return "К сожалению, информация по вашему запросу не найдена."
        
        # Берем наиболее релевантный результат
        best_result = results[0]
        content = best_result['content']
        
        # Простая генерация ответа
        if len(results) == 1:
            response = f"По вашему запросу найдена следующая информация: {content}"
        else:
            response = f"По вашему запросу найдено {len(results)} результатов. Наиболее релевантный: {content}"
            
            if len(results) > 1:
                response += f"\n\nДругие результаты:"
                for i, result in enumerate(results[1:3], 1):  # Показываем еще 2 результата
                    response += f"\n{i+1}. {result['content'][:100]}..."
        
        return response
    
    async def _delete_memory(self, task: Task) -> Dict[str, Any]:
        """Удаление информации из памяти"""
        try:
            data = task.data
            memory_id = data.get("memory_id")
            query = data.get("content", data.get("query", ""))
            
            if self.collection == "fallback":
                return {"status": "success", "message": "Удаление в режиме заглушки"}
            
            if memory_id:
                # Удаление по ID
                self.collection.delete(ids=[memory_id])
                message = f"Память с ID {memory_id} удалена"
            elif query:
                # Поиск и удаление по содержимому
                search_results = await self._search_memory(task)
                if search_results["status"] == "success" and search_results["results"]:
                    ids_to_delete = [result["id"] for result in search_results["results"]]
                    self.collection.delete(ids=ids_to_delete)
                    message = f"Удалено {len(ids_to_delete)} записей по запросу"
                else:
                    return {"status": "error", "error": "Записи для удаления не найдены"}
            else:
                return {"status": "error", "error": "Не указан ID или запрос для удаления"}
            
            self.memory_stats["collection_size"] = self.collection.count()
            
            return {
                "status": "success",
                "message": message
            }
            
        except Exception as e:
            self.memory_stats["failed_operations"] += 1
            self.logger.error(f"Ошибка удаления из памяти: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _retrieve_memory(self, task: Task) -> Dict[str, Any]:
        """Получение всех записей пользователя"""
        try:
            data = task.data
            user_id = data.get("user_id", "system")
            limit = data.get("limit", 50)
            
            if self.collection == "fallback":
                return {"status": "success", "memories": [], "total": 0}
            
            # Получаем записи пользователя
            results = self.collection.get(
                where={"user_id": user_id} if user_id != "system" else None,
                limit=limit
            )
            
            memories = []
            for i, doc in enumerate(results['documents']):
                memory = {
                    "id": results['ids'][i],
                    "content": doc,
                    "metadata": results['metadatas'][i]
                }
                memories.append(memory)
            
            return {
                "status": "success",
                "memories": memories,
                "total": len(memories),
                "user_id": user_id
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения памяти: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _store_memory_fallback(self, content: str, user_id: str, metadata: Dict) -> Dict[str, Any]:
        """Заглушка для сохранения памяти"""
        memory_id = str(uuid.uuid4())
        
        # Сохраняем в файл как fallback
        fallback_file = os.path.join(self.memory_path, "fallback_memory.json")
        
        try:
            if os.path.exists(fallback_file):
                with open(fallback_file, 'r', encoding='utf-8') as f:
                    memories = json.load(f)
            else:
                memories = []
            
            memory_entry = {
                "id": memory_id,
                "content": content,
                "user_id": user_id,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat()
            }
            
            memories.append(memory_entry)
            
            with open(fallback_file, 'w', encoding='utf-8') as f:
                json.dump(memories, f, ensure_ascii=False, indent=2)
            
            return {
                "status": "success",
                "memory_id": memory_id,
                "content": content,
                "message": "Информация сохранена (режим заглушки)"
            }
            
        except Exception as e:
            return {"status": "error", "error": f"Ошибка fallback сохранения: {str(e)}"}
    
    async def _search_memory_fallback(self, query: str, user_id: str) -> Dict[str, Any]:
        """Заглушка для поиска в памяти"""
        fallback_file = os.path.join(self.memory_path, "fallback_memory.json")
        
        try:
            if not os.path.exists(fallback_file):
                return {
                    "status": "success",
                    "query": query,
                    "response": "Память пуста (режим заглушки)",
                    "results": [],
                    "total_found": 0
                }
            
            with open(fallback_file, 'r', encoding='utf-8') as f:
                memories = json.load(f)
            
            # Простой поиск по ключевым словам
            query_words = query.lower().split()
            matching_memories = []
            
            for memory in memories:
                if user_id != "system" and memory.get("user_id") != user_id:
                    continue
                
                content_lower = memory["content"].lower()
                if any(word in content_lower for word in query_words):
                    matching_memories.append({
                        "content": memory["content"],
                        "metadata": memory["metadata"],
                        "id": memory["id"],
                        "distance": 0.5  # Фиктивная дистанция
                    })
            
            if matching_memories:
                response = f"Найдена информация: {matching_memories[0]['content']}"
            else:
                response = "Информация по запросу не найдена"
            
            return {
                "status": "success",
                "query": query,
                "response": response,
                "results": matching_memories[:5],
                "total_found": len(matching_memories)
            }
            
        except Exception as e:
            return {"status": "error", "error": f"Ошибка fallback поиска: {str(e)}"}
    
    async def _get_metrics(self) -> Dict[str, Any]:
        """Получение метрик агента"""
        base_metrics = await super()._get_metrics()
        
        base_metrics.update({
            "chroma_connected": self.chroma_client is not None and self.chroma_client != "fallback",
            "embedding_model_loaded": self.embedding_model is not None and self.embedding_model != "fallback",
            "memory_stats": self.memory_stats,
            "chroma_host": self.chroma_host,
            "chroma_port": self.chroma_port
        })
        
        return base_metrics
    
    async def _cleanup_agent(self):
        """Очистка ресурсов"""
        self.logger.info("Очистка ресурсов MemoryAgent")
        
        if self.embedding_model and self.embedding_model != "fallback":
            del self.embedding_model


# Функция запуска
async def run_memory_agent(config: Dict[str, Any]):
    """Запуск агента памяти"""
    agent = MemoryAgent(config)
    await agent.initialize()
    await agent.start()
    
    try:
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
        'chroma_host': os.getenv('CHROMA_HOST', 'localhost'),
        'chroma_port': int(os.getenv('CHROMA_PORT', 8000)),
        'memory_path': '/workspace/memory',
        'postgres_host': os.getenv('POSTGRES_HOST', 'localhost'),
        'postgres_port': int(os.getenv('POSTGRES_PORT', 5432)),
        'postgres_db': os.getenv('POSTGRES_DB', 'agi_layer'),
        'postgres_user': os.getenv('POSTGRES_USER', 'agi_user'),
        'postgres_password': os.getenv('POSTGRES_PASSWORD', 'agi_password')
    }
    
    asyncio.run(run_memory_agent(config))