#!/usr/bin/env python3
"""
Web Dashboard для AGI Layer v3.9
Streamlit интерфейс для мониторинга и управления системой
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
import aiohttp
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
import sys
from pathlib import Path

# Добавляем путь к агентам
sys.path.append(str(Path(__file__).parent.parent))

# Конфигурация страницы
st.set_page_config(
    page_title="AGI Layer v3.9 Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Конфигурация БД
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'agi_layer'),
    'user': os.getenv('POSTGRES_USER', 'agi_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'agi_password')
}

# Кеширование данных
@st.cache_data(ttl=30)
def get_agent_status():
    """Получение статуса агентов"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT agent_name, status, last_heartbeat, metrics
            FROM agent_status
            ORDER BY agent_name
        """)
        
        agents = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [dict(agent) for agent in agents]
        
    except Exception as e:
        st.error(f"Ошибка получения статуса агентов: {e}")
        return []

@st.cache_data(ttl=60)
def get_task_statistics():
    """Получение статистики задач"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Общая статистика
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM tasks
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY status
        """)
        status_stats = cursor.fetchall()
        
        # Статистика по агентам
        cursor.execute("""
            SELECT 
                agent_name,
                status,
                COUNT(*) as count
            FROM tasks
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY agent_name, status
            ORDER BY agent_name
        """)
        agent_stats = cursor.fetchall()
        
        # Статистика по времени
        cursor.execute("""
            SELECT 
                DATE_TRUNC('hour', created_at) as hour,
                COUNT(*) as count
            FROM tasks
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY hour
            ORDER BY hour
        """)
        time_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            'status': [dict(row) for row in status_stats],
            'agents': [dict(row) for row in agent_stats],
            'time': [dict(row) for row in time_stats]
        }
        
    except Exception as e:
        st.error(f"Ошибка получения статистики задач: {e}")
        return {'status': [], 'agents': [], 'time': []}

@st.cache_data(ttl=30)
def get_recent_tasks(limit=50):
    """Получение последних задач"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                id, agent_name, task_type, status, 
                created_at, updated_at, data
            FROM tasks
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [dict(task) for task in tasks]
        
    except Exception as e:
        st.error(f"Ошибка получения задач: {e}")
        return []

