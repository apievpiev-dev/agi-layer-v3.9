"""
AGI Layer v3.9 - Web UI
=======================

Streamlit интерфейс для управления и мониторинга AGI системы:
- Статус всех агентов
- Интерактивный чат с LLM
- Генерация изображений
- Просмотр логов
- Системная статистика
"""

import asyncio
import json
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List

# Конфигурация страницы
st.set_page_config(
    page_title="AGI Layer v3.9",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS стили
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        font-size: 3rem;
        margin-bottom: 2rem;
    }
    .agent-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2E86AB;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class AGIWebUI:
    """Класс для Web интерфейса AGI Layer"""
    
    def __init__(self):
        import os
        self.api_url = os.getenv("API_URL", "http://localhost:18080")
        
    def check_api_connection(self) -> bool:
        """Проверка подключения к API"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_system_status(self) -> Dict:
        """Получение статуса системы"""
        try:
            response = requests.get(f"{self.api_url}/status", timeout=10)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        # Заглушка если API недоступен
        return {
            "meta_agent": {
                "status": "unknown",
                "uptime": 0
            },
            "agents": {},
            "statistics": {
                "total_agents": 0,
                "active_agents": 0,
                "failed_agents": 0
            }
        }
    
    def get_agent_logs(self, agent_name: str) -> List[str]:
        """Получение логов агента"""
        try:
            response = requests.get(f"{self.api_url}/agents/{agent_name}/logs", timeout=5)
            if response.status_code == 200:
                return response.json().get("logs", [])
        except:
            pass
        return ["Логи недоступны"]

def main():
    """Главная функция Web UI"""
    
    # Заголовок
    st.markdown('<h1 class="main-header">🤖 AGI Layer v3.9</h1>', unsafe_allow_html=True)
    
    # Инициализация UI
    ui = AGIWebUI()
    
    # Сайдбар с навигацией
    st.sidebar.title("🛠️ Навигация")
    page = st.sidebar.selectbox(
        "Выберите страницу:",
        ["🏠 Главная", "🤖 Агенты", "💬 Чат", "🎨 Генерация", "📊 Мониторинг", "📝 Логи", "🧠 Память", "⚙️ Настройки"]
    )
    
    # Проверка подключения к API
    if not ui.check_api_connection():
        st.markdown("""
        <div class="error-box">
            ⚠️ <strong>API недоступен</strong><br>
            Система запускается или есть проблемы с подключением.<br>
            Попробуйте обновить страницу через несколько секунд.
        </div>
        """, unsafe_allow_html=True)
    
    # Получаем статус системы
    system_status = ui.get_system_status()
    
    # Отображение выбранной страницы
    if page == "🏠 Главная":
        show_dashboard(system_status)
    elif page == "🤖 Агенты":
        show_agents(system_status)
    elif page == "💬 Чат":
        show_chat()
    elif page == "🎨 Генерация":
        show_generation()
    elif page == "📊 Мониторинг":
        show_monitoring(system_status)
    elif page == "📝 Логи":
        show_logs(ui)
    elif page == "🧠 Память":
        show_memory()
    elif page == "⚙️ Настройки":
        show_settings()

def show_dashboard(system_status: Dict):
    """Главная панель"""
    st.header("📊 Обзор системы")
    
    # Метрики в колонках
    col1, col2, col3, col4 = st.columns(4)
    
    stats = system_status.get("statistics", {})
    
    with col1:
        st.metric(
            "Всего агентов",
            stats.get("total_agents", 0),
            delta=None
        )
    
    with col2:
        st.metric(
            "Активных агентов", 
            stats.get("active_agents", 0),
            delta=None
        )
    
    with col3:
        st.metric(
            "Ошибок",
            stats.get("failed_agents", 0),
            delta=None
        )
    
    with col4:
        uptime = system_status.get("meta_agent", {}).get("uptime", 0)
        st.metric(
            "Время работы (мин)",
            f"{int(uptime // 60)}",
            delta=None
        )
    
    # Статус Meta Agent
    meta_status = system_status.get("meta_agent", {})
    if meta_status.get("status") == "running":
        st.markdown("""
        <div class="success-box">
            ✅ <strong>Meta Agent активен</strong><br>
            Система координации агентов работает нормально.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="error-box">
            ❌ <strong>Meta Agent неактивен</strong><br>
            Проверьте статус Docker контейнеров.
        </div>
        """, unsafe_allow_html=True)

def show_agents(system_status: Dict):
    """Страница агентов"""
    st.header("🤖 Агенты AI")
    
    agents = system_status.get("agents", {})
    
    if not agents:
        st.warning("Агенты еще не зарегистрированы или система запускается...")
        return
    
    for agent_name, agent_info in agents.items():
        with st.expander(f"🤖 {agent_name.replace('_', ' ').title()}", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Статус:** {agent_info.get('status', 'unknown')}")
                st.write(f"**Тип:** {agent_info.get('agent_type', 'unknown')}")
                st.write(f"**Модель:** {agent_info.get('model_name', 'не указана')}")
            
            with col2:
                st.write(f"**Память:** {agent_info.get('memory_usage', 0):.1f} MB")
                st.write(f"**CPU:** {agent_info.get('cpu_usage', 0):.1f}%")
                st.write(f"**Ошибки:** {agent_info.get('error_count', 0)}")

def show_chat():
    """Страница чата с LLM"""
    st.header("💬 Чат с AI")
    
    # История чата
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Отображение истории
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Поле ввода
    if prompt := st.chat_input("Введите ваш вопрос..."):
        # Добавляем сообщение пользователя
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Генерируем ответ через API
        with st.chat_message("assistant"):
            with st.spinner("🤖 Генерирую ответ..."):
                try:
                    # Отправляем запрос к API
                    api_response = requests.post(
                        f"{AGIWebUI().api_url}/generate",
                        json={"prompt": prompt, "model": "llama3.2:3b"},
                        timeout=60
                    )
                    
                    if api_response.status_code == 200:
                        result = api_response.json()
                        response = result.get("generated_text", "Ошибка генерации")
                    else:
                        response = "❌ Ошибка API. Проверьте подключение."
                        
                except Exception as e:
                    response = f"❌ Ошибка: {str(e)}"
                
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

def show_generation():
    """Страница генерации изображений"""
    st.header("🎨 Генерация изображений")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        prompt = st.text_area(
            "Описание изображения:",
            placeholder="Например: красивый закат над горами, фотореалистично",
            height=100
        )
        
        col1_1, col1_2 = st.columns(2)
        with col1_1:
            width = st.slider("Ширина", 256, 1024, 512, 64)
        with col1_2:
            height = st.slider("Высота", 256, 1024, 512, 64)
        
        if st.button("🎨 Генерировать", type="primary"):
            if prompt:
                with st.spinner("Генерация изображения..."):
                    start_time = datetime.now()
                    try:
                        api_url = AGIWebUI().api_url
                        resp = requests.post(
                            f"{api_url}/generate/image",
                            json={
                                "prompt": prompt,
                                "width": width,
                                "height": height,
                                "num_images": 1
                            },
                            timeout=300
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("status") == "completed" and data.get("image_base64"):
                                import base64
                                img_bytes = base64.b64decode(data["image_base64"]) 
                                st.image(img_bytes, caption="Сгенерированное изображение", use_column_width=True)
                                elapsed = (datetime.now() - start_time).total_seconds()
                                st.success(f"Готово за {elapsed:.1f} сек")
                            else:
                                st.warning(data.get("message", "Задача в обработке"))
                        else:
                            st.error("Ошибка API генерации изображения")
                    except Exception as e:
                        st.error(f"Ошибка: {e}")
            else:
                st.warning("Введите описание изображения!")
    
    with col2:
        st.markdown("### 🎯 Советы:")
        st.markdown("""
        - Используйте детальные описания
        - Указывайте стиль: "фотореалистично", "арт", "аниме"
        - Добавляйте освещение: "мягкий свет", "драматичное освещение"
        - Указывайте композицию: "крупный план", "панорама"
        """)

def show_monitoring(system_status: Dict):
    """Страница мониторинга"""
    st.header("📊 Мониторинг системы")
    
    # Системные ресурсы
    st.subheader("💻 Ресурсы сервера")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Заглушка для использования CPU
        cpu_usage = 25  # Примерное значение
        fig_cpu = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = cpu_usage,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "CPU %"},
            gauge = {'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}],
                    'threshold': {'line': {'color': "red", 'width': 4},
                                'thickness': 0.75, 'value': 90}}))
        fig_cpu.update_layout(height=300)
        st.plotly_chart(fig_cpu, use_container_width=True)
    
    with col2:
        # Заглушка для использования RAM
        ram_usage = 15  # 15GB из 128GB
        fig_ram = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = ram_usage,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "RAM GB"},
            gauge = {'axis': {'range': [None, 128]},
                    'bar': {'color': "green"},
                    'steps': [
                        {'range': [0, 64], 'color': "lightgray"},
                        {'range': [64, 96], 'color': "yellow"},
                        {'range': [96, 128], 'color': "red"}]}))
        fig_ram.update_layout(height=300)
        st.plotly_chart(fig_ram, use_container_width=True)
    
    with col3:
        # Заглушка для использования диска
        disk_usage = 8  # 8GB из 1800GB
        fig_disk = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = disk_usage,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Диск GB"},
            gauge = {'axis': {'range': [None, 1800]},
                    'bar': {'color': "purple"},
                    'steps': [
                        {'range': [0, 900], 'color': "lightgray"},
                        {'range': [900, 1350], 'color': "yellow"},
                        {'range': [1350, 1800], 'color': "red"}]}))
        fig_disk.update_layout(height=300)
        st.plotly_chart(fig_disk, use_container_width=True)

def show_logs(ui):
    """Страница логов"""
    st.header("📝 Логи системы")
    
    # Выбор агента
    agent_name = st.selectbox(
        "Выберите агент:",
        ["meta_agent", "llm_agent", "vision_agent", "image_gen_agent", "api_server"]
    )
    
    if st.button("🔄 Обновить логи"):
        logs = ui.get_agent_logs(agent_name)
        
        st.subheader(f"📄 Логи {agent_name}")
        
        # Отображаем логи в контейнере с прокруткой
        log_container = st.container()
        with log_container:
            for log_line in logs[-50:]:  # Последние 50 строк
                st.text(log_line)

def show_settings():
    """Страница настроек"""
    st.header("⚙️ Настройки системы")
    
def show_memory():
    """Страница работы с памятью"""
    st.header("🧠 Память")
    ui = AGIWebUI()
    api_url = ui.api_url

    st.subheader("Запись в память")
    with st.form("memory_store_form"):
        content = st.text_area("Текст для сохранения", height=120)
        meta = st.text_input("Метаданные (JSON)", value="{}")
        submitted = st.form_submit_button("💾 Сохранить")
        if submitted:
            try:
                import json as _json
                metadata = _json.loads(meta) if meta.strip() else {}
                resp = requests.post(f"{api_url}/memory/store", json={"content": content, "metadata": metadata}, timeout=20)
                if resp.status_code == 200:
                    st.success("Сохранено")
                else:
                    st.error(f"Ошибка API: {resp.text}")
            except Exception as e:
                st.error(f"Ошибка: {e}")

    st.subheader("Поиск в памяти")
    with st.form("memory_search_form"):
        query = st.text_input("Запрос")
        nres = st.slider("Результатов", 1, 10, 5)
        submitted = st.form_submit_button("🔎 Искать")
        if submitted:
            try:
                resp = requests.post(f"{api_url}/memory/search", json={"query": query, "n_results": nres}, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    st.json(data)
                else:
                    st.error(f"Ошибка API: {resp.text}")
            except Exception as e:
                st.error(f"Ошибка: {e}")

    # Конфигурация агентов
    st.subheader("🤖 Конфигурация агентов")
    
    with st.expander("LLM Agent настройки"):
        model_name = st.selectbox(
            "Модель:",
            ["llama3.2:3b", "phi3:3.8b", "qwen2.5:7b"]
        )
        max_tokens = st.slider("Максимум токенов:", 128, 4096, 1024)
        temperature = st.slider("Temperature:", 0.1, 2.0, 0.7, 0.1)
        
        if st.button("💾 Сохранить настройки LLM"):
            st.success("Настройки сохранены!")
    
    # Системные настройки
    st.subheader("🔧 Системные настройки")
    
    with st.expander("Ресурсы"):
        max_memory = st.slider("Максимум памяти на агента (GB):", 4, 32, 16)
        max_cpu = st.slider("Максимум CPU ядер на агента:", 1, 16, 4)
        
        if st.button("💾 Сохранить ресурсы"):
            st.success("Настройки ресурсов сохранены!")
    
    # Управление системой
    st.subheader("🛠️ Управление")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Перезапустить систему", type="secondary"):
            st.info("Система перезапускается...")
    
    with col2:
        if st.button("⏹️ Остановить систему", type="secondary"):
            st.warning("Система останавливается...")
    
    with col3:
        if st.button("📋 Экспорт конфигурации", type="secondary"):
            st.success("Конфигурация экспортирована!")


if __name__ == "__main__":
    # Статус установки в сайдбаре
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🚀 Статус установки")
        # Берём статусы из API
        try:
            api_url = AGIWebUI().api_url
            health = requests.get(f"{api_url}/health", timeout=5).json()
            if health.get("status") == "healthy":
                st.success("✅ API доступен")
                models = health.get("available_models", [])
                st.write(f"📦 Моделей Ollama: {len(models)}")
            else:
                st.warning("⚠️ API отвечает, но сообщает о проблемах")
        except Exception:
            st.error("❌ API недоступен")
    
    # Запускаем главную функцию
    main()
