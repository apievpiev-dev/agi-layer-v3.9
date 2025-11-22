"""
Модуль планирования контента (Шаг 1: Цех планирования)
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

try:
    from content_factory.config.database import db
    from content_factory.config.settings import settings
except ImportError:
    from config.database import db
    from config.settings import settings


class ContentPlanner:
    """Класс для планирования контента"""
    
    def __init__(self):
        self.db = db
    
    def collect_ideas(self, topic_id: int, sources: List[str] = None) -> List[Dict[str, Any]]:
        """
        Сбор идей для контента из различных источников
        
        Args:
            topic_id: ID темы
            sources: Список источников идей (questions, competitors, seo, trends, brainstorm)
        """
        ideas = []
        sources = sources or ["questions", "seo", "brainstorm"]
        
        # Идеи из вопросов клиентов (заглушка - в реальности можно подключить к CRM)
        if "questions" in sources:
            ideas.extend(self._get_ideas_from_questions(topic_id))
        
        # Идеи из SEO-анализа
        if "seo" in sources:
            ideas.extend(self._get_ideas_from_seo(topic_id))
        
        # Идеи из мозгового штурма
        if "brainstorm" in sources:
            ideas.extend(self._get_ideas_from_brainstorm(topic_id))
        
        # Идеи из анализа конкурентов (заглушка)
        if "competitors" in sources:
            ideas.extend(self._get_ideas_from_competitors(topic_id))
        
        # Идеи из трендов (заглушка)
        if "trends" in sources:
            ideas.extend(self._get_ideas_from_trends(topic_id))
        
        return ideas
    
    def _get_ideas_from_questions(self, topic_id: int) -> List[Dict[str, Any]]:
        """Генерация идей на основе типичных вопросов"""
        topic = self._get_topic(topic_id)
        if not topic:
            return []
        
        # Шаблоны вопросов для разных тем
        question_templates = [
            f"Как {topic['name'].lower()}?",
            f"Что такое {topic['name'].lower()}?",
            f"Лучшие способы {topic['name'].lower()}",
            f"Ошибки в {topic['name'].lower()}",
            f"С чего начать {topic['name'].lower()}?",
            f"Советы по {topic['name'].lower()}",
        ]
        
        ideas = []
        for template in question_templates:
            ideas.append({
                "title": template,
                "description": f"Статья, отвечающая на вопрос: {template}",
                "topic_id": topic_id,
                "source": "questions",
                "keywords": self._extract_keywords(template),
                "seo_potential": 0.7,
                "priority": 1
            })
        
        return ideas
    
    def _get_ideas_from_seo(self, topic_id: int) -> List[Dict[str, Any]]:
        """Генерация идей на основе SEO-запросов"""
        topic = self._get_topic(topic_id)
        if not topic:
            return []
        
        # Шаблоны SEO-запросов
        seo_templates = [
            f"{topic['name']} для начинающих",
            f"{topic['name']} пошаговая инструкция",
            f"{topic['name']} лучшие практики",
            f"{topic['name']} примеры",
            f"{topic['name']} обзор",
            f"{topic['name']} сравнение",
            f"{topic['name']} руководство",
            f"{topic['name']} советы",
        ]
        
        ideas = []
        for template in seo_templates:
            ideas.append({
                "title": template,
                "description": f"SEO-оптимизированная статья: {template}",
                "topic_id": topic_id,
                "source": "seo",
                "keywords": self._extract_keywords(template),
                "seo_potential": 0.9,
                "priority": 2
            })
        
        return ideas
    
    def _get_ideas_from_brainstorm(self, topic_id: int) -> List[Dict[str, Any]]:
        """Генерация идей из мозгового штурма"""
        topic = self._get_topic(topic_id)
        if not topic:
            return []
        
        # Шаблоны для мозгового штурма
        brainstorm_templates = [
            f"История успеха: {topic['name']}",
            f"Кейс: {topic['name']}",
            f"Интервью с экспертом: {topic['name']}",
            f"Чек-лист: {topic['name']}",
            f"Инфографика: {topic['name']}",
            f"Видео-урок: {topic['name']}",
        ]
        
        ideas = []
        for template in brainstorm_templates:
            ideas.append({
                "title": template,
                "description": f"Креативный контент: {template}",
                "topic_id": topic_id,
                "source": "brainstorm",
                "keywords": self._extract_keywords(template),
                "seo_potential": 0.6,
                "priority": 1
            })
        
        return ideas
    
    def _get_ideas_from_competitors(self, topic_id: int) -> List[Dict[str, Any]]:
        """Анализ конкурентов (заглушка)"""
        # В реальности здесь можно парсить конкурентов
        return []
    
    def _get_ideas_from_trends(self, topic_id: int) -> List[Dict[str, Any]]:
        """Анализ трендов (заглушка)"""
        # В реальности здесь можно использовать API трендов
        return []
    
    def _get_topic(self, topic_id: int) -> Optional[Dict[str, Any]]:
        """Получение темы"""
        topics = self.db.get_topics()
        for topic in topics:
            if topic['id'] == topic_id:
                return topic
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Извлечение ключевых слов из текста"""
        # Простое извлечение (в реальности можно использовать NLP)
        words = re.findall(r'\b[а-яёa-z]{4,}\b', text.lower())
        return list(set(words))[:10]
    
    def analyze_seo(self, idea_title: str, keywords: List[str] = None) -> Dict[str, Any]:
        """
        SEO-анализ идеи
        
        Args:
            idea_title: Заголовок идеи
            keywords: Список ключевых слов
        """
        keywords = keywords or self._extract_keywords(idea_title)
        
        # Простой SEO-анализ
        seo_score = 0.0
        factors = {
            "title_length": len(idea_title),
            "keywords_count": len(keywords),
            "keyword_density": 0.0
        }
        
        if 30 <= factors["title_length"] <= 60:
            seo_score += 0.3
        
        if factors["keywords_count"] >= 3:
            seo_score += 0.3
        
        # Проверка наличия ключевых слов в заголовке
        title_lower = idea_title.lower()
        matched_keywords = sum(1 for kw in keywords if kw.lower() in title_lower)
        if matched_keywords > 0:
            factors["keyword_density"] = matched_keywords / len(keywords)
            seo_score += 0.4
        
        return {
            "score": seo_score,
            "factors": factors,
            "recommendations": self._get_seo_recommendations(seo_score, factors)
        }
    
    def _get_seo_recommendations(self, score: float, factors: Dict[str, Any]) -> List[str]:
        """Получение SEO-рекомендаций"""
        recommendations = []
        
        if factors["title_length"] < 30:
            recommendations.append("Увеличьте длину заголовка до 30-60 символов")
        elif factors["title_length"] > 60:
            recommendations.append("Сократите заголовок до 60 символов")
        
        if factors["keywords_count"] < 3:
            recommendations.append("Добавьте больше ключевых слов")
        
        if factors["keyword_density"] < 0.3:
            recommendations.append("Включите больше ключевых слов в заголовок")
        
        return recommendations
    
    def create_content_plan(self, days_ahead: int = None) -> Dict[str, Any]:
        """
        Создание контент-плана на указанный период
        
        Args:
            days_ahead: Количество дней вперед
        """
        days_ahead = days_ahead or settings.CONTENT_PLAN_DAYS_AHEAD
        end_date = (datetime.now() + timedelta(days=days_ahead)).date()
        
        # Получаем все одобренные идеи
        ideas = self.db.get_ideas(status="approved")
        
        if not ideas:
            # Если нет одобренных идей, берем новые
            ideas = self.db.get_ideas(status="new")[:10]
        
        # Распределяем идеи по датам
        plan = {}
        current_date = datetime.now().date()
        idea_index = 0
        
        while current_date <= end_date and idea_index < len(ideas):
            # Пропускаем выходные (можно настроить)
            if current_date.weekday() < 5:  # Понедельник-Пятница
                idea = ideas[idea_index % len(ideas)]
                
                # Определяем формат контента
                formats = ["article", "post", "video", "infographic"]
                content_format = formats[idea_index % len(formats)]
                
                # Добавляем в план
                plan_id = self.db.add_to_plan(
                    idea_id=idea['id'],
                    publish_date=current_date.isoformat(),
                    format=content_format,
                    platform="website",
                    keyword=json.loads(idea.get('keywords', '[]'))[0] if idea.get('keywords') else None,
                    responsible="system"
                )
                
                plan[current_date.isoformat()] = {
                    "plan_id": plan_id,
                    "idea": idea,
                    "format": content_format
                }
                
                idea_index += 1
            
            current_date += timedelta(days=1)
        
        return {
            "start_date": datetime.now().date().isoformat(),
            "end_date": end_date.isoformat(),
            "total_items": len(plan),
            "plan": plan
        }
    
    def save_ideas(self, ideas: List[Dict[str, Any]]):
        """Сохранение идей в базу данных"""
        saved_ids = []
        for idea in ideas:
            idea_id = self.db.add_idea(
                title=idea["title"],
                description=idea.get("description", ""),
                topic_id=idea.get("topic_id"),
                source=idea.get("source", "unknown"),
                keywords=idea.get("keywords", []),
                seo_potential=idea.get("seo_potential", 0.0),
                priority=idea.get("priority", 1)
            )
            saved_ids.append(idea_id)
        return saved_ids
