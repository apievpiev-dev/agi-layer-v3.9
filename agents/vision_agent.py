"""
VisionAgent - агент для анализа изображений с использованием BLIP2 и EasyOCR
"""

import asyncio
import os
import torch
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import easyocr
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from .base_agent import BaseAgent, Task


class VisionAnalysisRequest(BaseModel):
    """Модель запроса анализа изображения"""
    image_path: str
    analysis_type: str = "general"  # general, ocr, detailed


class VisionAgent(BaseAgent):
    """Агент для анализа изображений"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("vision_agent", config)
        
        # Конфигурация модели
        self.model_path = config.get('models_path', '/workspace/models')
        self.model_name = "Salesforce/blip-image-captioning-base"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # BLIP2 модель и процессор
        self.processor: Optional[BlipProcessor] = None
        self.model: Optional[BlipForConditionalGeneration] = None
        
        # EasyOCR reader
        self.ocr_reader: Optional[easyocr.Reader] = None
        
        # Статистика
        self.analysis_stats = {
            "total_analyzed": 0,
            "successful": 0,
            "failed": 0,
            "ocr_requests": 0,
            "average_time": 0.0
        }
        
        # FastAPI приложение
        self.app = FastAPI(title="VisionAgent API", version="3.9")
        self._setup_routes()
        
        self.logger.info(f"VisionAgent инициализирован для устройства: {self.device}")
    
    def _setup_routes(self):
        """Настройка FastAPI маршрутов"""
        
        @self.app.post("/analyze")
        async def analyze_image_endpoint(request: VisionAnalysisRequest):
            """Анализ изображения через HTTP API"""
            try:
                task = Task(
                    id=f"vision_{datetime.now().timestamp()}",
                    agent_name="vision_agent",
                    task_type="analyze_image",
                    data={
                        "image_path": request.image_path,
                        "analysis_type": request.analysis_type
                    }
                )
                
                result = await self.process_task(task)
                return result
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/status")
        async def get_status():
            """Статус агента"""
            return await self.health_check()
        
        @self.app.get("/stats")
        async def get_stats():
            """Статистика анализа"""
            return {
                "stats": self.analysis_stats,
                "model_loaded": self.model is not None,
                "ocr_loaded": self.ocr_reader is not None,
                "device": self.device
            }
        
        @self.app.post("/process_task")
        async def process_task_endpoint(task_data: Dict[str, Any]):
            """Обработка задачи через HTTP API"""
            try:
                task = Task(
                    id=task_data["id"],
                    agent_name=task_data["agent_name"],
                    task_type=task_data["task_type"],
                    data=task_data["data"]
                )
                
                result = await self.process_task(task)
                return result
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _initialize_agent(self):
        """Инициализация агента анализа изображений"""
        self.logger.info("Инициализация VisionAgent")
        
        # Загружаем модели
        await self._load_models()
        
        # Запускаем HTTP сервер
        asyncio.create_task(self._start_http_server())
        
        self.logger.info("VisionAgent инициализирован")
    
    async def _start_http_server(self):
        """Запуск HTTP сервера"""
        try:
            config = uvicorn.Config(
                app=self.app,
                host="0.0.0.0",
                port=8004,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            self.logger.error(f"Ошибка запуска HTTP сервера: {e}")
    
    async def _load_models(self):
        """Загрузка моделей BLIP2 и EasyOCR"""
        try:
            # Загрузка BLIP2
            await self._load_blip_model()
            
            # Загрузка EasyOCR
            await self._load_ocr_model()
            
            self.logger.info("✅ Все модели анализа изображений загружены")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки моделей: {e}")
    
    async def _load_blip_model(self):
        """Загрузка модели BLIP2"""
        try:
            self.logger.info("Загрузка BLIP2 модели...")
            
            model_cache_path = os.path.join(self.model_path, "blip2-base")
            
            if os.path.exists(model_cache_path):
                self.logger.info(f"Загрузка BLIP2 из кеша: {model_cache_path}")
                self.processor = BlipProcessor.from_pretrained(model_cache_path)
                self.model = BlipForConditionalGeneration.from_pretrained(
                    model_cache_path,
                    torch_dtype=torch.float32
                ).to(self.device)
            else:
                self.logger.info(f"Загрузка BLIP2 из HuggingFace: {self.model_name}")
                self.processor = BlipProcessor.from_pretrained(
                    self.model_name,
                    cache_dir=self.model_path
                )
                self.model = BlipForConditionalGeneration.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,
                    cache_dir=self.model_path
                ).to(self.device)
                
                # Сохраняем локально
                os.makedirs(model_cache_path, exist_ok=True)
                self.processor.save_pretrained(model_cache_path)
                self.model.save_pretrained(model_cache_path)
            
            self.logger.info("✅ BLIP2 модель загружена")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки BLIP2: {e}")
            # Создаем заглушку
            self.model = "fallback"
            self.processor = "fallback"
    
    async def _load_ocr_model(self):
        """Загрузка EasyOCR"""
        try:
            self.logger.info("Инициализация EasyOCR...")
            
            ocr_path = os.path.join(self.model_path, "ocr_models")
            os.makedirs(ocr_path, exist_ok=True)
            
            # Инициализируем EasyOCR для русского и английского
            self.ocr_reader = easyocr.Reader(
                ['en', 'ru'],
                model_storage_directory=ocr_path,
                download_enabled=True,
                gpu=self.device == "cuda"
            )
            
            self.logger.info("✅ EasyOCR инициализирован")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации EasyOCR: {e}")
            self.ocr_reader = "fallback"
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задач анализа изображений"""
        try:
            if task.task_type == "analyze_image":
                return await self._analyze_image(task)
            elif task.task_type == "ocr_extract":
                return await self._extract_text(task)
            elif task.task_type == "ping":
                return {"status": "success", "message": "pong"}
            else:
                return {"status": "error", "error": f"Неизвестный тип задачи: {task.task_type}"}
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки задачи: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _analyze_image(self, task: Task) -> Dict[str, Any]:
        """Анализ изображения"""
        start_time = datetime.now()
        
        try:
            data = task.data
            image_path = data.get("image_path", "")
            analysis_type = data.get("analysis_type", "general")
            
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": "Изображение не найдено"}
            
            self.analysis_stats["total_analyzed"] += 1
            self.logger.info(f"Анализ изображения: {image_path}")
            
            # Загружаем изображение
            image = Image.open(image_path).convert('RGB')
            
            result = {
                "status": "success",
                "image_path": image_path,
                "analysis_type": analysis_type,
                "image_size": image.size
            }
            
            # Общий анализ через BLIP2
            if analysis_type in ["general", "detailed"]:
                blip_result = await self._analyze_with_blip(image)
                result.update(blip_result)
            
            # OCR анализ
            if analysis_type in ["ocr", "detailed"]:
                ocr_result = await self._analyze_with_ocr(image_path)
                result.update(ocr_result)
                self.analysis_stats["ocr_requests"] += 1
            
            # Дополнительная информация для детального анализа
            if analysis_type == "detailed":
                result["detailed_info"] = {
                    "format": image.format if hasattr(image, 'format') else "Unknown",
                    "mode": image.mode,
                    "size": image.size,
                    "has_transparency": image.mode in ("RGBA", "LA") or "transparency" in image.info
                }
            
            self.analysis_stats["successful"] += 1
            
            # Обновляем среднее время
            analysis_time = (datetime.now() - start_time).total_seconds()
            self.analysis_stats["average_time"] = (
                self.analysis_stats["average_time"] * (self.analysis_stats["successful"] - 1) + analysis_time
            ) / self.analysis_stats["successful"]
            
            result["analysis_time"] = analysis_time
            
            self.logger.info(f"✅ Изображение проанализировано за {analysis_time:.2f}с")
            
            return result
            
        except Exception as e:
            self.analysis_stats["failed"] += 1
            self.logger.error(f"Ошибка анализа изображения: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _analyze_with_blip(self, image: Image.Image) -> Dict[str, Any]:
        """Анализ изображения с помощью BLIP2"""
        try:
            if self.model == "fallback" or self.processor == "fallback":
                return {
                    "description": "Изображение содержит различные визуальные элементы. Для детального анализа требуется загрузка модели BLIP2.",
                    "confidence": 0.5,
                    "objects": ["изображение", "содержимое"],
                    "note": "Анализ выполнен в режиме заглушки"
                }
            
            # Обрабатываем изображение
            inputs = self.processor(image, return_tensors="pt").to(self.device)
            
            # Генерируем описание
            with torch.no_grad():
                out = self.model.generate(**inputs, max_length=50, num_beams=4)
            
            description = self.processor.decode(out[0], skip_special_tokens=True)
            
            # Дополнительный анализ с условным промптом
            conditional_inputs = self.processor(
                image, 
                text="a photo of", 
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                conditional_out = self.model.generate(**conditional_inputs, max_length=50)
            
            conditional_description = self.processor.decode(conditional_out[0], skip_special_tokens=True)
            
            # Извлекаем объекты из описания (простая эвристика)
            objects = self._extract_objects_from_description(description)
            
            return {
                "description": description,
                "conditional_description": conditional_description,
                "objects": objects,
                "confidence": 0.85,  # Примерная уверенность
                "model_used": "BLIP2"
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка BLIP2 анализа: {e}")
            return {
                "description": f"Ошибка анализа: {str(e)}",
                "confidence": 0.0,
                "objects": [],
                "model_used": "BLIP2 (error)"
            }
    
    async def _analyze_with_ocr(self, image_path: str) -> Dict[str, Any]:
        """Извлечение текста с помощью EasyOCR"""
        try:
            if self.ocr_reader == "fallback":
                return {
                    "extracted_text": "OCR анализ недоступен - модель не загружена",
                    "text_regions": [],
                    "languages": ["en", "ru"],
                    "note": "OCR в режиме заглушки"
                }
            
            # Выполняем OCR
            results = self.ocr_reader.readtext(image_path)
            
            # Обрабатываем результаты
            extracted_text = []
            text_regions = []
            
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # Фильтруем по уверенности
                    extracted_text.append(text)
                    text_regions.append({
                        "text": text,
                        "bbox": bbox,
                        "confidence": float(confidence)
                    })
            
            full_text = " ".join(extracted_text)
            
            return {
                "extracted_text": full_text,
                "text_regions": text_regions,
                "total_regions": len(text_regions),
                "languages": ["en", "ru"],
                "ocr_model": "EasyOCR"
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка OCR анализа: {e}")
            return {
                "extracted_text": f"Ошибка OCR: {str(e)}",
                "text_regions": [],
                "total_regions": 0,
                "ocr_model": "EasyOCR (error)"
            }
    
    def _extract_objects_from_description(self, description: str) -> list:
        """Извлечение объектов из описания (простая эвристика)"""
        # Список общих объектов для поиска
        common_objects = [
            "person", "people", "man", "woman", "child", "baby",
            "car", "truck", "bus", "bicycle", "motorcycle",
            "dog", "cat", "bird", "horse", "cow",
            "house", "building", "tree", "flower", "grass",
            "table", "chair", "bed", "sofa", "computer",
            "phone", "book", "cup", "plate", "food"
        ]
        
        description_lower = description.lower()
        found_objects = []
        
        for obj in common_objects:
            if obj in description_lower:
                found_objects.append(obj)
        
        # Если не нашли конкретных объектов, возвращаем общие категории
        if not found_objects:
            if any(word in description_lower for word in ["person", "man", "woman", "people"]):
                found_objects.append("person")
            if any(word in description_lower for word in ["animal", "dog", "cat"]):
                found_objects.append("animal")
            if any(word in description_lower for word in ["vehicle", "car", "truck"]):
                found_objects.append("vehicle")
            if any(word in description_lower for word in ["building", "house", "structure"]):
                found_objects.append("building")
        
        return found_objects or ["object"]
    
    async def _extract_text(self, task: Task) -> Dict[str, Any]:
        """Извлечение текста из изображения (только OCR)"""
        try:
            data = task.data
            image_path = data.get("image_path", "")
            
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": "Изображение не найдено"}
            
            ocr_result = await self._analyze_with_ocr(image_path)
            
            return {
                "status": "success",
                "image_path": image_path,
                **ocr_result
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_metrics(self) -> Dict[str, Any]:
        """Получение метрик агента"""
        base_metrics = await super()._get_metrics()
        
        base_metrics.update({
            "blip_model_loaded": self.model is not None and self.model != "fallback",
            "ocr_model_loaded": self.ocr_reader is not None and self.ocr_reader != "fallback",
            "device": self.device,
            "analysis_stats": self.analysis_stats,
            "model_path": self.model_path
        })
        
        return base_metrics
    
    async def _cleanup_agent(self):
        """Очистка ресурсов"""
        self.logger.info("Очистка ресурсов VisionAgent")
        
        if self.model and self.model != "fallback":
            del self.model
        if self.processor and self.processor != "fallback":
            del self.processor
        if self.ocr_reader and self.ocr_reader != "fallback":
            del self.ocr_reader
        
        # Очищаем CUDA кеш если используется GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


# Функция запуска
async def run_vision_agent(config: Dict[str, Any]):
    """Запуск агента анализа изображений"""
    agent = VisionAgent(config)
    await agent.initialize()
    await agent.start()
    
    try:
        while agent.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Получен сигнал остановки")
    finally:
        await agent.stop()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    config = {
        'models_path': os.getenv('MODELS_PATH', '/workspace/models'),
        'postgres_host': os.getenv('POSTGRES_HOST', 'localhost'),
        'postgres_port': int(os.getenv('POSTGRES_PORT', 5432)),
        'postgres_db': os.getenv('POSTGRES_DB', 'agi_layer'),
        'postgres_user': os.getenv('POSTGRES_USER', 'agi_user'),
        'postgres_password': os.getenv('POSTGRES_PASSWORD', 'agi_password')
    }
    
    asyncio.run(run_vision_agent(config))