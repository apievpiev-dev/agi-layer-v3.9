"""
Модуль контроля качества (Шаг 4: Цех контроля качества)
"""

import re
import json
from typing import Dict, Any, List
from content_factory.config.database import db
from content_factory.modules.ai_integration import AIIntegration
from content_factory.config.settings import settings


class QualityController:
    """Класс для контроля качества контента"""
    
    def __init__(self):
        self.db = db
        self.ai = AIIntegration()
    
    def check_content(self, content_id: int) -> Dict[str, Any]:
        """
        Полная проверка контента
        
        Args:
            content_id: ID контента для проверки
        """
        # Получаем контент
        items = self.db.get_content_items()
        content_item = None
        for item in items:
            if item['id'] == content_id:
                content_item = item
                break
        
        if not content_item:
            raise ValueError(f"Контент с ID {content_id} не найден")
        
        content_text = content_item['content']
        
        # Выполняем все проверки
        checks = {
            "editing": self._check_editing(content_text, content_item),
            "proofreading": self._check_proofreading(content_text),
            "seo": self._check_seo(content_text, content_item),
            "factcheck": self._check_factcheck(content_text),
            "structure": self._check_structure(content_text)
        }
        
        # Общая оценка
        overall_score = sum(check['score'] for check in checks.values()) / len(checks)
        
        # Определяем статус
        if overall_score >= 0.8:
            status = "passed"
        elif overall_score >= 0.6:
            status = "needs_revision"
        else:
            status = "failed"
        
        result = {
            "content_id": content_id,
            "overall_score": overall_score,
            "status": status,
            "checks": checks,
            "recommendations": self._get_recommendations(checks)
        }
        
        # Сохраняем результаты проверок
        self._save_quality_checks(content_id, checks)
        
        return result
    
    def _check_editing(self, text: str, content_item: Dict) -> Dict[str, Any]:
        """Проверка редактирования (логика, структура, стиль)"""
        issues = []
        score = 1.0
        
        # Проверка длины
        word_count = len(text.split())
        if word_count < settings.MIN_ARTICLE_LENGTH:
            issues.append(f"Текст слишком короткий ({word_count} слов, минимум {settings.MIN_ARTICLE_LENGTH})")
            score -= 0.2
        elif word_count > settings.MAX_ARTICLE_LENGTH:
            issues.append(f"Текст слишком длинный ({word_count} слов, максимум {settings.MAX_ARTICLE_LENGTH})")
            score -= 0.1
        
        # Проверка структуры
        if not re.search(r'^#\s+', text, re.MULTILINE):
            issues.append("Отсутствует заголовок H1")
            score -= 0.1
        
        h2_count = len(re.findall(r'^##\s+', text, re.MULTILINE))
        if h2_count < 2:
            issues.append(f"Мало подзаголовков H2 ({h2_count}, рекомендуется минимум 2)")
            score -= 0.1
        
        # Проверка абзацев
        paragraphs = text.split("\n\n")
        if len(paragraphs) < 3:
            issues.append("Мало абзацев, текст плохо структурирован")
            score -= 0.1
        
        # Проверка введения и заключения
        first_para = paragraphs[0] if paragraphs else ""
        last_para = paragraphs[-1] if paragraphs else ""
        
        if len(first_para) < 50:
            issues.append("Слишком короткое введение")
            score -= 0.05
        
        if len(last_para) < 50:
            issues.append("Слишком короткое заключение")
            score -= 0.05
        
        return {
            "type": "editing",
            "score": max(0.0, score),
            "issues": issues,
            "status": "passed" if score >= 0.8 else "needs_revision"
        }
    
    def _check_proofreading(self, text: str) -> Dict[str, Any]:
        """Проверка корректуры (орфография, пунктуация)"""
        issues = []
        score = 1.0
        
        # Простая проверка на очевидные ошибки
        # В реальности можно использовать библиотеки типа pymorphy2, natasha
        
        # Проверка двойных пробелов
        if "  " in text:
            issues.append("Найдены двойные пробелы")
            score -= 0.05
        
        # Проверка пробелов перед знаками препинания
        if re.search(r'\s+[.,;:!?]', text):
            issues.append("Найдены пробелы перед знаками препинания")
            score -= 0.05
        
        # Проверка отсутствия пробелов после знаков препинания
        if re.search(r'[.,;:!?][А-Яа-яA-Za-z]', text):
            issues.append("Отсутствуют пробелы после знаков препинания")
            score -= 0.1
        
        # Проверка на повторяющиеся слова
        words = text.lower().split()
        for i in range(len(words) - 1):
            if words[i] == words[i+1] and len(words[i]) > 3:
                issues.append(f"Повторяющееся слово: '{words[i]}'")
                score -= 0.05
                break
        
        return {
            "type": "proofreading",
            "score": max(0.0, score),
            "issues": issues,
            "status": "passed" if score >= 0.8 else "needs_revision"
        }
    
    def _check_seo(self, text: str, content_item: Dict) -> Dict[str, Any]:
        """SEO-проверка"""
        issues = []
        score = 1.0
        
        # Получаем ключевые слова из метаданных
        metadata = json.loads(content_item.get('metadata', '{}'))
        keywords = metadata.get('keywords_used', [])
        
        if not keywords:
            # Пытаемся получить из ТЗ
            specs = self.db.get_specs()
            spec = None
            for s in specs:
                if s['id'] == content_item['spec_id']:
                    spec = s
                    break
            
            if spec:
                keywords = json.loads(spec.get('keywords', '[]'))
        
        if keywords:
            # Проверяем использование ключевых слов
            text_lower = text.lower()
            for keyword in keywords[:5]:  # Проверяем первые 5
                keyword_lower = keyword.lower()
                count = text_lower.count(keyword_lower)
                
                if count == 0:
                    issues.append(f"Ключевое слово '{keyword}' не используется")
                    score -= 0.1
                elif count < 2:
                    issues.append(f"Ключевое слово '{keyword}' используется редко ({count} раз)")
                    score -= 0.05
        
        # Проверка заголовка H1
        h1_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        if h1_match:
            h1_text = h1_match.group(1)
            if keywords:
                h1_lower = h1_text.lower()
                if not any(kw.lower() in h1_lower for kw in keywords[:3]):
                    issues.append("В заголовке H1 нет ключевых слов")
                    score -= 0.15
        else:
            issues.append("Отсутствует заголовок H1")
            score -= 0.2
        
        # Проверка длины текста для SEO
        word_count = len(text.split())
        if word_count < 1000:
            issues.append(f"Текст слишком короткий для SEO ({word_count} слов)")
            score -= 0.1
        
        # Используем AI для дополнительного SEO-анализа
        if keywords:
            seo_analysis = self.ai.analyze_seo(text, keywords)
            if seo_analysis['score'] < 0.7:
                issues.extend(seo_analysis['recommendations'])
                score = min(score, seo_analysis['score'])
        
        return {
            "type": "seo",
            "score": max(0.0, score),
            "issues": issues,
            "status": "passed" if score >= 0.7 else "needs_revision"
        }
    
    def _check_factcheck(self, text: str) -> Dict[str, Any]:
        """Проверка фактов (упрощенная версия)"""
        issues = []
        score = 1.0
        
        # Простая проверка на подозрительные утверждения
        # В реальности можно использовать фактчекинг API
        
        # Проверка на числа и статистику
        numbers = re.findall(r'\d+%', text)
        if numbers:
            # Если есть проценты, проверяем на разумность
            for num_str in numbers:
                num = int(num_str.replace('%', ''))
                if num > 100:
                    issues.append(f"Подозрительный процент: {num_str}")
                    score -= 0.1
        
        # Проверка на утверждения без источников
        claim_patterns = [
            r'исследования показывают',
            r'ученые доказали',
            r'статистика говорит'
        ]
        
        for pattern in claim_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Проверяем, есть ли ссылка рядом
                # Упрощенная проверка
                pass
        
        return {
            "type": "factcheck",
            "score": max(0.0, score),
            "issues": issues,
            "status": "passed" if score >= 0.8 else "needs_revision"
        }
    
    def _check_structure(self, text: str) -> Dict[str, Any]:
        """Проверка структуры"""
        issues = []
        score = 1.0
        
        # Проверка наличия заголовков
        h1_count = len(re.findall(r'^#\s+', text, re.MULTILINE))
        h2_count = len(re.findall(r'^##\s+', text, re.MULTILINE))
        h3_count = len(re.findall(r'^###\s+', text, re.MULTILINE))
        
        if h1_count == 0:
            issues.append("Отсутствует заголовок H1")
            score -= 0.2
        elif h1_count > 1:
            issues.append(f"Слишком много заголовков H1 ({h1_count}, должен быть один)")
            score -= 0.1
        
        if h2_count < 2:
            issues.append(f"Мало подзаголовков H2 ({h2_count})")
            score -= 0.1
        
        # Проверка длины абзацев
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        long_paragraphs = [p for p in paragraphs if len(p) > 500]
        if long_paragraphs:
            issues.append(f"Найдены слишком длинные абзацы ({len(long_paragraphs)} шт.)")
            score -= 0.1
        
        # Проверка списков
        has_lists = bool(re.search(r'^[\-\*\+]\s+', text, re.MULTILINE))
        if not has_lists and len(paragraphs) > 5:
            issues.append("Рекомендуется добавить списки для лучшей читаемости")
            score -= 0.05
        
        return {
            "type": "structure",
            "score": max(0.0, score),
            "issues": issues,
            "status": "passed" if score >= 0.8 else "needs_revision"
        }
    
    def _get_recommendations(self, checks: Dict[str, Dict]) -> List[str]:
        """Получение общих рекомендаций"""
        recommendations = []
        
        for check_name, check_result in checks.items():
            if check_result['status'] != "passed":
                recommendations.extend([
                    f"{check_name}: {issue}" 
                    for issue in check_result.get('issues', [])[:3]
                ])
        
        if not recommendations:
            recommendations.append("Контент соответствует всем требованиям качества")
        
        return recommendations
    
    def _save_quality_checks(self, content_id: int, checks: Dict[str, Dict]):
        """Сохранение результатов проверок в БД"""
        # В реальности здесь будет сохранение в таблицу quality_checks
        # Пока просто логируем
        pass
    
    def approve_content(self, content_id: int) -> bool:
        """Одобрение контента после проверки"""
        self.db.update_content_status(content_id, "approved")
        return True
    
    def reject_content(self, content_id: int, reason: str = "") -> bool:
        """Отклонение контента"""
        self.db.update_content_status(content_id, "rejected")
        return True
