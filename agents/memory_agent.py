"""
MemoryAgent - Агент управления памятью
====================================

Управляет долгосрочной памятью через ChromaDB:
- Векторное хранение диалогов
- Поиск по контексту
- RAG (Retrieval-Augmented Generation)
- Анализ и архивирование памяти
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import chromadb
from loguru import logger
from sentence_transformers import SentenceTransformer

from base_agent import BaseAgent, AgentConfig, AgentMessage


class MemoryAgent(BaseAgent):
    """Агент для управления памятью системы"""
    
    def __init__(self):
        config = AgentConfig(
            name="memory_agent",
            type="memory_management",
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            max_memory="4G",
            max_cpu_cores=2
        )
        super().__init__(config)
        
        # ChromaDB клиент
        self.chroma_client = None
        self.collection = None
        
        # Sentence Transformer для embeddings
        self.embedding_model = None
        
        # Настройки памяти
        self.collection_name = "agi_memory"
        self.max_memory_items = 10000
        self.memory_retention_days = 30

    async def _load_model(self):
        """Загрузка модели для создания embeddings"""
        try:
            logger.info("Загрузка модели для embeddings...")
            
            def load_embedding_model():
                return SentenceTransformer(
                    "sentence-transformers/all-MiniLM-L6-v2",
                    cache_folder="/app/models/cache"
                )
            
            self.embedding_model = await asyncio.to_thread(load_embedding_model)
            
            logger.info("✅ Модель embeddings загружена")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели embeddings: {e}")
            raise

    async def _agent_specific_init(self):
        """Специфичная инициализация MemoryAgent"""
        try:
            # Подключаемся к ChromaDB
            chroma_url = os.getenv("CHROMA_URL", "http://localhost:8000")
            self.chroma_client = chromadb.HttpClient(host="localhost", port=8000)
            
            # Создаем или получаем коллекцию
            try:
                self.collection = self.chroma_client.get_collection(self.collection_name)
                logger.info(f"Подключен к существующей коллекции {self.collection_name}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "AGI Layer v3.9 долгосрочная память"}
                )
                logger.info(f"Создана новая коллекция {self.collection_name}")
            
            # Регистрируемся в MetaAgent
            await self.send_message(
                "meta_agent",
                "registration",
                {
                    "agent_type": self.type,
                    "capabilities": [
                        "long_term_memory",
                        "context_search",
                        "conversation_history",
                        "knowledge_retrieval"
                    ],
                    "collection_name": self.collection_name,
                    "status": "ready"
                }
            )
            
            logger.info("MemoryAgent зарегистрирован в MetaAgent")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации MemoryAgent: {e}")
            raise

    async def _agent_main_loop(self):
        """Основной цикл MemoryAgent"""
        while self.is_running:
            try:
                # Проверяем задачи в очереди
                task_data = await asyncio.to_thread(
                    self.redis_client.lpop, f"tasks_{self.name}"
                )
                
                if task_data:
                    task = json.loads(task_data)
                    await self._process_memory_task(task)
                
                # Периодическая очистка старой памяти
                await self._cleanup_old_memories()
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Ошибка в главном цикле MemoryAgent: {e}")
                await asyncio.sleep(10)

    async def _process_memory_task(self, task: Dict):
        """Обработка задач с памятью"""
        try:
            task_type = task.get("type", "store")
            
            if task_type == "store":
                await self._store_memory(task)
            elif task_type == "search":
                await self._search_memory(task)
            elif task_type == "context":
                await self._get_context(task)
            
        except Exception as e:
            logger.error(f"Ошибка обработки задачи памяти: {e}")

    async def _store_memory(self, task: Dict):
        """Сохранение в долгосрочную память"""
        try:
            content = task.get("content", "")
            metadata = task.get("metadata", {})
            memory_id = str(uuid.uuid4())
            
            # Создаем embedding
            def create_embedding():
                return self.embedding_model.encode([content])[0].tolist()
            
            embedding = await asyncio.to_thread(create_embedding)
            
            # Добавляем метаданные
            metadata.update({
                "timestamp": datetime.now().isoformat(),
                "agent": task.get("agent", "unknown"),
                "type": task.get("memory_type", "conversation")
            })
            
            # Сохраняем в ChromaDB
            def store_in_chroma():
                self.collection.add(
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[metadata],
                    ids=[memory_id]
                )
            
            await asyncio.to_thread(store_in_chroma)
            
            logger.info(f"Память сохранена: {memory_id}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения памяти: {e}")

    async def _search_memory(self, task: Dict) -> List[Dict]:
        """Поиск в долгосрочной памяти"""
        try:
            query = task.get("query", "")
            limit = task.get("limit", 5)
            
            # Создаем embedding для запроса
            def create_query_embedding():
                return self.embedding_model.encode([query])[0].tolist()
            
            query_embedding = await asyncio.to_thread(create_query_embedding)
            
            # Ищем в ChromaDB
            def search_in_chroma():
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    include=["documents", "metadatas", "distances"]
                )
                return results
            
            results = await asyncio.to_thread(search_in_chroma)
            
            # Форматируем результаты
            memories = []
            for i, doc in enumerate(results["documents"][0]):
                memories.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i],
                    "similarity": 1 - results["distances"][0][i],  # Преобразуем distance в similarity
                    "id": results["ids"][0][i] if "ids" in results else f"result_{i}"
                })
            
            return memories
            
        except Exception as e:
            logger.error(f"Ошибка поиска в памяти: {e}")
            return []

    async def _get_context(self, task: Dict) -> str:
        """Получение контекста для генерации"""
        try:
            query = task.get("query", "")
            context_length = task.get("context_length", 1000)
            
            # Ищем релевантные воспоминания
            memories = await self._search_memory({
                "query": query,
                "limit": 3
            })
            
            # Составляем контекст
            context_parts = []
            for memory in memories:
                if memory["similarity"] > 0.7:  # Только высокая релевантность
                    context_parts.append(memory["content"])
            
            context = "\n".join(context_parts)
            
            # Обрезаем если слишком длинный
            if len(context) > context_length:
                context = context[:context_length] + "..."
            
            return context
            
        except Exception as e:
            logger.error(f"Ошибка получения контекста: {e}")
            return ""

    async def _cleanup_old_memories(self):
        """Очистка старых воспоминаний"""
        try:
            # Выполняем раз в час
            current_time = datetime.now()
            last_cleanup = await self.get_memory("last_cleanup", "short_term")
            
            if last_cleanup:
                last_cleanup_time = datetime.fromisoformat(last_cleanup)
                if (current_time - last_cleanup_time).seconds < 3600:  # 1 час
                    return
            
            # Удаляем записи старше retention_days
            cutoff_date = current_time - timedelta(days=self.memory_retention_days)
            
            def cleanup_old():
                # Получаем все записи
                all_results = self.collection.get(include=["metadatas"])
                
                ids_to_delete = []
                for i, metadata in enumerate(all_results["metadatas"]):
                    timestamp_str = metadata.get("timestamp", "")
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                            if timestamp < cutoff_date:
                                ids_to_delete.append(all_results["ids"][i])
                        except:
                            continue
                
                # Удаляем старые записи
                if ids_to_delete:
                    self.collection.delete(ids=ids_to_delete)
                    return len(ids_to_delete)
                
                return 0
            
            deleted_count = await asyncio.to_thread(cleanup_old)
            
            if deleted_count > 0:
                logger.info(f"Очищено {deleted_count} старых воспоминаний")
            
            # Сохраняем время последней очистки
            await self.save_memory("last_cleanup", current_time.isoformat())
            
        except Exception as e:
            logger.error(f"Ошибка очистки памяти: {e}")

    async def process_message(self, message: AgentMessage) -> Dict[str, any]:
        """Обработка входящих сообщений"""
        try:
            if message.message_type == "store":
                content = message.content.get("content", "")
                metadata = message.content.get("metadata", {})
                
                await self._store_memory({
                    "content": content,
                    "metadata": metadata,
                    "agent": message.sender
                })
                
                return {"status": "stored", "message": "Память сохранена"}
                
            elif message.message_type == "search":
                query = message.content.get("query", "")
                limit = message.content.get("limit", 5)
                
                memories = await self._search_memory({
                    "query": query,
                    "limit": limit
                })
                
                return {
                    "status": "completed",
                    "results": memories,
                    "total_found": len(memories)
                }
                
            elif message.message_type == "context":
                query = message.content.get("query", "")
                context = await self._get_context({"query": query})
                
                return {
                    "status": "completed",
                    "context": context,
                    "context_length": len(context)
                }
                
            elif message.message_type == "status":
                # Получаем статистику коллекции
                def get_stats():
                    try:
                        count = self.collection.count()
                        return count
                    except:
                        return 0
                
                memory_count = await asyncio.to_thread(get_stats)
                
                return {
                    "agent_name": self.name,
                    "status": self.status,
                    "memory_items": memory_count,
                    "max_capacity": self.max_memory_items,
                    "retention_days": self.memory_retention_days,
                    "model": "sentence-transformers/all-MiniLM-L6-v2"
                }
                
            else:
                return {"status": "unknown", "message": "Неизвестный тип сообщения"}
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения в MemoryAgent: {e}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # Запуск MemoryAgent
    async def main():
        memory_agent = MemoryAgent()
        await memory_agent.run()
    
    asyncio.run(main())
