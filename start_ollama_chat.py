#!/usr/bin/env python3
"""
Запуск веб-чата с Ollama
"""

import asyncio
import sys
import os
import logging

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ollama_chat import OllamaChatService, OllamaChatUI
import streamlit as st


async def main():
    """Основная функция запуска чата"""
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Настройка страницы Streamlit
    st.set_page_config(
        page_title="Ollama Chat",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Заголовок
    st.title("🤖 Чат с Ollama")
    st.markdown("---")
    
    # Инициализация сервиса
    ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    ollama_service = OllamaChatService(ollama_url)
    
    try:
        await ollama_service.initialize()
        chat_ui = OllamaChatUI(ollama_service)
        await chat_ui.render_chat_page()
        
    except Exception as e:
        st.error(f"Ошибка инициализации: {e}")
        st.info("Убедитесь, что Ollama запущен на localhost:11434")


if __name__ == "__main__":
    # Запуск через streamlit run
    print("Запуск веб-чата с Ollama...")
    print("Для запуска используйте: streamlit run start_ollama_chat.py")
    
    # Если запускается напрямую, используем asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nЗавершение работы...")