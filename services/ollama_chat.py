"""
Ollama Chat Service - веб-интерфейс для чата с Ollama
"""

import asyncio
import aiohttp
import logging
import json
from typing import Dict, Any, List, Optional
import streamlit as st
from datetime import datetime


class OllamaChatService:
    """Сервис для взаимодействия с Ollama"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.logger = logging.getLogger(__name__)
        self.http_session = None
        
    async def initialize(self):
        """Инициализация HTTP сессии"""
        self.http_session = aiohttp.ClientSession()
        
    async def get_models(self) -> List[Dict[str, Any]]:
        """Получение списка доступных моделей"""
        try:
            async with self.http_session.get(f"{self.ollama_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('models', [])
                else:
                    self.logger.error(f"Ошибка получения моделей: {response.status}")
                    return []
        except Exception as e:
            self.logger.error(f"Ошибка подключения к Ollama: {e}")
            return []
    
    async def generate_response(self, model: str, prompt: str, context: List[str] = None) -> str:
        """Генерация ответа от модели"""
        try:
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "context": context or []
            }
            
            async with self.http_session.post(
                f"{self.ollama_url}/api/generate", 
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', '')
                else:
                    error_text = await response.text()
                    self.logger.error(f"Ошибка генерации: {response.status} - {error_text}")
                    return f"Ошибка: {response.status}"
                    
        except Exception as e:
            self.logger.error(f"Ошибка генерации ответа: {e}")
            return f"Ошибка подключения: {e}"
    
    async def stream_response(self, model: str, prompt: str, context: List[str] = None):
        """Потоковая генерация ответа"""
        try:
            data = {
                "model": model,
                "prompt": prompt,
                "stream": True,
                "context": context or []
            }
            
            async with self.http_session.post(
                f"{self.ollama_url}/api/generate", 
                json=data
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                if 'response' in chunk:
                                    yield chunk['response']
                                if chunk.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    yield f"Ошибка: {response.status} - {error_text}"
                    
        except Exception as e:
            self.logger.error(f"Ошибка потоковой генерации: {e}")
            yield f"Ошибка подключения: {e}"
    
    async def check_ollama_status(self) -> bool:
        """Проверка статуса Ollama сервера"""
        try:
            async with self.http_session.get(f"{self.ollama_url}/api/tags") as response:
                return response.status == 200
        except:
            return False


class OllamaChatUI:
    """Веб-интерфейс для чата с Ollama"""
    
    def __init__(self, ollama_service: OllamaChatService):
        self.ollama_service = ollama_service
        
    async def render_chat_page(self):
        """Отрисовка страницы чата"""
        st.header("🤖 Чат с Ollama")
        
        # Проверка статуса Ollama
        ollama_status = await self.ollama_service.check_ollama_status()
        
        if not ollama_status:
            st.error("❌ Ollama сервер недоступен. Убедитесь, что Ollama запущен на localhost:11434")
            st.info("Для запуска Ollama используйте команду: `ollama serve`")
            return
        
        st.success("✅ Ollama сервер подключен")
        
        # Получение доступных моделей
        models = await self.ollama_service.get_models()
        
        if not models:
            st.warning("⚠️ Нет доступных моделей. Загрузите модель командой: `ollama pull llama2`")
            return
        
        # Настройки чата
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Выбор модели
            model_names = [model['name'] for model in models]
            selected_model = st.selectbox(
                "Выберите модель:",
                model_names,
                help="Выберите модель для чата"
            )
        
        with col2:
            # Кнопка очистки чата
            if st.button("🗑️ Очистить чат", use_container_width=True):
                st.session_state.ollama_chat_history = []
                st.session_state.ollama_context = []
                st.rerun()
        
        # История чата
        if 'ollama_chat_history' not in st.session_state:
            st.session_state.ollama_chat_history = []
        
        if 'ollama_context' not in st.session_state:
            st.session_state.ollama_context = []
        
        # Отображение истории чата
        chat_container = st.container()
        
        with chat_container:
            for i, message in enumerate(st.session_state.ollama_chat_history):
                if message['role'] == 'user':
                    with st.chat_message("user"):
                        st.write(message['content'])
                else:
                    with st.chat_message("assistant"):
                        st.write(message['content'])
        
        # Поле ввода
        user_input = st.chat_input("Введите ваше сообщение...")
        
        if user_input:
            # Добавление сообщения пользователя в историю
            st.session_state.ollama_chat_history.append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now()
            })
            
            # Отображение сообщения пользователя
            with chat_container:
                with st.chat_message("user"):
                    st.write(user_input)
            
            # Генерация ответа
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                # Формирование промпта с контекстом
                context_messages = []
                for msg in st.session_state.ollama_chat_history[-10:]:  # Последние 10 сообщений
                    if msg['role'] == 'user':
                        context_messages.append(f"Пользователь: {msg['content']}")
                    else:
                        context_messages.append(f"Ассистент: {msg['content']}")
                
                context_prompt = "\n".join(context_messages)
                context_prompt += f"\nПользователь: {user_input}\nАссистент:"
                
                # Потоковая генерация ответа
                try:
                    async for chunk in self.ollama_service.stream_response(
                        selected_model, 
                        context_prompt, 
                        st.session_state.ollama_context
                    ):
                        full_response += chunk
                        response_placeholder.write(full_response + "▌")
                    
                    # Убираем курсор
                    response_placeholder.write(full_response)
                    
                    # Добавление ответа в историю
                    st.session_state.ollama_chat_history.append({
                        'role': 'assistant',
                        'content': full_response,
                        'timestamp': datetime.now()
                    })
                    
                except Exception as e:
                    error_msg = f"Ошибка генерации ответа: {e}"
                    response_placeholder.write(error_msg)
                    st.session_state.ollama_chat_history.append({
                        'role': 'assistant',
                        'content': error_msg,
                        'timestamp': datetime.now()
                    })
        
        # Информация о модели
        if models:
            selected_model_info = next((m for m in models if m['name'] == selected_model), None)
            if selected_model_info:
                with st.expander("ℹ️ Информация о модели"):
                    st.write(f"**Название:** {selected_model_info['name']}")
                    st.write(f"**Размер:** {selected_model_info.get('size', 'N/A')} байт")
                    st.write(f"**Дата модификации:** {selected_model_info.get('modified_at', 'N/A')}")
                    st.write(f"**Контекст:** {len(st.session_state.ollama_context)} сообщений")


async def main():
    """Основная функция для запуска чата"""
    ollama_service = OllamaChatService()
    await ollama_service.initialize()
    
    chat_ui = OllamaChatUI(ollama_service)
    await chat_ui.render_chat_page()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())