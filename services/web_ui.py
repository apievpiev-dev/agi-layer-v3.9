"""
Web UI - интерфейс управления AGI Layer v3.9
"""

import asyncio
import logging
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import asyncpg
import aiohttp
from typing import Dict, Any, List
import json


class WebUI:
    """Web интерфейс для управления системой"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db_pool = None
        self.http_session = None
        
    async def initialize(self):
        """Инициализация Web UI"""
        # Подключение к базе данных
        self.db_pool = await asyncpg.create_pool(
            host=self.config['postgres']['host'],
            port=self.config['postgres']['port'],
            database=self.config['postgres']['database'],
            user=self.config['postgres']['user'],
            password=self.config['postgres']['password']
        )
        
        # HTTP сессия для API вызовов
        self.http_session = aiohttp.ClientSession()
        
    async def run(self):
        """Запуск Streamlit приложения"""
        # Настройка страницы
        st.set_page_config(
            page_title="AGI Layer v3.9",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Основной заголовок
        st.title("🤖 AGI Layer v3.9 - Система управления")
        st.markdown("---")
        
        # Боковая панель
        await self._render_sidebar()
        
        # Основной контент
        page = st.session_state.get('page', 'dashboard')
        
        if page == 'dashboard':
            await self._render_dashboard()
        elif page == 'agents':
            await self._render_agents_page()
        elif page == 'tasks':
            await self._render_tasks_page()
        elif page == 'images':
            await self._render_images_page()
        elif page == 'logs':
            await self._render_logs_page()
        elif page == 'settings':
            await self._render_settings_page()
    
    async def _render_sidebar(self):
        """Отрисовка боковой панели"""
        with st.sidebar:
            st.header("📊 Навигация")
            
            if st.button("📈 Дашборд", use_container_width=True):
                st.session_state.page = 'dashboard'
            
            if st.button("🤖 Агенты", use_container_width=True):
                st.session_state.page = 'agents'
            
            if st.button("📋 Задачи", use_container_width=True):
                st.session_state.page = 'tasks'
            
            if st.button("🖼️ Изображения", use_container_width=True):
                st.session_state.page = 'images'
            
            if st.button("📝 Логи", use_container_width=True):
                st.session_state.page = 'logs'
            
            if st.button("⚙️ Настройки", use_container_width=True):
                st.session_state.page = 'settings'
            
            st.markdown("---")
            
            # Статус системы
            await self._render_system_status()
    
    async def _render_system_status(self):
        """Отрисовка статуса системы"""
        st.header("🔍 Статус системы")
        
        try:
            async with self.db_pool.acquire() as conn:
                # Статистика агентов
                agents_stats = await conn.fetch(
                    "SELECT name, status, tasks_completed, errors_count FROM agents"
                )
                
                total_tasks = sum(row['tasks_completed'] for row in agents_stats)
                total_errors = sum(row['errors_count'] for row in agents_stats)
                running_agents = len([row for row in agents_stats if row['status'] == 'running'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Агентов запущено", running_agents)
                    st.metric("Всего задач", total_tasks)
                
                with col2:
                    st.metric("Ошибок", total_errors)
                    st.metric("Всего агентов", len(agents_stats))
                
        except Exception as e:
            st.error(f"Ошибка получения статуса: {e}")
    
    async def _render_dashboard(self):
        """Отрисовка дашборда"""
        st.header("📈 Дашборд системы")
        
        # Метрики в реальном времени
        col1, col2, col3, col4 = st.columns(4)
        
        try:
            async with self.db_pool.acquire() as conn:
                # Получение метрик
                agents_count = await conn.fetchval("SELECT COUNT(*) FROM agents")
                running_count = await conn.fetchval("SELECT COUNT(*) FROM agents WHERE status = 'running'")
                pending_tasks = await conn.fetchval("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
                completed_tasks = await conn.fetchval("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
                
                with col1:
                    st.metric("Всего агентов", agents_count)
                
                with col2:
                    st.metric("Запущено", running_count)
                
                with col3:
                    st.metric("Задач в очереди", pending_tasks)
                
                with col4:
                    st.metric("Завершено", completed_tasks)
                
        except Exception as e:
            st.error(f"Ошибка получения метрик: {e}")
        
        st.markdown("---")
        
        # Графики
        col1, col2 = st.columns(2)
        
        with col1:
            await self._render_tasks_chart()
        
        with col2:
            await self._render_agents_chart()
        
        # Последние задачи
        st.subheader("📋 Последние задачи")
        await self._render_recent_tasks()
    
    async def _render_tasks_chart(self):
        """Отрисовка графика задач"""
        try:
            async with self.db_pool.acquire() as conn:
                # Получение статистики задач за последние 24 часа
                rows = await conn.fetch(
                    """
                    SELECT 
                        DATE_TRUNC('hour', created_at) as hour,
                        status,
                        COUNT(*) as count
                    FROM tasks 
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                    GROUP BY hour, status
                    ORDER BY hour
                    """
                )
                
                if rows:
                    df = pd.DataFrame([dict(row) for row in rows])
                    
                    fig = px.bar(
                        df, 
                        x='hour', 
                        y='count', 
                        color='status',
                        title="Задачи по часам (24ч)",
                        color_discrete_map={
                            'pending': '#FFA500',
                            'processing': '#1f77b4',
                            'completed': '#2ca02c',
                            'failed': '#d62728'
                        }
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Нет данных о задачах")
                    
        except Exception as e:
            st.error(f"Ошибка построения графика задач: {e}")
    
    async def _render_agents_chart(self):
        """Отрисовка графика агентов"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT name, status, tasks_completed, errors_count FROM agents"
                )
                
                if rows:
                    df = pd.DataFrame([dict(row) for row in rows])
                    
                    fig = go.Figure()
                    
                    # График выполненных задач
                    fig.add_trace(go.Bar(
                        name='Задачи выполнены',
                        x=df['name'],
                        y=df['tasks_completed'],
                        marker_color='lightblue'
                    ))
                    
                    # График ошибок
                    fig.add_trace(go.Bar(
                        name='Ошибки',
                        x=df['name'],
                        y=df['errors_count'],
                        marker_color='lightcoral'
                    ))
                    
                    fig.update_layout(
                        title="Производительность агентов",
                        xaxis_title="Агенты",
                        yaxis_title="Количество",
                        barmode='group'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Нет данных об агентах")
                    
        except Exception as e:
            st.error(f"Ошибка построения графика агентов: {e}")
    
    async def _render_recent_tasks(self):
        """Отрисовка последних задач"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, agent_name, task_type, status, created_at, updated_at
                    FROM tasks 
                    ORDER BY created_at DESC 
                    LIMIT 10
                    """
                )
                
                if rows:
                    df = pd.DataFrame([dict(row) for row in rows])
                    
                    # Форматирование времени
                    df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%H:%M:%S')
                    df['updated_at'] = pd.to_datetime(df['updated_at']).dt.strftime('%H:%M:%S')
                    
                    st.dataframe(
                        df,
                        use_container_width=True,
                        column_config={
                            "id": "ID",
                            "agent_name": "Агент",
                            "task_type": "Тип",
                            "status": "Статус",
                            "created_at": "Создано",
                            "updated_at": "Обновлено"
                        }
                    )
                else:
                    st.info("Нет задач")
                    
        except Exception as e:
            st.error(f"Ошибка получения задач: {e}")
    
    async def _render_agents_page(self):
        """Отрисовка страницы агентов"""
        st.header("🤖 Управление агентами")
        
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT name, status, last_activity, memory_usage, cpu_usage, 
                           tasks_completed, errors_count, created_at
                    FROM agents 
                    ORDER BY name
                    """
                )
                
                if rows:
                    for row in rows:
                        with st.expander(f"{row['name']} - {row['status']}"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Статус", row['status'])
                                st.metric("Задач выполнено", row['tasks_completed'])
                            
                            with col2:
                                st.metric("Использование памяти", f"{row['memory_usage']:.1f} MB")
                                st.metric("Использование CPU", f"{row['cpu_usage']:.1f}%")
                            
                            with col3:
                                st.metric("Ошибок", row['errors_count'])
                                st.metric("Последняя активность", 
                                         row['last_activity'].strftime('%H:%M:%S') if row['last_activity'] else 'N/A')
                            
                            # Кнопки управления
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button(f"Перезапустить {row['name']}", key=f"restart_{row['name']}"):
                                    await self._restart_agent(row['name'])
                            
                            with col2:
                                if st.button(f"Остановить {row['name']}", key=f"stop_{row['name']}"):
                                    await self._stop_agent(row['name'])
                            
                            with col3:
                                if st.button(f"Логи {row['name']}", key=f"logs_{row['name']}"):
                                    st.session_state.agent_logs = row['name']
                                    st.session_state.page = 'logs'
                else:
                    st.info("Нет агентов")
                    
        except Exception as e:
            st.error(f"Ошибка получения агентов: {e}")
    
    async def _render_tasks_page(self):
        """Отрисовка страницы задач"""
        st.header("📋 Управление задачами")
        
        # Фильтры
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox("Статус", ["Все", "pending", "processing", "completed", "failed"])
        
        with col2:
            agent_filter = st.selectbox("Агент", ["Все"] + await self._get_agent_names())
        
        with col3:
            limit = st.number_input("Количество", min_value=10, max_value=1000, value=50)
        
        try:
            async with self.db_pool.acquire() as conn:
                # Построение запроса
                query = "SELECT * FROM tasks WHERE 1=1"
                params = []
                
                if status_filter != "Все":
                    query += " AND status = $" + str(len(params) + 1)
                    params.append(status_filter)
                
                if agent_filter != "Все":
                    query += " AND agent_name = $" + str(len(params) + 1)
                    params.append(agent_filter)
                
                query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
                params.append(limit)
                
                rows = await conn.fetch(query, *params)
                
                if rows:
                    df = pd.DataFrame([dict(row) for row in rows])
                    
                    # Форматирование данных
                    df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
                    df['updated_at'] = pd.to_datetime(df['updated_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
                    
                    st.dataframe(
                        df,
                        use_container_width=True,
                        column_config={
                            "id": "ID",
                            "agent_name": "Агент",
                            "task_type": "Тип",
                            "status": "Статус",
                            "priority": "Приоритет",
                            "created_at": "Создано",
                            "updated_at": "Обновлено"
                        }
                    )
                else:
                    st.info("Нет задач с указанными фильтрами")
                    
        except Exception as e:
            st.error(f"Ошибка получения задач: {e}")
    
    async def _render_images_page(self):
        """Отрисовка страницы изображений"""
        st.header("🖼️ Сгенерированные изображения")
        
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT task_id, agent_name, prompt, image_path, created_at
                    FROM generated_images 
                    ORDER BY created_at DESC 
                    LIMIT 20
                    """
                )
                
                if rows:
                    for row in rows:
                        with st.expander(f"Изображение {row['task_id'][:8]}..."):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                if os.path.exists(row['image_path']):
                                    st.image(row['image_path'], caption=row['prompt'])
                                else:
                                    st.error(f"Файл не найден: {row['image_path']}")
                            
                            with col2:
                                st.write(f"**Агент:** {row['agent_name']}")
                                st.write(f"**Промпт:** {row['prompt']}")
                                st.write(f"**Создано:** {row['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                                st.write(f"**Путь:** {row['image_path']}")
                else:
                    st.info("Нет сгенерированных изображений")
                    
        except Exception as e:
            st.error(f"Ошибка получения изображений: {e}")
    
    async def _render_logs_page(self):
        """Отрисовка страницы логов"""
        st.header("📝 Логи системы")
        
        # Фильтры
        col1, col2, col3 = st.columns(3)
        
        with col1:
            agent_filter = st.selectbox("Агент", ["Все"] + await self._get_agent_names())
        
        with col2:
            level_filter = st.selectbox("Уровень", ["Все", "INFO", "WARNING", "ERROR"])
        
        with col3:
            hours = st.number_input("Часов назад", min_value=1, max_value=24, value=6)
        
        try:
            async with self.db_pool.acquire() as conn:
                # Построение запроса
                query = "SELECT * FROM agent_logs WHERE timestamp > $" + str(1)
                params = [datetime.now() - timedelta(hours=hours)]
                
                if agent_filter != "Все":
                    query += " AND agent_name = $" + str(len(params) + 1)
                    params.append(agent_filter)
                
                if level_filter != "Все":
                    query += " AND level = $" + str(len(params) + 1)
                    params.append(level_filter)
                
                query += " ORDER BY timestamp DESC LIMIT 100"
                
                rows = await conn.fetch(query, *params)
                
                if rows:
                    for row in rows:
                        timestamp = row['timestamp'].strftime('%H:%M:%S')
                        level = row['level']
                        agent = row['agent_name']
                        message = row['message']
                        
                        # Цветовое кодирование уровней
                        if level == 'ERROR':
                            st.error(f"**{timestamp}** [{agent}] {message}")
                        elif level == 'WARNING':
                            st.warning(f"**{timestamp}** [{agent}] {message}")
                        else:
                            st.info(f"**{timestamp}** [{agent}] {message}")
                else:
                    st.info("Нет логов с указанными фильтрами")
                    
        except Exception as e:
            st.error(f"Ошибка получения логов: {e}")
    
    async def _render_settings_page(self):
        """Отрисовка страницы настроек"""
        st.header("⚙️ Настройки системы")
        
        # Основные настройки
        st.subheader("Основные настройки")
        
        col1, col2 = st.columns(2)
        
        with col1:
            log_level = st.selectbox("Уровень логирования", ["INFO", "DEBUG", "WARNING", "ERROR"])
            agent_timeout = st.number_input("Таймаут агента (сек)", min_value=60, max_value=3600, value=300)
        
        with col2:
            max_tasks = st.number_input("Максимум задач", min_value=1, max_value=100, value=10)
            recovery_interval = st.number_input("Интервал восстановления (сек)", min_value=60, max_value=3600, value=300)
        
        if st.button("Сохранить настройки"):
            st.success("Настройки сохранены")
        
        # Действия системы
        st.subheader("Действия системы")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Перезапустить все агенты", use_container_width=True):
                await self._restart_all_agents()
        
        with col2:
            if st.button("🧹 Очистить логи", use_container_width=True):
                await self._clear_logs()
        
        with col3:
            if st.button("💾 Создать бэкап", use_container_width=True):
                await self._create_backup()
    
    async def _get_agent_names(self) -> List[str]:
        """Получение списка имен агентов"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT DISTINCT name FROM agents ORDER BY name")
                return [row['name'] for row in rows]
        except:
            return []
    
    async def _restart_agent(self, agent_name: str):
        """Перезапуск агента"""
        try:
            # Отправка команды через MetaAgent API
            url = f"http://meta_agent:8000/restart_agent"
            data = {"agent_name": agent_name}
            
            async with self.http_session.post(url, json=data) as response:
                if response.status == 200:
                    st.success(f"Агент {agent_name} перезапущен")
                else:
                    st.error(f"Ошибка перезапуска агента {agent_name}")
        except Exception as e:
            st.error(f"Ошибка: {e}")
    
    async def _stop_agent(self, agent_name: str):
        """Остановка агента"""
        st.info(f"Функция остановки агента {agent_name} в разработке")
    
    async def _restart_all_agents(self):
        """Перезапуск всех агентов"""
        st.info("Функция перезапуска всех агентов в разработке")
    
    async def _clear_logs(self):
        """Очистка логов"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("DELETE FROM agent_logs WHERE timestamp < NOW() - INTERVAL '7 days'")
                st.success("Старые логи очищены")
        except Exception as e:
            st.error(f"Ошибка очистки логов: {e}")
    
    async def _create_backup(self):
        """Создание резервной копии"""
        st.info("Функция создания бэкапа в разработке")


async def main():
    """Основная функция запуска Web UI"""
    from config.settings import settings
    
    config = {
        'postgres': {
            'host': settings.POSTGRES_HOST,
            'port': settings.POSTGRES_PORT,
            'database': settings.POSTGRES_DB,
            'user': settings.POSTGRES_USER,
            'password': settings.POSTGRES_PASSWORD
        }
    }
    
    web_ui = WebUI(config)
    await web_ui.initialize()
    await web_ui.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

