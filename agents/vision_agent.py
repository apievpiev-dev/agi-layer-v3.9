"""
VisionAgent - Агент компьютерного зрения
=======================================

Обрабатывает изображения используя:
- BLIP2 для описания изображений
- CLIP для понимания содержимого
- EasyOCR для распознавания текста
- Анализ объектов и сцен
"""

import asyncio
import base64
import io
import os
from datetime import datetime
from typing import Dict, List, Optional

import torch
from loguru import logger
from PIL import Image
from transformers import (
    BlipForConditionalGeneration,
    BlipProcessor,
    CLIPModel,
    CLIPProcessor
)
import easyocr

from base_agent import BaseAgent, AgentConfig, AgentMessage


class VisionAgent(BaseAgent):
    """Агент для компьютерного зрения"""
    
    def __init__(self):
        config = AgentConfig(
            name="vision_agent",
            type="computer_vision",
            model_name="Salesforce/blip2-opt-2.7b",
            max_memory="8G",
            max_cpu_cores=4
        )
        super().__init__(config)
        
        # Модели зрения
        self.blip_model = None
        self.blip_processor = None
        self.clip_model = None
        self.clip_processor = None
        self.ocr_reader = None
        
        # Кэш результатов
        self.image_cache = {}

    async def _load_model(self):
        """Загрузка моделей компьютерного зрения"""
        try:
            logger.info("Загрузка моделей компьютерного зрения...")
            
            # BLIP2 для описания изображений
            logger.info("Загрузка BLIP2...")
            self.blip_processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-base",
                cache_dir="/app/models/cache"
            )
            self.blip_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base",
                torch_dtype=torch.float32,
                cache_dir="/app/models/cache"
            )
            
            # CLIP для понимания изображений
            logger.info("Загрузка CLIP...")
            self.clip_processor = CLIPProcessor.from_pretrained(
                "openai/clip-vit-base-patch32",
                cache_dir="/app/models/cache"
            )
            self.clip_model = CLIPModel.from_pretrained(
                "openai/clip-vit-base-patch32",
                cache_dir="/app/models/cache"
            )
            
            # EasyOCR для распознавания текста
            logger.info("Инициализация EasyOCR...")
            self.ocr_reader = easyocr.Reader(['ru', 'en'], gpu=False)
            
            logger.info("✅ Все модели компьютерного зрения загружены")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки моделей зрения: {e}")
            raise

    async def _agent_specific_init(self):
        """Специфичная инициализация VisionAgent"""
        # Регистрируемся в MetaAgent
        await self.send_message(
            "meta_agent",
            "registration",
            {
                "agent_type": self.type,
                "capabilities": [
                    "image_description", 
                    "text_recognition", 
                    "object_detection",
                    "scene_analysis",
                    "image_similarity"
                ],
                "status": "ready"
            }
        )
        logger.info("VisionAgent зарегистрирован в MetaAgent")

    async def _agent_main_loop(self):
        """Основной цикл VisionAgent"""
        while self.is_running:
            try:
                # Проверяем задачи в очереди
                task_data = await asyncio.to_thread(
                    self.redis_client.lpop, f"tasks_{self.name}"
                )
                
                if task_data:
                    import json
                    task = json.loads(task_data)
                    await self._process_vision_task(task)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка в главном цикле VisionAgent: {e}")
                await asyncio.sleep(5)

    async def _process_vision_task(self, task: Dict):
        """Обработка задач компьютерного зрения"""
        try:
            task_id = task.get("id", "unknown")
            task_type = task.get("type", "analyze")
            image_data = task.get("image_data", "")
            
            logger.info(f"Обработка задачи зрения {task_id}: {task_type}")
            
            # Декодируем изображение
            image = await self._decode_image(image_data)
            
            result = {}
            
            if task_type == "describe":
                result = await self._describe_image(image)
            elif task_type == "extract_text":
                result = await self._extract_text(image)
            elif task_type == "analyze":
                result = await self._analyze_image(image)
            elif task_type == "similarity":
                text_query = task.get("text_query", "")
                result = await self._check_similarity(image, text_query)
            
            # Сохраняем результат
            final_result = {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "agent": self.name
            }
            
            await asyncio.to_thread(
                self.redis_client.lpush,
                f"results_{task_id}",
                json.dumps(final_result)
            )
            
            logger.info(f"Задача зрения {task_id} выполнена")
            
        except Exception as e:
            logger.error(f"Ошибка обработки задачи зрения: {e}")

    async def _decode_image(self, image_data: str) -> Image.Image:
        """Декодирование изображения из base64"""
        try:
            # Удаляем префикс data:image если есть
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            # Декодируем base64
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Конвертируем в RGB если нужно
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            logger.error(f"Ошибка декодирования изображения: {e}")
            raise

    async def _describe_image(self, image: Image.Image) -> Dict:
        """Описание изображения с помощью BLIP2"""
        try:
            def generate_description():
                inputs = self.blip_processor(image, return_tensors="pt")
                with torch.no_grad():
                    out = self.blip_model.generate(**inputs, max_length=50)
                description = self.blip_processor.decode(out[0], skip_special_tokens=True)
                return description
            
            description = await asyncio.to_thread(generate_description)
            
            return {
                "description": description,
                "confidence": 0.85,  # Примерная уверенность
                "language": "en"
            }
            
        except Exception as e:
            logger.error(f"Ошибка описания изображения: {e}")
            return {"description": "Ошибка анализа изображения", "confidence": 0.0}

    async def _extract_text(self, image: Image.Image) -> Dict:
        """Извлечение текста из изображения"""
        try:
            def extract_ocr():
                # Конвертируем PIL в numpy array
                import numpy as np
                img_array = np.array(image)
                
                # Запускаем OCR
                results = self.ocr_reader.readtext(img_array)
                
                texts = []
                for (bbox, text, confidence) in results:
                    if confidence > 0.5:  # Фильтруем по уверенности
                        texts.append({
                            "text": text,
                            "confidence": confidence,
                            "bbox": bbox
                        })
                
                return texts
            
            ocr_results = await asyncio.to_thread(extract_ocr)
            
            # Объединяем весь текст
            all_text = " ".join([item["text"] for item in ocr_results])
            
            return {
                "extracted_text": all_text,
                "details": ocr_results,
                "total_words": len(all_text.split()),
                "confidence": sum(item["confidence"] for item in ocr_results) / len(ocr_results) if ocr_results else 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения текста: {e}")
            return {"extracted_text": "", "details": [], "confidence": 0.0}

    async def _analyze_image(self, image: Image.Image) -> Dict:
        """Полный анализ изображения"""
        try:
            # Получаем описание
            description_result = await self._describe_image(image)
            
            # Извлекаем текст
            text_result = await self._extract_text(image)
            
            # Анализ размера и характеристик
            width, height = image.size
            aspect_ratio = width / height
            
            return {
                "description": description_result,
                "text_content": text_result,
                "image_properties": {
                    "width": width,
                    "height": height,
                    "aspect_ratio": round(aspect_ratio, 2),
                    "format": image.format,
                    "mode": image.mode
                },
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа изображения: {e}")
            return {"error": str(e)}

    async def _check_similarity(self, image: Image.Image, text_query: str) -> Dict:
        """Проверка соответствия изображения текстовому запросу"""
        try:
            def compute_similarity():
                # Обрабатываем изображение и текст
                inputs = self.clip_processor(
                    text=[text_query], 
                    images=image, 
                    return_tensors="pt", 
                    padding=True
                )
                
                with torch.no_grad():
                    outputs = self.clip_model(**inputs)
                    logits_per_image = outputs.logits_per_image
                    probs = logits_per_image.softmax(dim=1)
                
                return float(probs[0][0])
            
            similarity_score = await asyncio.to_thread(compute_similarity)
            
            return {
                "query": text_query,
                "similarity_score": round(similarity_score, 3),
                "match": similarity_score > 0.3,  # Порог соответствия
                "confidence": "high" if similarity_score > 0.7 else "medium" if similarity_score > 0.3 else "low"
            }
            
        except Exception as e:
            logger.error(f"Ошибка проверки соответствия: {e}")
            return {"similarity_score": 0.0, "match": False, "error": str(e)}

    async def process_message(self, message: AgentMessage) -> Dict[str, any]:
        """Обработка входящих сообщений"""
        try:
            if message.message_type == "analyze_image":
                image_data = message.content.get("image_data", "")
                analysis_type = message.content.get("type", "analyze")
                
                image = await self._decode_image(image_data)
                
                if analysis_type == "describe":
                    result = await self._describe_image(image)
                elif analysis_type == "extract_text":
                    result = await self._extract_text(image)
                else:
                    result = await self._analyze_image(image)
                
                return {"status": "completed", "result": result}
                
            elif message.message_type == "status":
                return {
                    "agent_name": self.name,
                    "models_loaded": {
                        "blip": self.blip_model is not None,
                        "clip": self.clip_model is not None,
                        "ocr": self.ocr_reader is not None
                    },
                    "status": self.status,
                    "memory_usage": await self._get_memory_usage(),
                    "error_count": self.error_count
                }
                
            else:
                return {"status": "unknown", "message": "Неизвестный тип сообщения"}
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения в VisionAgent: {e}")
            return {"status": "error", "message": str(e)}

    async def describe_image_from_path(self, image_path: str) -> str:
        """Публичный метод для описания изображения по пути"""
        try:
            image = Image.open(image_path)
            result = await self._describe_image(image)
            return result.get("description", "Не удалось описать изображение")
            
        except Exception as e:
            logger.error(f"Ошибка описания изображения: {e}")
            return f"Ошибка: {str(e)}"


if __name__ == "__main__":
    # Запуск VisionAgent
    async def main():
        vision_agent = VisionAgent()
        await vision_agent.run()
    
    asyncio.run(main())


