"""
Модуль дистрибуции контента (Шаг 6: Цех дистрибуции)
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

try:
    from content_factory.config.database import db
    from content_factory.config.settings import settings
except ImportError:
    from config.database import db
    from config.settings import settings


class ContentDistributor:
    """Класс для дистрибуции контента"""
    
    def __init__(self):
        self.db = db
    
    def publish_content(self, content_id: int, platform: str,
                        publish_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Публикация контента на платформе
        
        Args:
            content_id: ID контента
            platform: Платформа (website, telegram, vk, etc.)
            publish_date: Дата публикации (если None - публикуем сейчас)
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
        
        # Проверяем статус
        if content_item['status'] != "approved":
            raise ValueError(f"Контент не одобрен для публикации (статус: {content_item['status']})")
        
        # Определяем метод публикации
        if platform == "website":
            result = self._publish_to_website(content_item)
        elif platform == "telegram":
            result = self._publish_to_telegram(content_item)
        elif platform in ["vk", "ok"]:
            result = self._publish_to_social(content_item, platform)
        else:
            result = self._publish_generic(content_item, platform)
        
        # Сохраняем информацию о публикации
        publication_id = self._save_publication(
            content_id=content_id,
            platform=platform,
            url=result.get('url', ''),
            published_at=publish_date or datetime.now(),
            status="published" if result.get('success') else "failed",
            metadata=result
        )
        
        # Обновляем статус контента
        if result.get('success'):
            self.db.update_content_status(content_id, "published")
        
        return {
            "publication_id": publication_id,
            "success": result.get('success', False),
            "url": result.get('url', ''),
            "platform": platform
        }
    
    def _publish_to_website(self, content_item: Dict) -> Dict[str, Any]:
        """Публикация на сайте (заглушка)"""
        # В реальности здесь будет интеграция с CMS (WordPress, etc.)
        url = f"https://example.com/content/{content_item['id']}"
        
        return {
            "success": True,
            "url": url,
            "method": "cms_api"
        }
    
    def _publish_to_telegram(self, content_item: Dict) -> Dict[str, Any]:
        """Публикация в Telegram (заглушка)"""
        # В реальности здесь будет интеграция с Telegram Bot API
        # Используем существующий telegram_bot.py если доступен
        
        return {
            "success": True,
            "url": f"t.me/channel/{content_item['id']}",
            "method": "telegram_bot"
        }
    
    def _publish_to_social(self, content_item: Dict, platform: str) -> Dict[str, Any]:
        """Публикация в соцсети (заглушка)"""
        # В реальности здесь будет интеграция с API соцсетей
        
        return {
            "success": True,
            "url": f"{platform}.com/post/{content_item['id']}",
            "method": f"{platform}_api"
        }
    
    def _publish_generic(self, content_item: Dict, platform: str) -> Dict[str, Any]:
        """Универсальная публикация"""
        return {
            "success": False,
            "error": f"Платформа {platform} не поддерживается",
            "method": "generic"
        }
    
    def _save_publication(self, content_id: int, platform: str, url: str,
                         published_at: datetime, status: str,
                         metadata: Dict) -> int:
        """Сохранение информации о публикации в БД"""
        # В реальности здесь будет запись в таблицу publications
        # Пока возвращаем заглушку
        return hash(f"{content_id}_{platform}_{published_at}") % 1000000
    
    def schedule_publication(self, content_id: int, platform: str,
                           publish_date: datetime) -> Dict[str, Any]:
        """Планирование публикации на будущее"""
        # Сохраняем в очередь публикаций
        # В реальности здесь будет использование планировщика задач (Celery, etc.)
        
        return {
            "success": True,
            "scheduled_for": publish_date.isoformat(),
            "platform": platform,
            "content_id": content_id
        }
    
    def repackage_content(self, content_id: int, target_format: str) -> Dict[str, Any]:
        """
        Переупаковка контента в другой формат
        
        Args:
            content_id: ID исходного контента
            target_format: Целевой формат (post, infographic, video_script)
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
        
        original_text = content_item['content']
        
        # Переупаковываем в зависимости от формата
        if target_format == "post":
            repackaged = self._convert_to_post(original_text)
        elif target_format == "infographic":
            repackaged = self._convert_to_infographic(original_text)
        elif target_format == "video_script":
            repackaged = self._convert_to_video_script(original_text)
        else:
            raise ValueError(f"Формат {target_format} не поддерживается")
        
        return {
            "original_content_id": content_id,
            "target_format": target_format,
            "content": repackaged
        }
    
    def _convert_to_post(self, text: str) -> str:
        """Конвертация в пост для соцсетей"""
        # Извлекаем основные тезисы
        paragraphs = text.split("\n\n")
        main_points = []
        
        for para in paragraphs[:5]:
            if len(para) > 50:
                # Берем первое предложение
                sentences = para.split(". ")
                if sentences:
                    main_points.append(sentences[0])
        
        # Формируем пост
        post = f"📌 {main_points[0] if main_points else 'Новая статья!'}\n\n"
        
        for i, point in enumerate(main_points[1:4], 1):
            post += f"{i}. {point}\n"
        
        post += "\n👉 Читайте полную версию по ссылке в описании!"
        
        return post
    
    def _convert_to_infographic(self, text: str) -> Dict[str, Any]:
        """Конвертация в инфографику (структура данных)"""
        # Извлекаем ключевые факты
        paragraphs = text.split("\n\n")
        facts = []
        
        for para in paragraphs:
            # Ищем предложения с числами или списки
            if any(char.isdigit() for char in para):
                sentences = para.split(". ")
                for sent in sentences:
                    if any(char.isdigit() for char in sent) and len(sent) < 150:
                        facts.append(sent.strip())
        
        return {
            "title": text.split("\n")[0] if text else "Инфографика",
            "facts": facts[:10],
            "format": "infographic"
        }
    
    def _convert_to_video_script(self, text: str) -> str:
        """Конвертация в сценарий видео"""
        paragraphs = text.split("\n\n")
        
        script = "СЦЕНАРИЙ ВИДЕО\n"
        script += "=" * 50 + "\n\n"
        
        script += "[ХУК - 15 секунд]\n"
        if paragraphs:
            script += f"{paragraphs[0][:200]}...\n\n"
        
        script += "[ВСТУПЛЕНИЕ - 30 секунд]\n"
        script += "Сегодня мы поговорим о...\n\n"
        
        script += "[ОСНОВНАЯ ЧАСТЬ - 5-8 минут]\n"
        for i, para in enumerate(paragraphs[1:6], 1):
            script += f"{i}. {para[:300]}...\n\n"
        
        script += "[ЗАКЛЮЧЕНИЕ - 30 секунд]\n"
        if paragraphs:
            script += f"{paragraphs[-1][:200]}...\n\n"
        
        script += "[ПРИЗЫВ К ДЕЙСТВИЮ]\n"
        script += "Подписывайтесь на канал и ставьте лайки!"
        
        return script
    
    def get_publications(self, content_id: int = None,
                        platform: str = None) -> List[Dict[str, Any]]:
        """Получение списка публикаций"""
        # В реальности здесь будет запрос к БД
        # Пока возвращаем заглушку
        return []
