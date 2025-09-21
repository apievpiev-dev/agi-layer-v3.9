"""
Ollama Chat Web Interface - Веб-интерфейс для чата с Ollama
"""

import asyncio
import logging
import streamlit as st
import aiohttp
import json
from typing import Dict, Any, List, AsyncGenerator
from datetime import datetime
import os


class OllamaChatUI:
    """Веб-интерфейс для чата с Ollama"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.http_session = None
        self.ollama_host = config.get('ollama_host', 'localhost')
        self.ollama_port = config.get('ollama_port', 11434)
        self.ollama_base_url = f"http://{self.ollama_host}:{self.ollama_port}"
        
    async def initialize(self):
        """Инициализация Web UI"""
        self.http_session = aiohttp.ClientSession()
        
        # Проверка подключения к Ollama
        try:
            async with self.http_session.get(f"{self.ollama_base_url}/api/tags") as response:
                if response.status == 200:
                    st.success("✅ Подключение к Ollama установлено")
                else:
                    st.error("❌ Не удалось подключиться к Ollama")
        except Exception as e:
            st.error(f"❌ Ошибка подключения к Ollama: {e}")
    
    async def run(self):
        """Запуск Streamlit приложения"""
        # Настройка страницы
        st.set_page_config(
            page_title="Ollama Chat - AGI Layer",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Основной заголовок
        st.title("🤖 Ollama Chat - Веб-интерфейс")
        st.markdown("---")
        
        # Инициализация сессии
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        if 'current_model' not in st.session_state:
            st.session_state.current_model = 'llama2'
        
        # Боковая панель
        await self._render_sidebar()
        
        # Основной чат
        await self._render_chat()
    
    async def _render_sidebar(self):
        """Отрисовка боковой панели"""
        with st.sidebar:
            st.header("⚙️ Настройки чата")
            
            # Выбор модели
            st.subheader("📋 Доступные модели")
            try:
                models = await self._get_available_models()
                if models:
                    selected_model = st.selectbox(
                        "Выберите модель:",
                        models,
                        index=models.index(st.session_state.current_model) if st.session_state.current_model in models else 0
                    )
                    if selected_model != st.session_state.current_model:
                        st.session_state.current_model = selected_model
                        st.rerun()
                else:
                    st.warning("Нет доступных моделей")
                    st.info("Загрузите модель командой: `ollama pull llama2`")
            except Exception as e:
                st.error(f"Ошибка получения моделей: {e}")
            
            st.markdown("---")
            
            # Настройки генерации
            st.subheader("🎛️ Параметры генерации")
            
            temperature = st.slider(
                "Температура (креативность):",
                min_value=0.0,
                max_value=2.0,
                value=0.7,
                step=0.1,
                help="Высокие значения делают ответы более креативными"
            )
            
            max_tokens = st.slider(
                "Максимум токенов:",
                min_value=100,
                max_value=4000,
                value=1000,
                step=100,
                help="Максимальная длина ответа"
            )
            
            top_p = st.slider(
                "Top-p (nucleus sampling):",
                min_value=0.0,
                max_value=1.0,
                value=0.9,
                step=0.05,
                help="Контролирует разнообразие ответов"
            )
            
            # Сохранение параметров в сессии
            st.session_state.generation_params = {
                'temperature': temperature,
                'max_tokens': max_tokens,
                'top_p': top_p
            }
            
            st.markdown("---")
            
            # Действия
            st.subheader("🛠️ Действия")
            
            if st.button("🗑️ Очистить чат", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
            
            if st.button("📥 Загрузить модель", use_container_width=True):
                model_name = st.text_input("Имя модели (например: llama2):")
                if model_name:
                    with st.spinner(f"Загрузка модели {model_name}..."):
                        success = await self._pull_model(model_name)
                        if success:
                            st.success(f"Модель {model_name} загружена!")
                        else:
                            st.error(f"Ошибка загрузки модели {model_name}")
            
            if st.button("🔄 Обновить список моделей", use_container_width=True):
                st.rerun()
            
            st.markdown("---")
            
            # Статус системы
            await self._render_system_status()
    
    async def _render_system_status(self):
        """Отрисовка статуса системы"""
        st.subheader("📊 Статус системы")
        
        try:
            # Проверка статуса Ollama
            async with self.http_session.get(f"{self.ollama_base_url}/api/tags") as response:
                if response.status == 200:
                    st.success("🟢 Ollama работает")
                else:
                    st.error("🔴 Ollama недоступен")
        except Exception as e:
            st.error(f"🔴 Ошибка: {e}")
        
        # Информация о текущей модели
        st.info(f"**Текущая модель:** {st.session_state.current_model}")
        
        # Количество сообщений
        st.info(f"**Сообщений в чате:** {len(st.session_state.messages)}")
    
    async def _render_chat(self):
        """Отрисовка основного чата"""
        # Отображение истории сообщений
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Поле ввода
        if prompt := st.chat_input("Введите ваше сообщение..."):
            # Добавление сообщения пользователя
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Отображение сообщения пользователя
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Генерация ответа
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                try:
                    # Получение параметров генерации
                    params = st.session_state.get('generation_params', {
                        'temperature': 0.7,
                        'max_tokens': 1000,
                        'top_p': 0.9
                    })
                    
                    # Отправка запроса к Ollama
                    async for chunk in self._generate_response(prompt, params):
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                    
                    # Финальное отображение
                    message_placeholder.markdown(full_response)
                    
                    # Добавление ответа в историю
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                except Exception as e:
                    error_msg = f"Ошибка генерации ответа: {e}"
                    message_placeholder.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
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
    
    async def _generate_response(self, prompt: str, params: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Генерация ответа через Ollama API"""
        try:
            # Подготовка контекста
            messages = []
            
            # Добавление системного промпта
            system_prompt = "Ты полезный AI-ассистент. Отвечай на русском языке, если вопрос задан на русском."
            messages.append({"role": "system", "content": system_prompt})
            
            # Добавление истории сообщений
            for msg in st.session_state.messages[-10:]:  # Последние 10 сообщений
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Добавление текущего сообщения
            messages.append({"role": "user", "content": prompt})
            
            # Подготовка запроса
            request_data = {
                "model": st.session_state.current_model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": params.get('temperature', 0.7),
                    "num_predict": params.get('max_tokens', 1000),
                    "top_p": params.get('top_p', 0.9)
                }
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
    
    async def _pull_model(self, model_name: str) -> bool:
        """Загрузка модели"""
        try:
            async with self.http_session.post(
                f"{self.ollama_base_url}/api/pull",
                json={"name": model_name}
            ) as response:
                return response.status == 200
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели {model_name}: {e}")
            return False
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.http_session:
            await self.http_session.close()


async def main():
    """Основная функция запуска Ollama Chat UI"""
    config = {
        'ollama_host': os.getenv('OLLAMA_HOST', 'localhost'),
        'ollama_port': int(os.getenv('OLLAMA_PORT', 11434))
    }
    
    chat_ui = OllamaChatUI(config)
    
    try:
        await chat_ui.initialize()
        await chat_ui.run()
    finally:
        await chat_ui.cleanup()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())