@st.cache_data(ttl=60)
def get_system_logs(limit=100):
    """Получение системных логов"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                agent_name, level, message, created_at
            FROM agent_logs
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [dict(log) for log in logs]
        
    except Exception as e:
        st.error(f"Ошибка получения логов: {e}")
        return []

def send_task_to_agent(agent_name, task_type, data):
    """Отправка задачи агенту"""
    try:
        # Здесь должен быть HTTP запрос к MetaAgent
        # Для демонстрации возвращаем успех
        return {"status": "success", "message": f"Задача отправлена агенту {agent_name}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def main():
    """Основная функция дашборда"""
    
    # Заголовок
    st.title("🤖 AGI Layer v3.9 Dashboard")
    st.markdown("*Мониторинг и управление мультиагентной системой*")
    
    # Боковая панель
    with st.sidebar:
        st.header("🎛️ Управление")
        
        # Обновление данных
        if st.button("🔄 Обновить данные", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        
        # Фильтры
        st.subheader("📊 Фильтры")
        
        time_range = st.selectbox(
            "Временной диапазон",
            ["Последний час", "Последние 24 часа", "Последняя неделя"],
            index=1
        )
        
        agent_filter = st.multiselect(
            "Агенты",
            ["meta_agent", "telegram_agent", "image_gen_agent", "vision_agent", 
             "memory_agent", "report_agent", "watchdog_agent", "recovery_agent"],
            default=[]
        )
        
        st.divider()
        
        # Быстрые действия
        st.subheader("⚡ Быстрые действия")
        
        if st.button("🎨 Генерировать изображение", use_container_width=True):
            st.session_state.show_image_gen = True
        
        if st.button("📊 Создать отчет", use_container_width=True):
            st.session_state.show_report_gen = True
        
        if st.button("🧠 Поиск в памяти", use_container_width=True):
            st.session_state.show_memory_search = True
    
    # Основная область
    
    # Статус системы
    st.header("📈 Статус системы")
    
    agents_data = get_agent_status()
    
    if agents_data:
        # Метрики в колонках
        col1, col2, col3, col4 = st.columns(4)
        
        active_agents = len([a for a in agents_data if a['status'] == 'running'])
        total_agents = len(agents_data)
        
        with col1:
            st.metric("Активные агенты", f"{active_agents}/{total_agents}")
        
        with col2:
            # Последняя активность
            if agents_data:
                last_activity = max([a.get('last_heartbeat', datetime.min) for a in agents_data if a.get('last_heartbeat')])
                if isinstance(last_activity, str):
                    last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                time_diff = datetime.now() - last_activity.replace(tzinfo=None)
                st.metric("Последняя активность", f"{int(time_diff.total_seconds())}с назад")
            else:
                st.metric("Последняя активность", "Нет данных")
        
        with col3:
            # Статистика задач за сегодня
            task_stats = get_task_statistics()
            total_tasks = sum([s['count'] for s in task_stats['status']])
            st.metric("Задач за 24ч", total_tasks)
        
        with col4:
            # Успешность выполнения
            if task_stats['status']:
                completed = sum([s['count'] for s in task_stats['status'] if s['status'] == 'completed'])
                success_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0
                st.metric("Успешность", f"{success_rate:.1f}%")
            else:
                st.metric("Успешность", "Нет данных")
        
        # Таблица агентов
        st.subheader("🤖 Статус агентов")
        
        agents_df = pd.DataFrame(agents_data)
        if not agents_df.empty:
            # Форматируем данные для отображения
            display_df = agents_df.copy()
            display_df['status'] = display_df['status'].map({
                'running': '🟢 Работает',
                'stopped': '🔴 Остановлен',
                'error': '❌ Ошибка',
                'starting': '🟡 Запускается'
            })
            
            # Форматируем время
            if 'last_heartbeat' in display_df.columns:
                display_df['last_heartbeat'] = pd.to_datetime(display_df['last_heartbeat']).dt.strftime('%H:%M:%S')
            
            st.dataframe(
                display_df[['agent_name', 'status', 'last_heartbeat']],
                column_config={
                    "agent_name": "Агент",
                    "status": "Статус",
                    "last_heartbeat": "Последний сигнал"
                },
                use_container_width=True
            )
    else:
        st.warning("Нет данных о статусе агентов")
    
    # Статистика задач
    st.header("📊 Статистика задач")
    
    task_stats = get_task_statistics()
    
    if task_stats['status']:
        col1, col2 = st.columns(2)
        
        with col1:
            # Круговая диаграмма статусов
            status_df = pd.DataFrame(task_stats['status'])
            fig_pie = px.pie(
                status_df, 
                values='count', 
                names='status',
                title="Распределение статусов задач (24ч)"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Статистика по агентам
            if task_stats['agents']:
                agents_df = pd.DataFrame(task_stats['agents'])
                agents_pivot = agents_df.pivot(index='agent_name', columns='status', values='count').fillna(0)
                
                fig_bar = px.bar(
                    agents_pivot.reset_index(),
                    x='agent_name',
                    y=agents_pivot.columns.tolist(),
                    title="Задачи по агентам (24ч)"
                )
                fig_bar.update_xaxis(tickangle=45)
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Временная диаграмма
        if task_stats['time']:
            time_df = pd.DataFrame(task_stats['time'])
            time_df['hour'] = pd.to_datetime(time_df['hour'])
            
            fig_line = px.line(
                time_df,
                x='hour',
                y='count',
                title="Активность по часам (24ч)",
                markers=True
            )
            st.plotly_chart(fig_line, use_container_width=True)
    
    # Последние задачи
    st.header("📋 Последние задачи")
    
    recent_tasks = get_recent_tasks(20)
    
    if recent_tasks:
        tasks_df = pd.DataFrame(recent_tasks)
        
        # Форматируем для отображения
        display_tasks = tasks_df.copy()
        display_tasks['created_at'] = pd.to_datetime(display_tasks['created_at']).dt.strftime('%H:%M:%S')
        display_tasks['status'] = display_tasks['status'].map({
            'pending': '⏳ Ожидает',
            'processing': '⚙️ Обрабатывается', 
            'completed': '✅ Завершена',
            'failed': '❌ Ошибка'
        })
        
        st.dataframe(
            display_tasks[['created_at', 'agent_name', 'task_type', 'status']],
            column_config={
                "created_at": "Время",
                "agent_name": "Агент",
                "task_type": "Тип",
                "status": "Статус"
            },
            use_container_width=True
        )
        
        # Детали выбранной задачи
        if st.checkbox("Показать детали задач"):
            selected_task = st.selectbox(
                "Выберите задачу",
                options=range(len(recent_tasks)),
                format_func=lambda x: f"{recent_tasks[x]['task_type']} ({recent_tasks[x]['created_at']})"
            )
            
            if selected_task is not None:
                task = recent_tasks[selected_task]
                st.json(task)
    
    # Системные логи
    st.header("📝 Системные логи")
    
    logs = get_system_logs(50)
    
    if logs:
        logs_df = pd.DataFrame(logs)
        logs_df['created_at'] = pd.to_datetime(logs_df['created_at']).dt.strftime('%H:%M:%S')
        
        # Фильтр по уровню
        level_filter = st.multiselect(
            "Уровень логов",
            ["INFO", "WARNING", "ERROR", "DEBUG"],
            default=["INFO", "WARNING", "ERROR"]
        )
        
        if level_filter:
            filtered_logs = logs_df[logs_df['level'].isin(level_filter)]
        else:
            filtered_logs = logs_df
        
        # Цветовая схема для уровней
        def color_level(level):
            colors = {
                'INFO': '🔵',
                'WARNING': '🟡', 
                'ERROR': '🔴',
                'DEBUG': '⚪'
            }
            return colors.get(level, '⚪')
        
        # Отображаем логи
        for _, log in filtered_logs.head(20).iterrows():
            level_icon = color_level(log['level'])
            st.text(f"{level_icon} {log['created_at']} [{log['agent_name']}] {log['message']}")
    
    # Модальные окна для быстрых действий
    
    # Генерация изображения
    if st.session_state.get('show_image_gen', False):
        with st.expander("🎨 Генерация изображения", expanded=True):
            prompt = st.text_input("Описание изображения")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Генерировать"):
                    if prompt:
                        result = send_task_to_agent("image_gen_agent", "generate_image", {"prompt": prompt})
                        if result['status'] == 'success':
                            st.success("Задача отправлена на генерацию!")
                        else:
                            st.error(f"Ошибка: {result.get('error')}")
                    else:
                        st.warning("Введите описание изображения")
            
            with col2:
                if st.button("Закрыть"):
                    st.session_state.show_image_gen = False
                    st.rerun()
    
    # Создание отчета
    if st.session_state.get('show_report_gen', False):
        with st.expander("📊 Создание отчета", expanded=True):
            report_type = st.selectbox("Тип отчета", ["system_status", "task_analysis", "agent_performance"])
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Создать отчет"):
                    result = send_task_to_agent("report_agent", "generate_report", {"report_type": report_type})
                    if result['status'] == 'success':
                        st.success("Задача на создание отчета отправлена!")
                    else:
                        st.error(f"Ошибка: {result.get('error')}")
            
            with col2:
                if st.button("Закрыть "):
                    st.session_state.show_report_gen = False
                    st.rerun()
    
    # Поиск в памяти
    if st.session_state.get('show_memory_search', False):
        with st.expander("🧠 Поиск в памяти", expanded=True):
            search_query = st.text_input("Поисковый запрос")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Найти"):
                    if search_query:
                        result = send_task_to_agent("memory_agent", "memory_search", {"query": search_query})
                        if result['status'] == 'success':
                            st.success("Поиск выполнен!")
                        else:
                            st.error(f"Ошибка: {result.get('error')}")
                    else:
                        st.warning("Введите поисковый запрос")
            
            with col2:
                if st.button("Закрыть  "):
                    st.session_state.show_memory_search = False
                    st.rerun()
    
    # Футер
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("🤖 AGI Layer v3.9")
    
    with col2:
        st.caption(f"🕐 Обновлено: {datetime.now().strftime('%H:%M:%S')}")
    
    with col3:
        if st.button("⚙️ Настройки"):
            st.info("Настройки будут добавлены в следующей версии")

# Автообновление каждые 30 секунд
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# Проверяем, нужно ли обновить
if (datetime.now() - st.session_state.last_update).seconds > 30:
    st.session_state.last_update = datetime.now()
    st.rerun()

if __name__ == "__main__":
    main()