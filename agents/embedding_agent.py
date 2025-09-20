"""
EmbeddingAgent - векторизация текста с помощью SentenceTransformers (CPU-only)
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings as ChromaSettings
from .base_agent import BaseAgent, Task


class EmbeddingAgent(BaseAgent):
    """Агент для создания векторных представлений текста"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("embedding_agent", config)
        self.model_path = config.get('models_path', '/app/models')
        self.chroma_config = config.get('chroma', {})
        self.model: Optional[SentenceTransformer] = None
        self.chroma_client: Optional[chromadb.ClientAPI] = None
        self.collection_name = "agi_embeddings"
        
    async def _initialize_agent(self):
        """Инициализация EmbeddingAgent"""
        self.logger.info("Инициализация EmbeddingAgent")
        
        # Загрузка модели SentenceTransformers
        await self._load_model()
        
        # Подключение к ChromaDB
        await self._connect_chromadb()
        
        self.logger.info("EmbeddingAgent успешно инициализирован")
    
    async def _load_model(self):
        """Загрузка модели SentenceTransformers"""
        try:
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            model_file = os.path.join(self.model_path, "sentence_transformers")
            
            self.logger.info(f"Загрузка SentenceTransformers из {model_file}")
            
            # Загрузка модели
            if os.path.exists(model_file):
                self.model = SentenceTransformer(model_file)
            else:
                self.model = SentenceTransformer(model_name)
                # Сохранение модели для будущего использования
                self.model.save(model_file)
            
            self.logger.info("SentenceTransformers модель загружена успешно")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {e}")
            raise
    
    async def _connect_chromadb(self):
        """Подключение к ChromaDB"""
        try:
            chroma_host = self.chroma_config.get('host', 'chromadb')
            chroma_port = self.chroma_config.get('port', 8000)
            
            self.chroma_client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port
            )
            
            # Создание или получение коллекции
            try:
                self.collection = self.chroma_client.get_collection(
                    name=self.collection_name
                )
                self.logger.info(f"Подключена существующая коллекция {self.collection_name}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                self.logger.info(f"Создана новая коллекция {self.collection_name}")
            
        except Exception as e:
            self.logger.error(f"Ошибка подключения к ChromaDB: {e}")
            # Fallback - локальная ChromaDB
            try:
                self.chroma_client = chromadb.Client(
                    settings=ChromaSettings(
                        persist_directory="/app/data/chroma"
                    )
                )
                self.collection = self.chroma_client.get_or_create_collection(
                    name=self.collection_name
                )
                self.logger.info("Подключена локальная ChromaDB")
            except Exception as e2:
                self.logger.error(f"Критическая ошибка подключения к ChromaDB: {e2}")
                raise
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задач векторизации"""
        if task.task_type == "text_embedding":
            return await self._create_embeddings(task)
        elif task.task_type == "similarity_search":
            return await self._similarity_search(task)
        elif task.task_type == "store_embeddings":
            return await self._store_embeddings(task)
        elif task.task_type == "retrieve_embeddings":
            return await self._retrieve_embeddings(task)
        elif task.task_type == "cluster_texts":
            return await self._cluster_texts(task)
        
        return {"status": "unknown_task_type"}
    
    async def _create_embeddings(self, task: Task) -> Dict[str, Any]:
        """Создание векторных представлений текста"""
        try:
            texts = task.data.get("texts", [])
            if isinstance(texts, str):
                texts = [texts]
            
            if not texts:
                return {"status": "error", "error": "Не указаны тексты для векторизации"}
            
            self.logger.info(f"Создание эмбеддингов для {len(texts)} текстов")
            
            # Создание эмбеддингов
            embeddings = self.model.encode(
                texts,
                convert_to_tensor=False,
                show_progress_bar=True
            )
            
            # Преобразование в список для JSON сериализации
            embeddings_list = embeddings.tolist()
            
            return {
                "status": "success",
                "embeddings": embeddings_list,
                "texts": texts,
                "embedding_dimension": embeddings.shape[1],
                "text_count": len(texts),
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "model": "SentenceTransformers"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка создания эмбеддингов: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _similarity_search(self, task: Task) -> Dict[str, Any]:
        """Поиск похожих текстов"""
        try:
            query_text = task.data.get("query_text", "")
            top_k = task.data.get("top_k", 10)
            filter_metadata = task.data.get("filter", {})
            
            if not query_text:
                return {"status": "error", "error": "Не указан поисковый запрос"}
            
            self.logger.info(f"Поиск похожих текстов для: {query_text[:100]}...")
            
            # Поиск в ChromaDB
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=filter_metadata if filter_metadata else None
            )
            
            # Обработка результатов
            similar_texts = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, distance, metadata) in enumerate(zip(
                    results['documents'][0],
                    results['distances'][0],
                    results['metadatas'][0] or [{}] * len(results['documents'][0])
                )):
                    similar_texts.append({
                        "text": doc,
                        "similarity": 1 - distance,  # Преобразование расстояния в схожесть
                        "distance": distance,
                        "metadata": metadata,
                        "rank": i + 1
                    })
            
            return {
                "status": "success",
                "query": query_text,
                "similar_texts": similar_texts,
                "results_count": len(similar_texts),
                "metadata": {
                    "searched_at": datetime.now().isoformat(),
                    "model": "SentenceTransformers"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска похожих текстов: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _store_embeddings(self, task: Task) -> Dict[str, Any]:
        """Сохранение эмбеддингов в ChromaDB"""
        try:
            texts = task.data.get("texts", [])
            metadatas = task.data.get("metadatas", [])
            ids = task.data.get("ids", [])
            
            if not texts:
                return {"status": "error", "error": "Не указаны тексты для сохранения"}
            
            # Генерация ID если не указаны
            if not ids:
                ids = [f"text_{i}_{datetime.now().timestamp()}" for i in range(len(texts))]
            
            # Подготовка метаданных
            if not metadatas:
                metadatas = [{} for _ in texts]
            elif len(metadatas) != len(texts):
                metadatas = [metadatas[0] if metadatas else {} for _ in texts]
            
            # Добавление временных меток
            for metadata in metadatas:
                metadata["created_at"] = datetime.now().isoformat()
            
            self.logger.info(f"Сохранение {len(texts)} текстов в ChromaDB")
            
            # Сохранение в ChromaDB
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "status": "success",
                "stored_count": len(texts),
                "ids": ids,
                "metadata": {
                    "stored_at": datetime.now().isoformat(),
                    "collection": self.collection_name
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения эмбеддингов: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _retrieve_embeddings(self, task: Task) -> Dict[str, Any]:
        """Получение эмбеддингов из ChromaDB"""
        try:
            ids = task.data.get("ids", [])
            limit = task.data.get("limit", 100)
            offset = task.data.get("offset", 0)
            
            self.logger.info(f"Получение эмбеддингов из ChromaDB")
            
            if ids:
                # Получение по конкретным ID
                results = self.collection.get(ids=ids)
            else:
                # Получение всех с пагинацией
                results = self.collection.get(
                    limit=limit,
                    offset=offset
                )
            
            # Обработка результатов
            retrieved_data = []
            if results['documents']:
                for i, (doc, metadata) in enumerate(zip(
                    results['documents'],
                    results['metadatas'] or [{}] * len(results['documents'])
                )):
                    retrieved_data.append({
                        "id": results['ids'][i],
                        "text": doc,
                        "metadata": metadata
                    })
            
            return {
                "status": "success",
                "retrieved_data": retrieved_data,
                "count": len(retrieved_data),
                "metadata": {
                    "retrieved_at": datetime.now().isoformat(),
                    "collection": self.collection_name
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения эмбеддингов: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _cluster_texts(self, task: Task) -> Dict[str, Any]:
        """Кластеризация текстов"""
        try:
            texts = task.data.get("texts", [])
            num_clusters = task.data.get("num_clusters", 5)
            
            if not texts or len(texts) < 2:
                return {"status": "error", "error": "Недостаточно текстов для кластеризации"}
            
            self.logger.info(f"Кластеризация {len(texts)} текстов на {num_clusters} кластеров")
            
            # Создание эмбеддингов
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            
            # Простая кластеризация K-means
            from sklearn.cluster import KMeans
            
            kmeans = KMeans(n_clusters=num_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Группировка текстов по кластерам
            clusters = {}
            for i, (text, label) in enumerate(zip(texts, cluster_labels)):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append({
                    "text": text,
                    "index": i
                })
            
            # Создание центроидов кластеров
            centroids = kmeans.cluster_centers_
            
            return {
                "status": "success",
                "clusters": clusters,
                "cluster_labels": cluster_labels.tolist(),
                "centroids": centroids.tolist(),
                "num_clusters": num_clusters,
                "text_count": len(texts),
                "metadata": {
                    "clustered_at": datetime.now().isoformat(),
                    "model": "SentenceTransformers + KMeans"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка кластеризации: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _cleanup_agent(self):
        """Очистка ресурсов EmbeddingAgent"""
        if self.model:
            del self.model
        if self.chroma_client:
            # ChromaDB клиент автоматически закрывает соединения
        
        self.logger.info("EmbeddingAgent очищен")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о модели"""
        return {
            "model_name": "SentenceTransformers",
            "model_type": "all-MiniLM-L6-v2",
            "embedding_dimension": 384,
            "loaded": self.model is not None,
            "chromadb_connected": self.chroma_client is not None,
            "collection": self.collection_name
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья агента"""
        try:
            # Проверка ChromaDB
            collection_count = self.collection.count() if self.chroma_client else -1
            
            return {
                "status": "healthy" if self.model is not None else "error",
                "model_loaded": self.model is not None,
                "chromadb_connected": self.chroma_client is not None,
                "collection_count": collection_count,
                "collection_name": self.collection_name
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "model_loaded": self.model is not None,
                "chromadb_connected": False
            }

