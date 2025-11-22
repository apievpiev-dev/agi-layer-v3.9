"""
Модуль сборки контента (Шаг 3: Цех сборки)
"""

import json
from typing import Dict, Any, Optional
from content_factory.config.database import db
from content_factory.modules.ai_integration import AIIntegration
from content_factory.config.settings import settings


class ContentProducer:
    """Класс для производства контента"""
    
    def __init__(self):
        self.db = db
        self.ai = AIIntegration()
    
    def create_content(self, spec_id: int) -> Dict[str, Any]:
        """
        Создание контента на основе ТЗ
        
        Args:
            spec_id: ID технического задания
        """
        # Получаем ТЗ
        specs = self.db.get_specs()
        spec = None
        for s in specs:
            if s['id'] == spec_id:
                spec = s
                break
        
        if not spec:
            raise ValueError(f"ТЗ с ID {spec_id} не найдено")
        
        # Получаем информацию о плане для определения формата
        plan_items = self.db.get_content_plan()
        plan_item = None
        for item in plan_items:
            if item['id'] == spec['plan_id']:
                plan_item = item
                break
        
        format_type = plan_item['format'] if plan_item else "article"
        
        # Генерируем контент в зависимости от формата
        if format_type == "article":
            content = self._generate_article(spec)
        elif format_type == "post":
            content = self._generate_post(spec)
        elif format_type == "video":
            content = self._generate_video_script(spec)
        else:
            content = self._generate_generic(spec)
        
        # Сохраняем контент
        content_id = self.db.add_content(
            spec_id=spec_id,
            title=spec['title'],
            content=content['text'],
            format=format_type,
            metadata=content.get('metadata', {}),
            status="draft"
        )
        
        return {
            "content_id": content_id,
            "title": spec['title'],
            "content": content['text'],
            "format": format_type,
            "metadata": content.get('metadata', {})
        }
    
    def _generate_article(self, spec: Dict) -> Dict[str, Any]:
        """Генерация статьи"""
        
        # Парсим структуру
        structure = json.loads(spec.get('structure', '{}'))
        main_points = json.loads(spec.get('main_points', '[]'))
        keywords = json.loads(spec.get('keywords', '[]'))
        
        # Строим промпт для AI
        prompt = f"""
        Напиши подробную статью на тему: {spec['title']}
        
        Цель: {spec.get('goal', 'Информировать аудиторию')}
        Целевая аудитория: {spec.get('target_audience', 'Общая аудитория')}
        Ключевые слова: {', '.join(keywords[:5])}
        
        Основные тезисы для раскрытия:
        {chr(10).join(f'- {point}' for point in main_points[:7])}
        
        Требования:
        - Минимальная длина: {settings.MIN_ARTICLE_LENGTH} слов
        - Максимальная длина: {settings.MAX_ARTICLE_LENGTH} слов
        - Используй ключевые слова естественным образом
        - Структурируй текст с подзаголовками
        - Добавь введение и заключение
        - Пиши информативно и интересно
        
        Начни статью прямо с заголовка H1: {spec['title']}
        """
        
        # Генерируем текст
        article_text = self.ai.generate_text(
            prompt,
            max_tokens=settings.MAX_ARTICLE_LENGTH,
            temperature=0.7
        )
        
        # Улучшаем структуру
        article_text = self._improve_structure(article_text, structure)
        
        # Добавляем метаданные
        metadata = {
            "word_count": len(article_text.split()),
            "keywords_used": keywords,
            "structure_sections": len(structure.get('sections', [])) if structure else 0
        }
        
        return {
            "text": article_text,
            "metadata": metadata
        }
    
    def _generate_post(self, spec: Dict) -> Dict[str, Any]:
        """Генерация поста для соцсетей"""
        
        main_points = json.loads(spec.get('main_points', '[]'))
        keywords = json.loads(spec.get('keywords', '[]'))
        
        prompt = f"""
        Напиши пост для социальных сетей на тему: {spec['title']}
        
        Требования:
        - Длина: 200-500 слов
        - Цепляющий заголовок
        - Интересный и вовлекающий текст
        - Призыв к действию в конце
        - Используй эмодзи для выразительности
        - Ключевые слова: {', '.join(keywords[:3])}
        
        Основные моменты для упоминания:
        {chr(10).join(f'- {point}' for point in main_points[:3])}
        """
        
        post_text = self.ai.generate_text(prompt, max_tokens=500, temperature=0.8)
        
        metadata = {
            "word_count": len(post_text.split()),
            "has_emoji": "😀" in post_text or "👍" in post_text,
            "has_cta": any(word in post_text.lower() for word in ["подпишись", "читай", "узнай", "переходи"])
        }
        
        return {
            "text": post_text,
            "metadata": metadata
        }
    
    def _generate_video_script(self, spec: Dict) -> Dict[str, Any]:
        """Генерация сценария для видео"""
        
        main_points = json.loads(spec.get('main_points', '[]'))
        
        prompt = f"""
        Создай сценарий для видео на тему: {spec['title']}
        
        Формат: YouTube видео (5-10 минут)
        
        Структура:
        1. Хук (первые 15 секунд - зацепить внимание)
        2. Вступление (30 секунд - о чем видео)
        3. Основная часть (раскрытие темы по пунктам)
        4. Заключение (30 секунд - резюме и призыв к действию)
        
        Основные пункты для раскрытия:
        {chr(10).join(f'- {point}' for point in main_points)}
        
        Верни сценарий с тайм-кодами и репликами.
        """
        
        script = self.ai.generate_text(prompt, max_tokens=1500, temperature=0.7)
        
        metadata = {
            "estimated_duration": "5-10 минут",
            "sections_count": len(main_points) + 2,
            "has_hook": True,
            "has_cta": True
        }
        
        return {
            "text": script,
            "metadata": metadata
        }
    
    def _generate_generic(self, spec: Dict) -> Dict[str, Any]:
        """Генерация контента общего формата"""
        
        main_points = json.loads(spec.get('main_points', '[]'))
        
        prompt = f"""
        Создай контент на тему: {spec['title']}
        
        {spec.get('goal', '')}
        
        Основные моменты:
        {chr(10).join(f'- {point}' for point in main_points)}
        
        Создай информативный и полезный контент.
        """
        
        content = self.ai.generate_text(prompt, max_tokens=2000, temperature=0.7)
        
        return {
            "text": content,
            "metadata": {}
        }
    
    def _improve_structure(self, text: str, structure: Dict) -> str:
        """Улучшение структуры текста"""
        # Простое улучшение - добавление подзаголовков если их нет
        if "##" not in text and "**" not in text:
            # Пытаемся разбить на абзацы и добавить подзаголовки
            paragraphs = text.split("\n\n")
            if len(paragraphs) > 3:
                # Добавляем подзаголовки к некоторым абзацам
                improved = []
                for i, para in enumerate(paragraphs):
                    if i > 0 and i < len(paragraphs) - 1 and len(para) > 100:
                        # Извлекаем первое предложение как подзаголовок
                        sentences = para.split(". ")
                        if len(sentences) > 1:
                            subheading = sentences[0].strip()
                            if len(subheading) < 100:
                                improved.append(f"## {subheading}")
                                improved.append(". ".join(sentences[1:]))
                                continue
                    improved.append(para)
                return "\n\n".join(improved)
        
        return text
    
    def regenerate_content(self, content_id: int, changes: Dict[str, Any] = None) -> Dict[str, Any]:
        """Перегенерация контента с изменениями"""
        
        # Получаем существующий контент
        items = self.db.get_content_items()
        content_item = None
        for item in items:
            if item['id'] == content_id:
                content_item = item
                break
        
        if not content_item:
            raise ValueError(f"Контент с ID {content_id} не найден")
        
        # Получаем ТЗ
        specs = self.db.get_specs()
        spec = None
        for s in specs:
            if s['id'] == content_item['spec_id']:
                spec = s
                break
        
        if not spec:
            raise ValueError("ТЗ не найдено")
        
        # Применяем изменения к промпту
        if changes:
            # Модифицируем промпт в соответствии с изменениями
            pass
        
        # Регенерируем контент
        plan_items = self.db.get_content_plan()
        plan_item = None
        for item in plan_items:
            if item['id'] == spec['plan_id']:
                plan_item = item
                break
        
        format_type = plan_item['format'] if plan_item else content_item['format']
        
        if format_type == "article":
            new_content = self._generate_article(spec)
        elif format_type == "post":
            new_content = self._generate_post(spec)
        else:
            new_content = self._generate_generic(spec)
        
        # Обновляем контент в БД
        # (В реальности нужен метод update_content в db)
        
        return new_content
