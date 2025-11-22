"""
Модуль упаковки контента (Шаг 5: Цех упаковки)
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from content_factory.config.database import db
from content_factory.config.settings import settings

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class ContentPackager:
    """Класс для упаковки контента (дизайн, обложки, иллюстрации)"""
    
    def __init__(self):
        self.db = db
        self.output_dir = Path(settings.OUTPUT_DIR) / "design"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_cover(self, content_id: int, title: str, 
                    style: str = "modern") -> Dict[str, Any]:
        """
        Создание обложки для контента
        
        Args:
            content_id: ID контента
            title: Заголовок
            style: Стиль обложки
        """
        # Генерируем обложку
        if PILLOW_AVAILABLE:
            cover_path = self._generate_cover_image(title, style, content_id)
        else:
            # Fallback - создаем текстовый файл с описанием
            cover_path = self._create_cover_description(title, style, content_id)
        
        # Сохраняем в БД
        asset_id = self._save_design_asset(
            content_id=content_id,
            asset_type="cover",
            file_path=str(cover_path),
            metadata={"style": style, "title": title}
        )
        
        return {
            "asset_id": asset_id,
            "file_path": str(cover_path),
            "type": "cover"
        }
    
    def _generate_cover_image(self, title: str, style: str, content_id: int) -> Path:
        """Генерация изображения обложки"""
        # Размеры обложки
        width, height = 1200, 630  # Стандартный размер для соцсетей
        
        # Создаем изображение
        img = Image.new('RGB', (width, height), color='#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        # Пытаемся загрузить шрифт
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Рисуем заголовок
        # Разбиваем заголовок на строки
        words = title.split()
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            bbox = draw.textbbox((0, 0), ' '.join(current_line + [word]), font=font_large)
            word_width = bbox[2] - bbox[0]
            
            if current_width + word_width < width - 100:
                current_line.append(word)
                current_width += word_width + 20
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Рисуем текст
        y_offset = (height - len(lines) * 60) // 2
        for i, line in enumerate(lines[:3]):  # Максимум 3 строки
            bbox = draw.textbbox((0, 0), line, font=font_large)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = y_offset + i * 60
            
            # Тень
            draw.text((x + 2, y + 2), line, font=font_large, fill='#000000')
            # Основной текст
            draw.text((x, y), line, font=font_large, fill='#ffffff')
        
        # Сохраняем
        cover_path = self.output_dir / f"cover_{content_id}.png"
        img.save(cover_path)
        
        return cover_path
    
    def _create_cover_description(self, title: str, style: str, content_id: int) -> Path:
        """Создание текстового описания обложки (fallback)"""
        cover_path = self.output_dir / f"cover_{content_id}.txt"
        with open(cover_path, 'w', encoding='utf-8') as f:
            f.write(f"Обложка для: {title}\n")
            f.write(f"Стиль: {style}\n")
            f.write(f"Размер: 1200x630px\n")
            f.write(f"Цвета: Темный фон, белый текст\n")
        return cover_path
    
    def create_infographic(self, content_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание инфографики"""
        # Упрощенная версия - создаем текстовое описание
        infographic_path = self.output_dir / f"infographic_{content_id}.txt"
        
        with open(infographic_path, 'w', encoding='utf-8') as f:
            f.write("Инфографика\n")
            f.write("=" * 50 + "\n\n")
            for key, value in data.items():
                f.write(f"{key}: {value}\n")
        
        asset_id = self._save_design_asset(
            content_id=content_id,
            asset_type="infographic",
            file_path=str(infographic_path),
            metadata=data
        )
        
        return {
            "asset_id": asset_id,
            "file_path": str(infographic_path),
            "type": "infographic"
        }
    
    def create_illustration(self, content_id: int, prompt: str,
                           style: str = "realistic") -> Dict[str, Any]:
        """Создание иллюстрации с помощью AI"""
        # В реальности здесь будет генерация через Stable Diffusion или DALL-E
        # Пока создаем описание
        
        illustration_path = self.output_dir / f"illustration_{content_id}.txt"
        
        with open(illustration_path, 'w', encoding='utf-8') as f:
            f.write(f"Иллюстрация\n")
            f.write(f"Промпт: {prompt}\n")
            f.write(f"Стиль: {style}\n")
            f.write(f"Размер: 1024x1024px\n")
        
        asset_id = self._save_design_asset(
            content_id=content_id,
            asset_type="illustration",
            file_path=str(illustration_path),
            metadata={"prompt": prompt, "style": style}
        )
        
        return {
            "asset_id": asset_id,
            "file_path": str(illustration_path),
            "type": "illustration"
        }
    
    def _save_design_asset(self, content_id: int, asset_type: str,
                          file_path: str, metadata: Dict) -> int:
        """Сохранение информации об ассете в БД"""
        # В реальности здесь будет запись в таблицу design_assets
        # Пока возвращаем заглушку
        return hash(f"{content_id}_{asset_type}_{file_path}") % 1000000
    
    def get_design_assets(self, content_id: int) -> List[Dict[str, Any]]:
        """Получение всех дизайн-ассетов для контента"""
        # В реальности здесь будет запрос к БД
        # Пока возвращаем пустой список
        return []
    
    def create_social_media_images(self, content_id: int, 
                                   platforms: List[str] = None) -> Dict[str, Any]:
        """Создание изображений для соцсетей"""
        platforms = platforms or ["telegram", "vk", "ok"]
        
        # Получаем контент
        items = self.db.get_content_items()
        content_item = None
        for item in items:
            if item['id'] == content_id:
                content_item = item
                break
        
        if not content_item:
            raise ValueError(f"Контент с ID {content_id} не найден")
        
        title = content_item['title']
        assets = {}
        
        for platform in platforms:
            # Размеры для разных платформ
            sizes = {
                "telegram": (1200, 630),
                "vk": (1200, 630),
                "ok": (1200, 630),
                "instagram": (1080, 1080)
            }
            
            size = sizes.get(platform, (1200, 630))
            
            if PILLOW_AVAILABLE:
                asset_path = self._generate_social_image(title, size, content_id, platform)
            else:
                asset_path = self._create_social_description(title, size, content_id, platform)
            
            assets[platform] = str(asset_path)
        
        return {
            "content_id": content_id,
            "assets": assets
        }
    
    def _generate_social_image(self, title: str, size: tuple, 
                               content_id: int, platform: str) -> Path:
        """Генерация изображения для соцсети"""
        width, height = size
        
        img = Image.new('RGB', (width, height), color='#2c3e50')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        except:
            font = ImageFont.load_default()
        
        # Рисуем заголовок
        words = title.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] < width - 100:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        y_offset = (height - len(lines) * 50) // 2
        for i, line in enumerate(lines[:3]):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = y_offset + i * 50
            draw.text((x, y), line, font=font, fill='#ffffff')
        
        asset_path = self.output_dir / f"social_{platform}_{content_id}.png"
        img.save(asset_path)
        
        return asset_path
    
    def _create_social_description(self, title: str, size: tuple,
                                   content_id: int, platform: str) -> Path:
        """Создание описания для соцсети (fallback)"""
        asset_path = self.output_dir / f"social_{platform}_{content_id}.txt"
        with open(asset_path, 'w', encoding='utf-8') as f:
            f.write(f"Изображение для {platform}\n")
            f.write(f"Заголовок: {title}\n")
            f.write(f"Размер: {size[0]}x{size[1]}px\n")
        return asset_path
