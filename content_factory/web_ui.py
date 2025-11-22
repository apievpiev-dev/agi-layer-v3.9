"""
Веб-интерфейс для управления контент-заводом
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from content_factory.config.database import db
from content_factory.config.settings import settings
from content_factory.modules.planning import ContentPlanner
from content_factory.modules.preparation import SpecGenerator
from content_factory.modules.production import ContentProducer
from content_factory.modules.quality_control import QualityController
from content_factory.modules.packaging import ContentPackager
from content_factory.modules.distribution import ContentDistributor
from content_factory.modules.analytics import ContentAnalytics


# Настройка страницы
st.set_page_config(
    page_title="Контент-завод",
    page_icon="🏭",
    layout="wide"
)

# Инициализация модулей
@st.cache_resource
def init_modules():
    return {
        "planner": ContentPlanner(),
        "spec_generator": SpecGenerator(),
        "producer": ContentProducer(),
        "quality": QualityController(),
        "packager": ContentPackager(),
        "distributor": ContentDistributor(),
        "analytics": ContentAnalytics()
    }

modules = init_modules()

# Боковая панель навигации
st.sidebar.title("🏭 Контент-завод")
page = st.sidebar.selectbox(
    "Выберите раздел",
    [
        "📊 Дашборд",
        "🎯 Фундамент",
        "📅 Планирование",
        "📝 ТЗ",
        "✍️ Производство",
        "✅ Контроль качества",
        "🎨 Упаковка",
        "📤 Дистрибуция",
        "📈 Аналитика"
    ]
)

# Главная страница - Дашборд
if page == "📊 Дашборд":
    st.title("📊 Дашборд контент-завода")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Статистика
    goals = db.get_goals()
    audiences = db.get_audiences()
    topics = db.get_topics()
    ideas = db.get_ideas()
    plan_items = db.get_content_plan()
    content_items = db.get_content_items()
    
    with col1:
        st.metric("Цели", len(goals))
    with col2:
        st.metric("Аудитории", len(audiences))
    with col3:
        st.metric("Темы", len(topics))
    with col4:
        st.metric("Идеи", len(ideas))
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Контент-план")
        planned = len([p for p in plan_items if p['status'] == 'planned'])
        in_progress = len([p for p in plan_items if p['status'] == 'in_progress'])
        ready = len([p for p in plan_items if p['status'] == 'ready'])
        published = len([p for p in plan_items if p['status'] == 'published'])
        
        st.metric("Запланировано", planned)
        st.metric("В работе", in_progress)
        st.metric("Готово", ready)
        st.metric("Опубликовано", published)
    
    with col2:
        st.subheader("Контент")
        draft = len([c for c in content_items if c['status'] == 'draft'])
        review = len([c for c in content_items if c['status'] == 'review'])
        approved = len([c for c in content_items if c['status'] == 'approved'])
        published = len([c for c in content_items if c['status'] == 'published'])
        
        st.metric("Черновики", draft)
        st.metric("На проверке", review)
        st.metric("Одобрено", approved)
        st.metric("Опубликовано", published)

# Фундамент
elif page == "🎯 Фундамент":
    st.title("🎯 Фундамент контент-завода")
    
    tab1, tab2, tab3 = st.tabs(["Цели", "Аудитории", "Темы"])
    
    with tab1:
        st.subheader("Цели")
        
        with st.form("add_goal"):
            goal_name = st.text_input("Название цели")
            goal_desc = st.text_area("Описание")
            goal_metric = st.text_input("Целевая метрика")
            goal_value = st.number_input("Целевое значение", value=0.0)
            
            if st.form_submit_button("Добавить цель"):
                if goal_name:
                    db.add_goal(goal_name, goal_desc, goal_metric, goal_value)
                    st.success("Цель добавлена!")
                    st.rerun()
        
        st.divider()
        goals = db.get_goals()
        for goal in goals:
            with st.expander(goal['name']):
                st.write(goal.get('description', ''))
                st.write(f"Метрика: {goal.get('target_metric', 'N/A')}")
                st.write(f"Цель: {goal.get('target_value', 0)}")
    
    with tab2:
        st.subheader("Аудитории")
        
        with st.form("add_audience"):
            aud_name = st.text_input("Название аудитории")
            aud_desc = st.text_area("Описание")
            aud_lang = st.selectbox("Язык", ["ru", "en"])
            
            if st.form_submit_button("Добавить аудиторию"):
                if aud_name:
                    db.add_audience(aud_name, aud_desc, language=aud_lang)
                    st.success("Аудитория добавлена!")
                    st.rerun()
        
        st.divider()
        audiences = db.get_audiences()
        for audience in audiences:
            with st.expander(audience['name']):
                st.write(audience.get('description', ''))
                st.write(f"Язык: {audience.get('language', 'ru')}")
    
    with tab3:
        st.subheader("Темы")
        
        goals = db.get_goals()
        audiences = db.get_audiences()
        
        with st.form("add_topic"):
            topic_name = st.text_input("Название темы")
            topic_desc = st.text_area("Описание")
            topic_goal = st.selectbox("Цель", [None] + [g['id'] for g in goals], format_func=lambda x: next((g['name'] for g in goals if g['id'] == x), "Не выбрано"))
            topic_audience = st.selectbox("Аудитория", [None] + [a['id'] for a in audiences], format_func=lambda x: next((a['name'] for a in audiences if a['id'] == x), "Не выбрано"))
            topic_priority = st.slider("Приоритет", 1, 5, 1)
            
            if st.form_submit_button("Добавить тему"):
                if topic_name:
                    db.add_topic(topic_name, topic_desc, topic_goal, topic_audience, topic_priority)
                    st.success("Тема добавлена!")
                    st.rerun()
        
        st.divider()
        topics = db.get_topics()
        for topic in topics:
            with st.expander(topic['name']):
                st.write(topic.get('description', ''))
                st.write(f"Приоритет: {topic.get('priority', 1)}")

# Планирование
elif page == "📅 Планирование":
    st.title("📅 Планирование контента")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Сбор идей")
        topics = db.get_topics()
        if topics:
            selected_topic = st.selectbox("Выберите тему", topics, format_func=lambda x: x['name'])
            
            if st.button("Собрать идеи"):
                with st.spinner("Собираю идеи..."):
                    ideas = modules["planner"].collect_ideas(selected_topic['id'])
                    if ideas:
                        modules["planner"].save_ideas(ideas)
                        st.success(f"Собрано {len(ideas)} идей!")
                        st.rerun()
    
    with col2:
        st.subheader("Идеи")
        ideas = db.get_ideas()
        for idea in ideas[:10]:
            with st.expander(idea['title']):
                st.write(idea.get('description', ''))
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Одобрить", key=f"approve_{idea['id']}"):
                        # Обновление статуса (нужен метод в БД)
                        st.success("Одобрено!")
                with col2:
                    st.write(f"SEO: {idea.get('seo_potential', 0):.2f}")
    
    st.divider()
    st.subheader("Контент-план")
    
    if st.button("Создать контент-план"):
        with st.spinner("Создаю план..."):
            plan = modules["planner"].create_content_plan()
            st.success(f"Создан план на {plan['total_items']} единиц контента!")
            st.json(plan)
    
    plan_items = db.get_content_plan()
    for item in plan_items[:20]:
        with st.expander(f"{item['publish_date']} - {item['format']}"):
            idea = next((i for i in db.get_ideas() if i['id'] == item['idea_id']), None)
            if idea:
                st.write(idea['title'])
            st.write(f"Статус: {item['status']}")

# ТЗ
elif page == "📝 ТЗ":
    st.title("📝 Технические задания")
    
    plan_items = db.get_content_plan()
    if plan_items:
        selected_plan = st.selectbox(
            "Выберите план",
            plan_items,
            format_func=lambda x: f"{x['publish_date']} - {x['format']}"
        )
        
        if st.button("Создать ТЗ"):
            with st.spinner("Генерирую ТЗ..."):
                try:
                    spec = modules["spec_generator"].generate_spec(selected_plan['id'])
                    st.success("ТЗ создано!")
                    st.json(spec)
                except Exception as e:
                    st.error(f"Ошибка: {e}")
    
    st.divider()
    specs = db.get_specs()
    for spec in specs:
        with st.expander(spec['title']):
            st.write(f"Цель: {spec.get('goal', 'N/A')}")
            st.write(f"Аудитория: {spec.get('target_audience', 'N/A')}")

# Производство
elif page == "✍️ Производство":
    st.title("✍️ Производство контента")
    
    specs = db.get_specs()
    if specs:
        selected_spec = st.selectbox("Выберите ТЗ", specs, format_func=lambda x: x['title'])
        
        if st.button("Создать контент"):
            with st.spinner("Генерирую контент..."):
                try:
                    content = modules["producer"].create_content(selected_spec['id'])
                    st.success("Контент создан!")
                    st.text_area("Контент", content['content'], height=400)
                except Exception as e:
                    st.error(f"Ошибка: {e}")
    
    st.divider()
    content_items = db.get_content_items()
    for item in content_items:
        with st.expander(item['title']):
            st.write(f"Статус: {item['status']}")
            st.write(f"Формат: {item['format']}")
            st.text_area("Контент", item['content'], height=200, key=f"content_{item['id']}")

# Контроль качества
elif page == "✅ Контроль качества":
    st.title("✅ Контроль качества")
    
    content_items = db.get_content_items(status="draft")
    if content_items:
        selected_content = st.selectbox("Выберите контент", content_items, format_func=lambda x: x['title'])
        
        if st.button("Проверить качество"):
            with st.spinner("Проверяю..."):
                try:
                    result = modules["quality"].check_content(selected_content['id'])
                    st.success("Проверка завершена!")
                    
                    st.metric("Общая оценка", f"{result['overall_score']:.2%}")
                    st.write(f"Статус: {result['status']}")
                    
                    for check_name, check_result in result['checks'].items():
                        with st.expander(f"{check_name} - {check_result['score']:.2%}"):
                            if check_result.get('issues'):
                                for issue in check_result['issues']:
                                    st.write(f"⚠️ {issue}")
                            else:
                                st.write("✅ Проблем не найдено")
                    
                    st.subheader("Рекомендации")
                    for rec in result['recommendations']:
                        st.write(f"💡 {rec}")
                except Exception as e:
                    st.error(f"Ошибка: {e}")

# Упаковка
elif page == "🎨 Упаковка":
    st.title("🎨 Упаковка контента")
    
    content_items = db.get_content_items(status="approved")
    if content_items:
        selected_content = st.selectbox("Выберите контент", content_items, format_func=lambda x: x['title'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Создать обложку"):
                with st.spinner("Создаю обложку..."):
                    try:
                        cover = modules["packager"].create_cover(selected_content['id'], selected_content['title'])
                        st.success("Обложка создана!")
                        st.write(f"Путь: {cover['file_path']}")
                    except Exception as e:
                        st.error(f"Ошибка: {e}")
        
        with col2:
            if st.button("Создать изображения для соцсетей"):
                with st.spinner("Создаю изображения..."):
                    try:
                        assets = modules["packager"].create_social_media_images(selected_content['id'])
                        st.success("Изображения созданы!")
                        st.json(assets)
                    except Exception as e:
                        st.error(f"Ошибка: {e}")

# Дистрибуция
elif page == "📤 Дистрибуция":
    st.title("📤 Дистрибуция контента")
    
    content_items = db.get_content_items(status="approved")
    if content_items:
        selected_content = st.selectbox("Выберите контент", content_items, format_func=lambda x: x['title'])
        platform = st.selectbox("Платформа", ["website", "telegram", "vk", "ok"])
        
        if st.button("Опубликовать"):
            with st.spinner("Публикую..."):
                try:
                    result = modules["distributor"].publish_content(selected_content['id'], platform)
                    if result['success']:
                        st.success("Опубликовано!")
                        st.write(f"URL: {result.get('url', 'N/A')}")
                    else:
                        st.error("Ошибка публикации")
                except Exception as e:
                    st.error(f"Ошибка: {e}")

# Аналитика
elif page == "📈 Аналитика":
    st.title("📈 Аналитика")
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("Начальная дата", start_date)
    with col2:
        end = st.date_input("Конечная дата", end_date)
    
    if st.button("Сгенерировать отчет"):
        with st.spinner("Генерирую отчет..."):
            try:
                report = modules["analytics"].generate_report(
                    start.isoformat(),
                    end.isoformat()
                )
                
                st.subheader("Общие метрики")
                metrics = report['overall_metrics']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Всего просмотров", metrics['total_views'])
                with col2:
                    st.metric("Вовлеченность", metrics['total_engagement'])
                with col3:
                    st.metric("Среднее просмотров", f"{metrics['average_views_per_content']:.0f}")
                
                st.subheader("Топ контент")
                for content in report['top_content']:
                    st.write(f"**{content['title']}** - {content['metric_value']:.0f} просмотров")
                
                st.subheader("Рекомендации")
                for rec in report['recommendations']:
                    st.write(f"💡 {rec}")
            except Exception as e:
                st.error(f"Ошибка: {e}")
