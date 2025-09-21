"""
Веб-чат с Ollama и памятью - улучшенная версия с сохранением истории
"""

import asyncio
import logging
import json
import aiohttp
import uuid
from typing import Dict, Any, List, AsyncGenerator, Optional
from datetime import datetime
import os
import asyncpg
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn


class ChatMemory:
    """Класс для управления памятью чата"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db_pool = None
        self.chroma_client = None
        self.embedding_model = None
        self.collection = None
        
    async def initialize(self):
        """Инициализация памяти"""
        try:
            # Подключение к PostgreSQL
            self.db_pool = await asyncpg.create_pool(
                host=self.config['postgres']['host'],
                port=self.config['postgres']['port'],
                database=self.config['postgres']['database'],
                user=self.config['postgres']['user'],
                password=self.config['postgres']['password'],
                min_size=2,
                max_size=10
            )
            
            # Подключение к ChromaDB
            self.chroma_client = chromadb.HttpClient(
                host=self.config['chroma']['host'],
                port=self.config['chroma']['port']
            )
            
            # Инициализация модели для эмбеддингов
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Создание/получение коллекции
            try:
                self.collection = self.chroma_client.get_collection("chat_memory")
            except:
                self.collection = self.chroma_client.create_collection("chat_memory")
            
            # Создание таблиц в PostgreSQL
            await self._create_tables()
            
            self.logger.info("Память чата инициализирована")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации памяти: {e}")
            raise
    
    async def _create_tables(self):
        """Создание таблиц в базе данных"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_embeddings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    message_id UUID REFERENCES chat_messages(id) ON DELETE CASCADE,
                    embedding_id VARCHAR(255) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    async def create_session(self, name: str = None) -> str:
        """Создание новой сессии чата"""
        session_name = name or f"Чат {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        async with self.db_pool.acquire() as conn:
            session_id = await conn.fetchval(
                "INSERT INTO chat_sessions (name) VALUES ($1) RETURNING id",
                session_name
            )
        
        return str(session_id)
    
    async def get_sessions(self) -> List[Dict[str, Any]]:
        """Получение списка сессий"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, name, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC"
            )
            return [dict(row) for row in rows]
    
    async def get_session_messages(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение сообщений сессии"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT role, content, metadata, created_at 
                FROM chat_messages 
                WHERE session_id = $1 
                ORDER BY created_at ASC 
                LIMIT $2
                """,
                session_id, limit
            )
            return [dict(row) for row in rows]
    
    async def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None) -> str:
        """Добавление сообщения в сессию"""
        async with self.db_pool.acquire() as conn:
            message_id = await conn.fetchval(
                """
                INSERT INTO chat_messages (session_id, role, content, metadata) 
                VALUES ($1, $2, $3, $4) 
                RETURNING id
                """,
                session_id, role, content, json.dumps(metadata or {})
            )
            
            # Обновление времени последнего обновления сессии
            await conn.execute(
                "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = $1",
                session_id
            )
        
        # Добавление в векторную память (только для сообщений пользователя)
        if role == "user":
            await self._add_to_vector_memory(str(message_id), content)
        
        return str(message_id)
    
    async def _add_to_vector_memory(self, message_id: str, content: str):
        """Добавление сообщения в векторную память"""
        try:
            # Генерация эмбеддинга
            embedding = self.embedding_model.encode(content).tolist()
            
            # Добавление в ChromaDB
            embedding_id = f"msg_{message_id}_{datetime.now().timestamp()}"
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[{"message_id": message_id, "type": "user_message"}],
                ids=[embedding_id]
            )
            
            # Сохранение связи в PostgreSQL
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO chat_embeddings (message_id, embedding_id) VALUES ($1, $2)",
                    message_id, embedding_id
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка добавления в векторную память: {e}")
    
    async def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Поиск в памяти по смыслу"""
        try:
            # Генерация эмбеддинга запроса
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Поиск в ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit
            )
            
            relevant_messages = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    relevant_messages.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0
                    })
            
            return relevant_messages
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска в памяти: {e}")
            return []
    
    async def get_context_for_session(self, session_id: str, query: str = None) -> List[Dict[str, str]]:
        """Получение контекста для сессии"""
        # Получаем последние сообщения сессии
        recent_messages = await self.get_session_messages(session_id, limit=10)
        
        context = []
        for msg in recent_messages[-10:]:  # Последние 10 сообщений
            context.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Если есть запрос, добавляем релевантную информацию из памяти
        if query:
            relevant_memories = await self.search_memory(query, limit=3)
            for memory in relevant_memories:
                if memory['distance'] < 0.8:  # Только релевантные результаты
                    context.append({
                        "role": "system",
                        "content": f"[Релевантная информация из памяти]: {memory['content']}"
                    })
        
        return context
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.db_pool:
            await self.db_pool.close()


class OllamaChatWithMemory:
    """Веб-чат с Ollama и памятью"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.http_session = None
        self.ollama_host = config.get('ollama_host', 'localhost')
        self.ollama_port = config.get('ollama_port', 11434)
        self.ollama_base_url = f"http://{self.ollama_host}:{self.ollama_port}"
        self.app = FastAPI(title="Ollama Chat with Memory", version="1.0.0")
        self.connected_clients: List[WebSocket] = []
        self.memory = ChatMemory(config)
        
        # Настройка маршрутов
        self._setup_routes()
    
    def _setup_routes(self):
        """Настройка маршрутов FastAPI"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def chat_page(request: Request):
            """Главная страница чата с памятью"""
            return self._get_chat_html()
        
        @self.app.get("/api/sessions")
        async def get_sessions():
            """Получение списка сессий"""
            try:
                sessions = await self.memory.get_sessions()
                return {"sessions": sessions}
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={"error": str(e)}
                )
        
        @self.app.post("/api/sessions")
        async def create_session(request: Request):
            """Создание новой сессии"""
            try:
                data = await request.json()
                name = data.get("name")
                session_id = await self.memory.create_session(name)
                return {"session_id": session_id}
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={"error": str(e)}
                )
        
        @self.app.get("/api/sessions/{session_id}/messages")
        async def get_session_messages(session_id: str):
            """Получение сообщений сессии"""
            try:
                messages = await self.memory.get_session_messages(session_id)
                return {"messages": messages}
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={"error": str(e)}
                )
        
        @self.app.get("/api/models")
        async def get_models():
            """Получение списка доступных моделей"""
            try:
                models = await self._get_available_models()
                return {"models": models}
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={"error": str(e)}
                )
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket для потокового чата с памятью"""
            await websocket.accept()
            self.connected_clients.append(websocket)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    message_type = message_data.get("type", "chat")
                    
                    if message_type == "chat":
                        await self._handle_chat_message(websocket, message_data)
                    elif message_type == "load_session":
                        await self._handle_load_session(websocket, message_data)
                    elif message_type == "search_memory":
                        await self._handle_search_memory(websocket, message_data)
                        
            except WebSocketDisconnect:
                self.connected_clients.remove(websocket)
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": str(e)
                }))
    
    async def _handle_chat_message(self, websocket: WebSocket, message_data: Dict):
        """Обработка сообщения чата"""
        try:
            message = message_data.get("message", "")
            model = message_data.get("model", "llama2")
            session_id = message_data.get("session_id")
            
            if not message or not session_id:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": "Недостаточно данных для обработки"
                }))
                return
            
            # Добавление сообщения пользователя в память
            await self.memory.add_message(session_id, "user", message)
            
            # Отправка сообщения пользователя обратно
            await websocket.send_text(json.dumps({
                "type": "user_message",
                "content": message
            }))
            
            # Получение контекста для ответа
            context = await self.memory.get_context_for_session(session_id, message)
            
            # Генерация и отправка ответа по частям
            await websocket.send_text(json.dumps({
                "type": "assistant_start"
            }))
            
            full_response = ""
            async for chunk in self._generate_response_with_context(context, message, model):
                full_response += chunk
                await websocket.send_text(json.dumps({
                    "type": "assistant_chunk",
                    "content": chunk
                }))
            
            # Сохранение ответа ассистента в память
            await self.memory.add_message(session_id, "assistant", full_response)
            
            await websocket.send_text(json.dumps({
                "type": "assistant_end",
                "full_content": full_response
            }))
            
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": str(e)
            }))
    
    async def _handle_load_session(self, websocket: WebSocket, message_data: Dict):
        """Загрузка сессии"""
        try:
            session_id = message_data.get("session_id")
            messages = await self.memory.get_session_messages(session_id)
            
            await websocket.send_text(json.dumps({
                "type": "session_loaded",
                "messages": messages
            }))
            
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": str(e)
            }))
    
    async def _handle_search_memory(self, websocket: WebSocket, message_data: Dict):
        """Поиск в памяти"""
        try:
            query = message_data.get("query", "")
            results = await self.memory.search_memory(query, limit=5)
            
            await websocket.send_text(json.dumps({
                "type": "memory_search_results",
                "results": results
            }))
            
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": str(e)
            }))
    
    async def _generate_response_with_context(self, context: List[Dict], prompt: str, model: str) -> AsyncGenerator[str, None]:
        """Генерация ответа с контекстом"""
        try:
            # Подготовка сообщений с контекстом
            messages = []
            
            # Системный промпт
            system_prompt = """Ты полезный AI-ассистент с памятью. Ты можешь помнить предыдущие разговоры и использовать эту информацию для более точных ответов. 
            Отвечай на русском языке, если вопрос задан на русском. Используй контекст из предыдущих сообщений для более релевантных ответов."""
            messages.append({"role": "system", "content": system_prompt})
            
            # Добавление контекста
            messages.extend(context)
            
            # Добавление текущего сообщения
            messages.append({"role": "user", "content": prompt})
            
            # Подготовка запроса
            request_data = {
                "model": model,
                "messages": messages,
                "stream": True
            }
            
            # Отправка запроса
            async with self.http_session.post(
                f"{self.ollama_base_url}/api/chat",
                json=request_data
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line:
                            try:
                                data = json.loads(line)
                                if 'message' in data and 'content' in data['message']:
                                    yield data['message']['content']
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    yield f"Ошибка API: {response.status} - {error_text}"
                    
        except Exception as e:
            yield f"Ошибка генерации: {e}"
    
    async def _get_available_models(self) -> List[str]:
        """Получение списка доступных моделей"""
        try:
            async with self.http_session.get(f"{self.ollama_base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    return models
                else:
                    return []
        except Exception as e:
            self.logger.error(f"Ошибка получения моделей: {e}")
            return []
    
    def _get_chat_html(self) -> str:
        """Генерация HTML для чата с памятью"""
        return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ollama Chat with Memory - AGI Layer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .chat-container {
            width: 95%;
            max-width: 1200px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            display: flex;
            overflow: hidden;
        }
        
        .sidebar {
            width: 300px;
            background: #f8f9fa;
            border-right: 1px solid #e9ecef;
            display: flex;
            flex-direction: column;
        }
        
        .sidebar-header {
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .sidebar-header h2 {
            font-size: 18px;
            margin-bottom: 10px;
        }
        
        .new-session-btn {
            width: 100%;
            padding: 10px;
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            margin-bottom: 10px;
        }
        
        .new-session-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .sessions-list {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }
        
        .session-item {
            padding: 12px;
            margin-bottom: 8px;
            background: white;
            border-radius: 8px;
            cursor: pointer;
            border: 2px solid transparent;
            transition: all 0.3s;
        }
        
        .session-item:hover {
            border-color: #667eea;
        }
        
        .session-item.active {
            border-color: #667eea;
            background: #f0f4ff;
        }
        
        .session-name {
            font-weight: 500;
            margin-bottom: 4px;
        }
        
        .session-date {
            font-size: 12px;
            color: #666;
        }
        
        .main-chat {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-title {
            font-size: 20px;
            font-weight: 600;
        }
        
        .model-selector {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .model-selector select {
            padding: 8px 12px;
            border: none;
            border-radius: 8px;
            background: rgba(255,255,255,0.2);
            color: white;
            font-size: 14px;
        }
        
        .model-selector select option {
            background: #667eea;
            color: white;
        }
        
        .status {
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            background: rgba(255,255,255,0.2);
        }
        
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 20px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }
        
        .message.user {
            flex-direction: row-reverse;
        }
        
        .message-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: bold;
            flex-shrink: 0;
        }
        
        .message.user .message-avatar {
            background: #667eea;
            color: white;
        }
        
        .message.assistant .message-avatar {
            background: #28a745;
            color: white;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
            white-space: pre-wrap;
        }
        
        .message.user .message-content {
            background: #667eea;
            color: white;
        }
        
        .message.assistant .message-content {
            background: white;
            border: 1px solid #e9ecef;
            color: #333;
        }
        
        .typing-indicator {
            display: none;
            align-items: center;
            gap: 8px;
            color: #666;
            font-style: italic;
            margin: 10px 0;
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #667eea;
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes typing {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        
        .chat-input {
            padding: 20px;
            background: white;
            border-top: 1px solid #e9ecef;
        }
        
        .input-container {
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }
        
        .input-field {
            flex: 1;
            min-height: 50px;
            max-height: 120px;
            padding: 12px 16px;
            border: 2px solid #e9ecef;
            border-radius: 25px;
            resize: none;
            font-family: inherit;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .input-field:focus {
            border-color: #667eea;
        }
        
        .send-button {
            width: 50px;
            height: 50px;
            border: none;
            border-radius: 50%;
            background: #667eea;
            color: white;
            font-size: 18px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .send-button:hover {
            background: #5a6fd8;
            transform: scale(1.05);
        }
        
        .send-button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .memory-search {
            padding: 10px;
            border-top: 1px solid #e9ecef;
            background: #f8f9fa;
        }
        
        .memory-search input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 12px;
        }
        
        .memory-results {
            max-height: 150px;
            overflow-y: auto;
            margin-top: 10px;
        }
        
        .memory-result {
            padding: 8px;
            margin-bottom: 4px;
            background: white;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            border: 1px solid transparent;
        }
        
        .memory-result:hover {
            border-color: #667eea;
        }
        
        @media (max-width: 768px) {
            .chat-container {
                width: 100%;
                height: 100vh;
                border-radius: 0;
            }
            
            .sidebar {
                width: 250px;
            }
            
            .message-content {
                max-width: 85%;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="sidebar">
            <div class="sidebar-header">
                <h2>🧠 Память чата</h2>
                <button class="new-session-btn" onclick="createNewSession()">+ Новый чат</button>
            </div>
            
            <div class="sessions-list" id="sessionsList">
                <!-- Список сессий будет загружен здесь -->
            </div>
            
            <div class="memory-search">
                <input type="text" id="memorySearch" placeholder="Поиск в памяти..." onkeyup="searchMemory(event)">
                <div class="memory-results" id="memoryResults"></div>
            </div>
        </div>
        
        <div class="main-chat">
            <div class="chat-header">
                <div class="chat-title" id="currentSessionTitle">Выберите чат</div>
                <div class="model-selector">
                    <label for="modelSelect">Модель:</label>
                    <select id="modelSelect">
                        <option value="llama2">Llama2</option>
                    </select>
                </div>
                <div class="status" id="status">Подключение...</div>
            </div>
            
            <div class="chat-messages" id="messages">
                <div class="message assistant">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        Привет! Я AI-ассистент с памятью. Я помню наши предыдущие разговоры и могу использовать эту информацию для более точных ответов. Создайте новый чат или выберите существующий из списка слева.
                    </div>
                </div>
            </div>
            
            <div class="typing-indicator" id="typing">
                <div class="message-avatar">🤖</div>
                <div>Ассистент печатает<span class="typing-dots">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </span></div>
            </div>
            
            <div class="chat-input">
                <div class="input-container">
                    <textarea 
                        id="messageInput" 
                        class="input-field" 
                        placeholder="Введите ваше сообщение..."
                        rows="1"
                        disabled
                    ></textarea>
                    <button id="sendButton" class="send-button" onclick="sendMessage()" disabled>➤</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let currentModel = 'llama2';
        let currentSessionId = null;
        let sessions = [];
        
        // Инициализация WebSocket
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onopen = function() {
                document.getElementById('status').textContent = 'Подключено';
                document.getElementById('status').style.background = 'rgba(40, 167, 69, 0.3)';
                loadSessions();
                loadModels();
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };
            
            ws.onclose = function() {
                document.getElementById('status').textContent = 'Отключено';
                document.getElementById('status').style.background = 'rgba(220, 53, 69, 0.3)';
                setTimeout(initWebSocket, 3000);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
                document.getElementById('status').textContent = 'Ошибка';
                document.getElementById('status').style.background = 'rgba(220, 53, 69, 0.3)';
            };
        }
        
        // Обработка сообщений WebSocket
        function handleWebSocketMessage(data) {
            switch(data.type) {
                case 'user_message':
                    addMessage('user', data.content);
                    break;
                case 'assistant_start':
                    showTyping();
                    break;
                case 'assistant_chunk':
                    updateLastAssistantMessage(data.content);
                    break;
                case 'assistant_end':
                    hideTyping();
                    finalizeLastAssistantMessage(data.full_content);
                    break;
                case 'session_loaded':
                    loadSessionMessages(data.messages);
                    break;
                case 'memory_search_results':
                    displayMemoryResults(data.results);
                    break;
                case 'error':
                    hideTyping();
                    addError(data.content);
                    break;
            }
        }
        
        // Загрузка сессий
        async function loadSessions() {
            try {
                const response = await fetch('/api/sessions');
                const data = await response.json();
                sessions = data.sessions;
                displaySessions();
            } catch (error) {
                console.error('Ошибка загрузки сессий:', error);
            }
        }
        
        // Отображение сессий
        function displaySessions() {
            const container = document.getElementById('sessionsList');
            container.innerHTML = '';
            
            sessions.forEach(session => {
                const div = document.createElement('div');
                div.className = 'session-item';
                if (session.id === currentSessionId) {
                    div.classList.add('active');
                }
                
                div.innerHTML = `
                    <div class="session-name">${escapeHtml(session.name)}</div>
                    <div class="session-date">${new Date(session.created_at).toLocaleDateString()}</div>
                `;
                
                div.onclick = () => loadSession(session.id, session.name);
                container.appendChild(div);
            });
        }
        
        // Загрузка сессии
        function loadSession(sessionId, sessionName) {
            currentSessionId = sessionId;
            document.getElementById('currentSessionTitle').textContent = sessionName;
            document.getElementById('messageInput').disabled = false;
            document.getElementById('sendButton').disabled = false;
            
            // Отправка запроса на загрузку сессии
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'load_session',
                    session_id: sessionId
                }));
            }
            
            displaySessions();
        }
        
        // Загрузка сообщений сессии
        function loadSessionMessages(messages) {
            const container = document.getElementById('messages');
            container.innerHTML = '';
            
            messages.forEach(msg => {
                addMessage(msg.role, msg.content, false);
            });
            
            container.scrollTop = container.scrollHeight;
        }
        
        // Создание новой сессии
        async function createNewSession() {
            const name = prompt('Введите название нового чата:') || `Чат ${new Date().toLocaleString()}`;
            
            try {
                const response = await fetch('/api/sessions', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name})
                });
                const data = await response.json();
                
                await loadSessions();
                loadSession(data.session_id, name);
            } catch (error) {
                console.error('Ошибка создания сессии:', error);
                alert('Ошибка создания новой сессии');
            }
        }
        
        // Поиск в памяти
        function searchMemory(event) {
            if (event.key === 'Enter') {
                const query = event.target.value.trim();
                if (query && ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'search_memory',
                        query: query
                    }));
                }
            }
        }
        
        // Отображение результатов поиска в памяти
        function displayMemoryResults(results) {
            const container = document.getElementById('memoryResults');
            container.innerHTML = '';
            
            results.forEach(result => {
                const div = document.createElement('div');
                div.className = 'memory-result';
                div.textContent = result.content.substring(0, 100) + '...';
                container.appendChild(div);
            });
        }
        
        // Отправка сообщения
        function sendMessage() {
            if (!currentSessionId) {
                alert('Сначала создайте или выберите чат');
                return;
            }
            
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !ws || ws.readyState !== WebSocket.OPEN) return;
            
            ws.send(JSON.stringify({
                type: 'chat',
                message: message,
                model: currentModel,
                session_id: currentSessionId
            }));
            
            input.value = '';
            input.style.height = 'auto';
        }
        
        // Добавление сообщения в чат
        function addMessage(role, content, scroll = true) {
            const messagesContainer = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            const avatar = role === 'user' ? '👤' : '🤖';
            
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">${escapeHtml(content)}</div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            if (scroll) {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }
        
        // Обновление последнего сообщения ассистента (для потокового вывода)
        function updateLastAssistantMessage(chunk) {
            let lastMessage = document.querySelector('.message.assistant:last-child .message-content');
            if (!lastMessage || lastMessage.dataset.streaming !== 'true') {
                const messagesContainer = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message assistant';
                messageDiv.innerHTML = `
                    <div class="message-avatar">🤖</div>
                    <div class="message-content" data-streaming="true">${escapeHtml(chunk)}</div>
                `;
                messagesContainer.appendChild(messageDiv);
                lastMessage = messageDiv.querySelector('.message-content');
            } else {
                lastMessage.textContent += chunk;
            }
            
            document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        }
        
        // Финальное оформление сообщения ассистента
        function finalizeLastAssistantMessage(fullContent) {
            let lastMessage = document.querySelector('.message.assistant:last-child .message-content');
            if (lastMessage) {
                lastMessage.textContent = fullContent;
                delete lastMessage.dataset.streaming;
            }
        }
        
        // Показать индикатор печати
        function showTyping() {
            document.getElementById('typing').style.display = 'flex';
            document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        }
        
        // Скрыть индикатор печати
        function hideTyping() {
            document.getElementById('typing').style.display = 'none';
        }
        
        // Добавление ошибки
        function addError(message) {
            const messagesContainer = document.getElementById('messages');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.textContent = message;
            messagesContainer.appendChild(errorDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        // Загрузка доступных моделей
        async function loadModels() {
            try {
                const response = await fetch('/api/models');
                const data = await response.json();
                
                if (data.models && data.models.length > 0) {
                    const select = document.getElementById('modelSelect');
                    select.innerHTML = '';
                    
                    data.models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model;
                        option.textContent = model;
                        select.appendChild(option);
                    });
                    
                    currentModel = data.models[0];
                }
            } catch (error) {
                console.error('Ошибка загрузки моделей:', error);
            }
        }
        
        // Экранирование HTML
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Обработка Enter в поле ввода
        document.getElementById('messageInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Автоматическое изменение высоты поля ввода
        document.getElementById('messageInput').addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
        
        // Изменение модели
        document.getElementById('modelSelect').addEventListener('change', function() {
            currentModel = this.value;
        });
        
        // Инициализация при загрузке страницы
        document.addEventListener('DOMContentLoaded', function() {
            initWebSocket();
        });
    </script>
</body>
</html>
        """
    
    async def initialize(self):
        """Инициализация"""
        self.http_session = aiohttp.ClientSession()
        await self.memory.initialize()
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.http_session:
            await self.http_session.close()
        await self.memory.cleanup()
    
    def run(self, host: str = "0.0.0.0", port: int = 8503):
        """Запуск сервера"""
        uvicorn.run(self.app, host=host, port=port)


async def main():
    """Основная функция"""
    config = {
        'ollama_host': os.getenv('OLLAMA_HOST', 'localhost'),
        'ollama_port': int(os.getenv('OLLAMA_PORT', 11434)),
        'postgres': {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'agi_layer'),
            'user': os.getenv('POSTGRES_USER', 'agi_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'agi_password')
        },
        'chroma': {
            'host': os.getenv('CHROMA_HOST', 'localhost'),
            'port': int(os.getenv('CHROMA_PORT', 8000))
        }
    }
    
    chat_ui = OllamaChatWithMemory(config)
    
    try:
        await chat_ui.initialize()
        chat_ui.run(host="0.0.0.0", port=8503)
    finally:
        await chat_ui.cleanup()


if __name__ == "__main__":
    asyncio.run(main())