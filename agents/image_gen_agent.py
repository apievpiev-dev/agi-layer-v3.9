"""
ImageGenAgent - агент для генерации изображений с использованием Stable Diffusion
Оптимизирован для работы на CPU
"""

import asyncio
import os
import torch
from datetime import datetime
from typing import Dict, Any, Optional
from diffusers import StableDiffusionPipeline, DiffusionPipeline
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from .base_agent import BaseAgent, Task


class ImageGenerationRequest(BaseModel):
    """Модель запроса генерации изображения"""
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 512
    height: int = 512
    num_inference_steps: int = 50
    guidance_scale: float = 12.0
    seed: Optional[int] = None


class ImageGenAgent(BaseAgent):
    """Агент для генерации изображений"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("image_gen_agent", config)
        
        # Конфигурация модели
        self.model_path = config.get('models_path', '/workspace/models')
        self.model_name = "runwayml/stable-diffusion-v1-5"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Pipeline для генерации
        self.pipeline: Optional[StableDiffusionPipeline] = None
        
        # Настройки генерации
        self.default_settings = {
            "width": 512,
            "height": 512,
            "num_inference_steps": 50,
            "guidance_scale": 12.0,
            "negative_prompt": "low quality, blurry, distorted, ugly, bad anatomy, deformed, extra limbs"
        }
        
        # Статистика
        self.generation_stats = {
            "total_generated": 0,
            "successful": 0,
            "failed": 0,
            "average_time": 0.0
        }
        
        # FastAPI приложение
        self.app = FastAPI(title="ImageGenAgent API", version="3.9")
        self._setup_routes()
        
        self.logger.info(f"ImageGenAgent инициализирован для устройства: {self.device}")
    
    def _setup_routes(self):
        """Настройка FastAPI маршрутов"""
        
        @self.app.post("/generate")
        async def generate_image_endpoint(request: ImageGenerationRequest):
            """Генерация изображения через HTTP API"""
            try:
                task = Task(
                    id=f"img_gen_{datetime.now().timestamp()}",
                    agent_name="image_gen_agent",
                    task_type="generate_image",
                    data={
                        "prompt": request.prompt,
                        "negative_prompt": request.negative_prompt,
                        "width": request.width,
                        "height": request.height,
                        "num_inference_steps": request.num_inference_steps,
                        "guidance_scale": request.guidance_scale,
                        "seed": request.seed
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
            """Статистика генерации"""
            return {
                "stats": self.generation_stats,
                "model_loaded": self.pipeline is not None,
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
        """Инициализация агента генерации изображений"""
        self.logger.info("Инициализация ImageGenAgent")
        
        # Загружаем модель
        await self._load_model()
        
        # Запускаем HTTP сервер
        asyncio.create_task(self._start_http_server())
        
        self.logger.info("ImageGenAgent инициализирован")
    
    async def _start_http_server(self):
        """Запуск HTTP сервера"""
        try:
            config = uvicorn.Config(
                app=self.app,
                host="0.0.0.0",
                port=8003,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            self.logger.error(f"Ошибка запуска HTTP сервера: {e}")
    
    async def _load_model(self):
        """Загрузка модели Stable Diffusion"""
        try:
            self.logger.info("Загрузка Stable Diffusion модели...")
            
            # Определяем путь к модели
            model_cache_path = os.path.join(self.model_path, "stable-diffusion-v1-5")
            
            # Загружаем pipeline
            if os.path.exists(model_cache_path):
                self.logger.info(f"Загрузка модели из кеша: {model_cache_path}")
                self.pipeline = StableDiffusionPipeline.from_pretrained(
                    model_cache_path,
                    torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
                    safety_checker=None,
                    requires_safety_checker=False
                )
            else:
                self.logger.info(f"Загрузка модели из HuggingFace: {self.model_name}")
                self.pipeline = StableDiffusionPipeline.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
                    safety_checker=None,
                    requires_safety_checker=False,
                    cache_dir=self.model_path
                )
                
                # Сохраняем модель локально
                self.logger.info(f"Сохранение модели в кеш: {model_cache_path}")
                self.pipeline.save_pretrained(model_cache_path)
            
            # Настройки для CPU
            if self.device == "cpu":
                self.logger.info("Оптимизация для CPU...")
                self.pipeline.enable_attention_slicing()
                # Дополнительные оптимизации для CPU
                try:
                    self.pipeline.enable_model_cpu_offload()
                except:
                    pass
            else:
                self.pipeline = self.pipeline.to(self.device)
            
            self.logger.info("✅ Stable Diffusion модель загружена успешно")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки модели: {e}")
            # Создаем заглушку для работы без модели
            self.pipeline = "fallback"
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задач генерации изображений"""
        try:
            if task.task_type == "generate_image":
                return await self._generate_image(task)
            elif task.task_type == "ping":
                return {"status": "success", "message": "pong"}
            else:
                return {"status": "error", "error": f"Неизвестный тип задачи: {task.task_type}"}
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки задачи: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _generate_image(self, task: Task) -> Dict[str, Any]:
        """Генерация изображения"""
        start_time = datetime.now()
        
        try:
            data = task.data
            prompt = data.get("prompt", "")
            
            if not prompt:
                return {"status": "error", "error": "Пустой промпт"}
            
            self.generation_stats["total_generated"] += 1
            self.logger.info(f"Генерация изображения: {prompt[:100]}...")
            
            # Параметры генерации
            generation_params = {
                "prompt": self._enhance_prompt(prompt),
                "negative_prompt": data.get("negative_prompt", self.default_settings["negative_prompt"]),
                "width": data.get("width", self.default_settings["width"]),
                "height": data.get("height", self.default_settings["height"]),
                "num_inference_steps": data.get("num_inference_steps", self.default_settings["num_inference_steps"]),
                "guidance_scale": data.get("guidance_scale", self.default_settings["guidance_scale"]),
            }
            
            # Добавляем seed если указан
            seed = data.get("seed")
            if seed is not None:
                torch.manual_seed(seed)
                generation_params["generator"] = torch.Generator().manual_seed(seed)
            
            # Генерируем изображение
            if self.pipeline == "fallback" or not self.pipeline:
                # Создаем заглушку
                result = await self._create_fallback_image(prompt)
            else:
                # Реальная генерация
                result = await self._generate_real_image(generation_params)
            
            if result["status"] == "success":
                self.generation_stats["successful"] += 1
                
                # Вычисляем время генерации
                generation_time = (datetime.now() - start_time).total_seconds()
                self.generation_stats["average_time"] = (
                    self.generation_stats["average_time"] * (self.generation_stats["successful"] - 1) + generation_time
                ) / self.generation_stats["successful"]
                
                result["generation_time"] = generation_time
                result["parameters"] = generation_params
                
                self.logger.info(f"✅ Изображение создано за {generation_time:.2f}с: {result['image_path']}")
            else:
                self.generation_stats["failed"] += 1
                self.logger.error(f"❌ Ошибка генерации: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.generation_stats["failed"] += 1
            self.logger.error(f"Ошибка генерации изображения: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _generate_real_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Реальная генерация изображения через Stable Diffusion"""
        try:
            # Генерируем изображение
            with torch.no_grad():
                image = self.pipeline(**params).images[0]
            
            # Сохраняем изображение
            timestamp = datetime.now().timestamp()
            image_filename = f"generated_{timestamp}.png"
            image_path = os.path.join("/workspace/data", image_filename)
            
            # Создаем директорию если нет
            os.makedirs("/workspace/data", exist_ok=True)
            
            # Сохраняем
            image.save(image_path)
            
            return {
                "status": "success",
                "image_path": image_path,
                "filename": image_filename,
                "prompt": params["prompt"]
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _create_fallback_image(self, prompt: str) -> Dict[str, Any]:
        """Создание изображения-заглушки"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import random
            
            # Создаем изображение
            width, height = 512, 512
            background_color = (
                random.randint(50, 200),
                random.randint(50, 200),
                random.randint(50, 200)
            )
            
            img = Image.new('RGB', (width, height), color=background_color)
            draw = ImageDraw.Draw(img)
            
            # Загружаем шрифт
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Разбиваем промпт на строки
            words = prompt.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if len(test_line) <= 25:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Ограничиваем количество строк
            lines = lines[:4]
            
            # Рисуем текст по центру
            total_height = len(lines) * 30
            start_y = (height - total_height) // 2
            
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                y = start_y + i * 30
                
                # Тень
                draw.text((x + 2, y + 2), line, fill=(0, 0, 0), font=font)
                # Основной текст
                draw.text((x, y), line, fill=(255, 255, 255), font=font)
            
            # Добавляем информацию о системе
            system_text = "AGI Layer v3.9 - Image Generation"
            bbox = draw.textbbox((0, 0), system_text, font=small_font)
            text_width = bbox[2] - bbox[0]
            draw.text(
                ((width - text_width) // 2, height - 40),
                system_text,
                fill=(200, 200, 200),
                font=small_font
            )
            
            # Рамка
            draw.rectangle([5, 5, width-5, height-5], outline=(255, 255, 255), width=2)
            
            # Сохраняем
            timestamp = datetime.now().timestamp()
            image_filename = f"placeholder_{timestamp}.png"
            image_path = os.path.join("/workspace/data", image_filename)
            
            os.makedirs("/workspace/data", exist_ok=True)
            img.save(image_path)
            
            return {
                "status": "success",
                "image_path": image_path,
                "filename": image_filename,
                "prompt": prompt,
                "note": "Изображение-заглушка (модель недоступна)"
            }
            
        except Exception as e:
            return {"status": "error", "error": f"Ошибка создания заглушки: {str(e)}"}
    
    def _enhance_prompt(self, prompt: str) -> str:
        """Улучшение промпта для лучшего качества"""
        # Базовые улучшения качества
        quality_terms = [
            "high quality",
            "detailed",
            "professional",
            "8k resolution",
            "masterpiece",
            "best quality"
        ]
        
        enhanced = prompt
        
        # Добавляем качественные термины если их нет
        prompt_lower = prompt.lower()
        for term in quality_terms[:3]:  # Добавляем только первые 3
            if term not in prompt_lower:
                enhanced += f", {term}"
        
        return enhanced
    
    async def _get_metrics(self) -> Dict[str, Any]:
        """Получение метрик агента"""
        base_metrics = await super()._get_metrics()
        
        base_metrics.update({
            "model_loaded": self.pipeline is not None and self.pipeline != "fallback",
            "device": self.device,
            "generation_stats": self.generation_stats,
            "model_path": self.model_path
        })
        
        return base_metrics
    
    async def _cleanup_agent(self):
        """Очистка ресурсов"""
        self.logger.info("Очистка ресурсов ImageGenAgent")
        
        if self.pipeline and self.pipeline != "fallback":
            del self.pipeline
        
        # Очищаем CUDA кеш если используется GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


# Функция запуска
async def run_image_gen_agent(config: Dict[str, Any]):
    """Запуск агента генерации изображений"""
    agent = ImageGenAgent(config)
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
    
    asyncio.run(run_image_gen_agent(config))