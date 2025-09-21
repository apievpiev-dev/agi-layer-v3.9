"""
Простой веб-интерфейс для чата с Ollama на FastAPI
"""

import asyncio
import logging
import json
import aiohttp
from typing import Dict, Any, List, AsyncGenerator
from datetime import datetime
import os
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn


class OllamaWebChat:
    """Веб-интерфейс для чата с Ollama на FastAPI"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.http_session = None
        self.ollama_host = config.get('ollama_host', 'localhost')
        self.ollama_port = config.get('ollama_port', 11434)
        self.ollama_base_url = f"http://{self.ollama_host}:{self.ollama_port}"
        self.app = FastAPI(title="Ollama Chat", version="1.0.0")
        self.connected_clients: List[WebSocket] = []
        
        # Настройка маршрутов
        self._setup_routes()
    
    def _setup_routes(self):
        """Настройка маршрутов FastAPI"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def chat_page(request: Request):
            """Главная страница чата"""
            return self._get_chat_html()
        
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
        
        @self.app.post("/api/chat")
        async def chat_endpoint(request: Request):
            """Эндпоинт для чата"""
            try:
                data = await request.json()
                message = data.get("message", "")
                model = data.get("model", "llama2")
                
                if not message:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Сообщение не может быть пустым"}
                    )
                
                response = await self._generate_single_response(message, model)
                return {"response": response}
                
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={"error": str(e)}
                )
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket для потокового чата"""
            await websocket.accept()
            self.connected_clients.append(websocket)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    message = message_data.get("message", "")
                    model = message_data.get("model", "llama2")
                    
                    if message:
                        # Отправка сообщения пользователя обратно
                        await websocket.send_text(json.dumps({
                            "type": "user_message",
                            "content": message
                        }))
                        
                        # Генерация и отправка ответа по частям
                        await websocket.send_text(json.dumps({
                            "type": "assistant_start"
                        }))
                        
                        full_response = ""
                        async for chunk in self._generate_response(message, model):
                            full_response += chunk
                            await websocket.send_text(json.dumps({
                                "type": "assistant_chunk",
                                "content": chunk
                            }))
                        
                        await websocket.send_text(json.dumps({
                            "type": "assistant_end",
                            "full_content": full_response
                        }))
                        
            except WebSocketDisconnect:
                self.connected_clients.remove(websocket)
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": str(e)
                }))
    
    def _get_chat_html(self) -> str:
        """Генерация HTML для чата"""
        return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ollama Chat - AGI Layer</title>
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
            width: 90%;
            max-width: 800px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            position: relative;
        }
        
        .chat-header h1 {
            font-size: 24px;
            margin-bottom: 10px;
        }
        
        .model-selector {
            display: flex;
            align-items: center;
            gap: 10px;
            justify-content: center;
            margin-top: 10px;
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
            position: absolute;
            top: 20px;
            right: 20px;
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
        
        .clear-button {
            background: #dc3545;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 15px;
            cursor: pointer;
            font-size: 12px;
            margin-left: 10px;
        }
        
        .clear-button:hover {
            background: #c82333;
        }
        
        @media (max-width: 600px) {
            .chat-container {
                width: 100%;
                height: 100vh;
                border-radius: 0;
            }
            
            .message-content {
                max-width: 85%;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🤖 Ollama Chat</h1>
            <div class="model-selector">
                <label for="modelSelect">Модель:</label>
                <select id="modelSelect">
                    <option value="llama2">Llama2</option>
                </select>
                <button class="clear-button" onclick="clearChat()">Очистить</button>
            </div>
            <div class="status" id="status">Подключение...</div>
        </div>
        
        <div class="chat-messages" id="messages">
            <div class="message assistant">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    Привет! Я AI-ассистент, работающий через Ollama. Чем могу помочь?
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
                ></textarea>
                <button id="sendButton" class="send-button" onclick="sendMessage()">➤</button>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let currentModel = 'llama2';
        
        // Инициализация WebSocket
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onopen = function() {
                document.getElementById('status').textContent = 'Подключено';
                document.getElementById('status').style.background = 'rgba(40, 167, 69, 0.3)';
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };
            
            ws.onclose = function() {
                document.getElementById('status').textContent = 'Отключено';
                document.getElementById('status').style.background = 'rgba(220, 53, 69, 0.3)';
                // Переподключение через 3 секунды
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
                case 'error':
                    hideTyping();
                    addError(data.content);
                    break;
            }
        }
        
        // Отправка сообщения
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !ws || ws.readyState !== WebSocket.OPEN) return;
            
            // Отправка через WebSocket
            ws.send(JSON.stringify({
                message: message,
                model: currentModel
            }));
            
            input.value = '';
            input.style.height = 'auto';
        }
        
        // Добавление сообщения в чат
        function addMessage(role, content) {
            const messagesContainer = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            const avatar = role === 'user' ? '👤' : '🤖';
            
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">${escapeHtml(content)}</div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        // Обновление последнего сообщения ассистента (для потокового вывода)
        function updateLastAssistantMessage(chunk) {
            let lastMessage = document.querySelector('.message.assistant:last-child .message-content');
            if (!lastMessage || lastMessage.dataset.streaming !== 'true') {
                // Создаем новое сообщение
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
        
        // Очистка чата
        function clearChat() {
            const messagesContainer = document.getElementById('messages');
            messagesContainer.innerHTML = `
                <div class="message assistant">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        Чат очищен. Чем могу помочь?
                    </div>
                </div>
            `;
        }
        
        // Экранирование HTML
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
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
            loadModels();
            initWebSocket();
        });
    </script>
</body>
</html>
        """
    
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
    
    async def _generate_single_response(self, prompt: str, model: str) -> str:
        """Генерация одного ответа"""
        try:
            messages = [
                {"role": "system", "content": "Ты полезный AI-ассистент. Отвечай на русском языке, если вопрос задан на русском."},
                {"role": "user", "content": prompt}
            ]
            
            request_data = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            async with self.http_session.post(
                f"{self.ollama_base_url}/api/chat",
                json=request_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('message', {}).get('content', 'Ошибка генерации ответа')
                else:
                    return f"Ошибка API: {response.status}"
                    
        except Exception as e:
            return f"Ошибка генерации: {e}"
    
    async def _generate_response(self, prompt: str, model: str) -> AsyncGenerator[str, None]:
        """Генерация потокового ответа"""
        try:
            messages = [
                {"role": "system", "content": "Ты полезный AI-ассистент. Отвечай на русском языке, если вопрос задан на русском."},
                {"role": "user", "content": prompt}
            ]
            
            request_data = {
                "model": model,
                "messages": messages,
                "stream": True
            }
            
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
    
    async def initialize(self):
        """Инициализация"""
        self.http_session = aiohttp.ClientSession()
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.http_session:
            await self.http_session.close()
    
    def run(self, host: str = "0.0.0.0", port: int = 8502):
        """Запуск сервера"""
        uvicorn.run(self.app, host=host, port=port)


async def main():
    """Основная функция"""
    config = {
        'ollama_host': os.getenv('OLLAMA_HOST', 'localhost'),
        'ollama_port': int(os.getenv('OLLAMA_PORT', 11434))
    }
    
    chat_ui = OllamaWebChat(config)
    
    try:
        await chat_ui.initialize()
        chat_ui.run(host="0.0.0.0", port=8502)
    finally:
        await chat_ui.cleanup()


if __name__ == "__main__":
    asyncio.run(main())