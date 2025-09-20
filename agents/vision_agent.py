"""
VisionAgent - анализ изображений с помощью BLIP2 (CPU-only)
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import torch
from transformers import Blip2Processor, Blip2ForConditionalGeneration
from PIL import Image
import requests
from .base_agent import BaseAgent, Task


class VisionAgent(BaseAgent):
    """Агент для анализа изображений"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("vision_agent", config)
        self.model_path = config.get('models_path', '/app/models')
        self.model_name = "Salesforce/blip2-opt-2.7b"
        self.processor: Optional[Blip2Processor] = None
        self.model: Optional[Blip2ForConditionalGeneration] = None
        self.device = "cpu"  # CPU-only
        
    async def _initialize_agent(self):
        """Инициализация VisionAgent"""
        self.logger.info("Инициализация VisionAgent")
        
        # Загрузка модели BLIP2
        await self._load_model()
        
        self.logger.info("VisionAgent успешно инициализирован")
    
    async def _load_model(self):
        """Загрузка модели BLIP2"""
        try:
            model_file = os.path.join(self.model_path, "blip2")
            
            self.logger.info(f"Загрузка BLIP2 из {model_file}")
            
            # Загрузка процессора
            self.processor = Blip2Processor.from_pretrained(
                model_file if os.path.exists(model_file) else self.model_name
            )
            
            # Загрузка модели
            self.model = Blip2ForConditionalGeneration.from_pretrained(
                model_file if os.path.exists(model_file) else self.model_name,
                torch_dtype=torch.float32,  # CPU совместимость
                device_map="cpu"
            )
            
            self.logger.info("BLIP2 загружен успешно")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {e}")
            raise
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задач анализа изображений"""
        if task.task_type == "image_captioning":
            return await self._caption_image(task)
        elif task.task_type == "visual_question_answering":
            return await self._answer_visual_question(task)
        elif task.task_type == "image_classification":
            return await self._classify_image(task)
        elif task.task_type == "object_detection":
            return await self._detect_objects(task)
        
        return {"status": "unknown_task_type"}
    
    async def _caption_image(self, task: Task) -> Dict[str, Any]:
        """Генерация описания изображения"""
        try:
            image_path = task.data.get("image_path")
            image_url = task.data.get("image_url")
            
            # Загрузка изображения
            image = await self._load_image(image_path, image_url)
            if not image:
                return {"status": "error", "error": "Не удалось загрузить изображение"}
            
            self.logger.info("Генерация описания изображения")
            
            # Обработка изображения
            inputs = self.processor(images=image, return_tensors="pt")
            
            # Генерация описания
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=100,
                    num_beams=4,
                    early_stopping=True
                )
            
            # Декодирование результата
            generated_text = self.processor.batch_decode(
                generated_ids, 
                skip_special_tokens=True
            )[0].strip()
            
            return {
                "status": "success",
                "caption": generated_text,
                "image_path": image_path,
                "image_url": image_url,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "model": "BLIP2"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации описания: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _answer_visual_question(self, task: Task) -> Dict[str, Any]:
        """Ответ на вопрос об изображении"""
        try:
            image_path = task.data.get("image_path")
            image_url = task.data.get("image_url")
            question = task.data.get("question", "")
            
            if not question:
                return {"status": "error", "error": "Вопрос не указан"}
            
            # Загрузка изображения
            image = await self._load_image(image_path, image_url)
            if not image:
                return {"status": "error", "error": "Не удалось загрузить изображение"}
            
            self.logger.info(f"Ответ на вопрос: {question}")
            
            # Обработка изображения и вопроса
            inputs = self.processor(
                images=image,
                text=question,
                return_tensors="pt"
            )
            
            # Генерация ответа
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=50,
                    num_beams=4,
                    early_stopping=True
                )
            
            # Декодирование результата
            answer = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=True
            )[0].strip()
            
            return {
                "status": "success",
                "question": question,
                "answer": answer,
                "image_path": image_path,
                "image_url": image_url,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "model": "BLIP2"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка ответа на вопрос: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _classify_image(self, task: Task) -> Dict[str, Any]:
        """Классификация изображения"""
        try:
            image_path = task.data.get("image_path")
            image_url = task.data.get("image_url")
            categories = task.data.get("categories", [
                "person", "animal", "vehicle", "building", "nature", "food", "object"
            ])
            
            # Загрузка изображения
            image = await self._load_image(image_path, image_url)
            if not image:
                return {"status": "error", "error": "Не удалось загрузить изображение"}
            
            self.logger.info("Классификация изображения")
            
            # Генерация описания для классификации
            caption_result = await self._caption_image(task)
            if caption_result["status"] != "success":
                return caption_result
            
            caption = caption_result["caption"].lower()
            
            # Простая классификация на основе ключевых слов
            category_scores = {}
            for category in categories:
                score = 0
                category_keywords = {
                    "person": ["человек", "люди", "лицо", "портрет", "man", "woman", "person"],
                    "animal": ["животное", "собака", "кошка", "птица", "animal", "dog", "cat", "bird"],
                    "vehicle": ["машина", "автомобиль", "грузовик", "vehicle", "car", "truck"],
                    "building": ["здание", "дом", "строение", "building", "house", "structure"],
                    "nature": ["природа", "дерево", "лес", "море", "nature", "tree", "forest", "sea"],
                    "food": ["еда", "пища", "фрукт", "food", "fruit", "meal"],
                    "object": ["объект", "предмет", "вещь", "object", "item", "thing"]
                }
                
                keywords = category_keywords.get(category, [category])
                for keyword in keywords:
                    if keyword in caption:
                        score += 1
                
                category_scores[category] = score
            
            # Определение лучшей категории
            best_category = max(category_scores, key=category_scores.get)
            confidence = category_scores[best_category] / max(sum(category_scores.values()), 1)
            
            return {
                "status": "success",
                "category": best_category,
                "confidence": confidence,
                "all_scores": category_scores,
                "caption": caption_result["caption"],
                "image_path": image_path,
                "image_url": image_url,
                "metadata": {
                    "classified_at": datetime.now().isoformat(),
                    "model": "BLIP2"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка классификации: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _detect_objects(self, task: Task) -> Dict[str, Any]:
        """Обнаружение объектов на изображении"""
        try:
            image_path = task.data.get("image_path")
            image_url = task.data.get("image_url")
            
            # Загрузка изображения
            image = await self._load_image(image_path, image_url)
            if not image:
                return {"status": "error", "error": "Не удалось загрузить изображение"}
            
            self.logger.info("Обнаружение объектов на изображении")
            
            # Генерация подробного описания
            caption_result = await self._caption_image(task)
            if caption_result["status"] != "success":
                return caption_result
            
            caption = caption_result["caption"]
            
            # Простое извлечение объектов из описания
            objects = []
            common_objects = [
                "человек", "люди", "лицо", "рука", "нога", "голова",
                "машина", "автомобиль", "грузовик", "автобус",
                "собака", "кошка", "птица", "животное",
                "дерево", "дом", "здание", "дорога", "небо",
                "стол", "стул", "книга", "телефон", "компьютер"
            ]
            
            caption_lower = caption.lower()
            for obj in common_objects:
                if obj in caption_lower:
                    objects.append({
                        "name": obj,
                        "confidence": 0.8,  # Примерная уверенность
                        "position": "unknown"  # BLIP2 не дает позиции
                    })
            
            return {
                "status": "success",
                "objects": objects,
                "object_count": len(objects),
                "caption": caption,
                "image_path": image_path,
                "image_url": image_url,
                "metadata": {
                    "detected_at": datetime.now().isoformat(),
                    "model": "BLIP2"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка обнаружения объектов: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _load_image(self, image_path: str = None, image_url: str = None) -> Optional[Image.Image]:
        """Загрузка изображения"""
        try:
            if image_path and os.path.exists(image_path):
                return Image.open(image_path)
            elif image_url:
                response = requests.get(image_url)
                if response.status_code == 200:
                    return Image.open(requests.get(image_url, stream=True).raw)
            else:
                self.logger.error("Не указан путь или URL изображения")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка загрузки изображения: {e}")
            return None
    
    async def _cleanup_agent(self):
        """Очистка ресурсов VisionAgent"""
        if self.model:
            del self.model
        if self.processor:
            del self.processor
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        self.logger.info("VisionAgent очищен")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о модели"""
        return {
            "model_name": "BLIP2",
            "device": self.device,
            "loaded": self.model is not None,
            "processor_loaded": self.processor is not None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья агента"""
        return {
            "status": "healthy" if self.model is not None else "error",
            "model_loaded": self.model is not None,
            "processor_loaded": self.processor is not None,
            "device": self.device
        }

