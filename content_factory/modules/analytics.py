"""
Модуль аналитики (Шаг 7: Цех аналитики)
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from content_factory.config.database import db
    from content_factory.config.settings import settings
except ImportError:
    from config.database import db
    from config.settings import settings


class ContentAnalytics:
    """Класс для аналитики контента"""
    
    def __init__(self):
        self.db = db
    
    def track_metric(self, content_id: int, publication_id: int,
                    metric_name: str, metric_value: float,
                    date: Optional[str] = None) -> bool:
        """
        Отслеживание метрики
        
        Args:
            content_id: ID контента
            publication_id: ID публикации
            metric_name: Название метрики (views, likes, shares, etc.)
            metric_value: Значение метрики
            date: Дата (если None - сегодня)
        """
        date = date or datetime.now().date().isoformat()
        
        self.db.add_analytics(
            content_id=content_id,
            publication_id=publication_id,
            metric_name=metric_name,
            metric_value=metric_value,
            date=date
        )
        
        return True
    
    def get_content_performance(self, content_id: int,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Получение производительности контента
        
        Args:
            content_id: ID контента
            start_date: Начальная дата
            end_date: Конечная дата
        """
        analytics = self.db.get_analytics(
            content_id=content_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Агрегируем метрики
        metrics = defaultdict(list)
        for record in analytics:
            metrics[record['metric_name']].append(record['metric_value'])
        
        # Вычисляем статистику
        performance = {}
        for metric_name, values in metrics.items():
            if values:
                performance[metric_name] = {
                    "total": sum(values),
                    "average": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values),
                    "count": len(values)
                }
        
        # Получаем информацию о контенте
        items = self.db.get_content_items()
        content_item = None
        for item in items:
            if item['id'] == content_id:
                content_item = item
                break
        
        return {
            "content_id": content_id,
            "title": content_item['title'] if content_item else "Unknown",
            "period": {
                "start": start_date or "all",
                "end": end_date or "all"
            },
            "metrics": performance,
            "total_records": len(analytics)
        }
    
    def get_top_performing_content(self, metric_name: str = "views",
                                  limit: int = 10,
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Получение топ-контента по метрике
        
        Args:
            metric_name: Название метрики
            limit: Количество результатов
            start_date: Начальная дата
            end_date: Конечная дата
        """
        analytics = self.db.get_analytics(
            start_date=start_date,
            end_date=end_date
        )
        
        # Фильтруем по метрике
        filtered = [a for a in analytics if a['metric_name'] == metric_name]
        
        # Группируем по контенту
        content_metrics = defaultdict(float)
        for record in filtered:
            content_metrics[record['content_id']] += record['metric_value']
        
        # Сортируем
        sorted_content = sorted(
            content_metrics.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        # Получаем информацию о контенте
        items = self.db.get_content_items()
        content_dict = {item['id']: item for item in items}
        
        result = []
        for content_id, total_value in sorted_content:
            if content_id in content_dict:
                result.append({
                    "content_id": content_id,
                    "title": content_dict[content_id]['title'],
                    "metric_value": total_value,
                    "metric_name": metric_name
                })
        
        return result
    
    def get_platform_performance(self, platform: str,
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Получение производительности платформы
        
        Args:
            platform: Название платформы
            start_date: Начальная дата
            end_date: Конечная дата
        """
        # В реальности здесь будет запрос к БД с фильтрацией по платформе
        # Пока возвращаем заглушку
        
        return {
            "platform": platform,
            "total_publications": 0,
            "total_views": 0,
            "average_engagement": 0.0,
            "top_content": []
        }
    
    def get_content_plan_analytics(self, start_date: Optional[str] = None,
                                   end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Аналитика контент-плана
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
        """
        # Получаем план
        plan = self.db.get_content_plan()
        
        # Фильтруем по датам
        if start_date and end_date:
            filtered_plan = [
                p for p in plan
                if start_date <= p['publish_date'] <= end_date
            ]
        else:
            filtered_plan = plan
        
        # Статистика по статусам
        status_counts = defaultdict(int)
        format_counts = defaultdict(int)
        
        for item in filtered_plan:
            status_counts[item['status']] += 1
            format_counts[item['format']] += 1
        
        return {
            "period": {
                "start": start_date or "all",
                "end": end_date or "all"
            },
            "total_items": len(filtered_plan),
            "by_status": dict(status_counts),
            "by_format": dict(format_counts),
            "completion_rate": (
                status_counts.get('published', 0) / len(filtered_plan) * 100
                if filtered_plan else 0
            )
        }
    
    def generate_report(self, start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Генерация отчета
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
        """
        end_date = end_date or datetime.now().date().isoformat()
        start_date = start_date or (datetime.now() - timedelta(days=30)).date().isoformat()
        
        # Собираем данные
        plan_analytics = self.get_content_plan_analytics(start_date, end_date)
        top_content = self.get_top_performing_content("views", limit=5, start_date=start_date, end_date=end_date)
        
        # Общая статистика
        all_analytics = self.db.get_analytics(start_date=start_date, end_date=end_date)
        
        total_views = sum(
            a['metric_value'] for a in all_analytics
            if a['metric_name'] == 'views'
        )
        
        total_engagement = sum(
            a['metric_value'] for a in all_analytics
            if a['metric_name'] in ['likes', 'shares', 'comments']
        )
        
        return {
            "period": {
                "start": start_date,
                "end": end_date
            },
            "content_plan": plan_analytics,
            "top_content": top_content,
            "overall_metrics": {
                "total_views": total_views,
                "total_engagement": total_engagement,
                "average_views_per_content": (
                    total_views / len(top_content) if top_content else 0
                )
            },
            "recommendations": self._generate_recommendations(plan_analytics, top_content)
        }
    
    def _generate_recommendations(self, plan_analytics: Dict,
                                  top_content: List[Dict]) -> List[str]:
        """Генерация рекомендаций на основе аналитики"""
        recommendations = []
        
        # Анализ плана
        completion_rate = plan_analytics.get('completion_rate', 0)
        if completion_rate < 70:
            recommendations.append(
                f"Низкий процент выполнения плана ({completion_rate:.1f}%). "
                "Увеличьте темп производства контента."
            )
        
        # Анализ форматов
        by_format = plan_analytics.get('by_format', {})
        if by_format:
            most_common = max(by_format.items(), key=lambda x: x[1])
            recommendations.append(
                f"Наиболее используемый формат: {most_common[0]}. "
                "Рассмотрите диверсификацию форматов."
            )
        
        # Анализ топ-контента
        if top_content:
            avg_views = sum(c['metric_value'] for c in top_content) / len(top_content)
            recommendations.append(
                f"Среднее количество просмотров топ-контента: {avg_views:.0f}. "
                "Изучите успешные темы и создавайте похожий контент."
            )
        
        if not recommendations:
            recommendations.append("Все показатели в норме. Продолжайте в том же духе!")
        
        return recommendations
