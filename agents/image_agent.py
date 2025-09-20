"""
ImageAgent - генерация изображений с помощью Stable Diffusion 1.5 (CPU-only)
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import torch
from diffusers import StableDiffusionPipeline
from PIL import Image
import aiofiles
from .base_agent import BaseAgent, Task


class ImageAgent(BaseAgent):
    """Агент для генерации изображений"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("image_agent", config)
        self.model_path = config.get('models_path', '/app/models')
        self.output_path = config.get('output_path', '/app/output/images')
        self.pipeline: Optional[StableDiffusionPipeline] = None
        self.device = "cpu"  # CPU-only
        
    async def _initialize_agent(self):
        """Инициализация ImageAgent"""
        self.logger.info("Инициализация ImageAgent")
        
        # Создание директории для выходных изображений
        os.makedirs(self.output_path, exist_ok=True)
        
        # Загрузка модели Stable Diffusion
        await self._load_model()
        
        self.logger.info("ImageAgent успешно инициализирован")
    
    async def _load_model(self):
        """Загрузка модели Stable Diffusion 1.5"""
        try:
            model_file = os.path.join(self.model_path, "stable_diffusion_1_5")
            
            self.logger.info(f"Загрузка Stable Diffusion 1.5 из {model_file}")
            
            # Загрузка пайплайна для CPU
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                model_file,
                torch_dtype=torch.float32,  # CPU совместимость
                use_safetensors=True
            )
            
            # Настройка для CPU
            self.pipeline = self.pipeline.to(self.device)
            
            # Оптимизация для CPU
            self.pipeline.enable_attention_slicing()
            
            self.logger.info("Stable Diffusion 1.5 загружен успешно")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {e}")
            
            # Fallback - загрузка из HuggingFace
            try:
                self.logger.info("Попытка загрузки из HuggingFace...")
                self.pipeline = StableDiffusionPipeline.from_pretrained(
                    "runwayml/stable-diffusion-v1-5",
                    torch_dtype=torch.float32,
                    use_safetensors=True
                )
                self.pipeline = self.pipeline.to(self.device)
                self.pipeline.enable_attention_slicing()
                
                self.logger.info("Модель загружена из HuggingFace")
                
            except Exception as e2:
                self.logger.error(f"Критическая ошибка загрузки модели: {e2}")
                raise
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задач генерации изображений"""
        if task.task_type == "image_generation":
            return await self._generate_image(task)
        elif task.task_type == "image_variation":
            return await self._create_image_variation(task)
        elif task.task_type == "image_upscale":
            return await self._upscale_image(task)
        
        return {"status": "unknown_task_type"}
    
    async def _generate_image(self, task: Task) -> Dict[str, Any]:
        """Генерация изображения по промпту"""
        try:
            prompt = task.data.get("prompt", "beautiful landscape")
            negative_prompt = task.data.get("negative_prompt", "")
            width = task.data.get("width", 512)
            height = task.data.get("height", 512)
            num_inference_steps = task.data.get("num_inference_steps", 20)
            guidance_scale = task.data.get("guidance_scale", 7.5)
            seed = task.data.get("seed", None)
            
            self.logger.info(f"Генерация изображения: {prompt}")
            
            # Генератор для воспроизводимости
            generator = torch.Generator(device=self.device)
            if seed is not None:
                generator.manual_seed(seed)
            
            # Генерация изображения
            with torch.no_grad():
                result = self.pipeline(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    generator=generator
                )
            
            # Сохранение изображения
            image = result.images[0]
            filename = f"image_{task.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.output_path, filename)
            
            image.save(filepath)
            
            # Сохранение метаданных
            metadata = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "seed": seed,
                "filename": filename,
                "filepath": filepath,
                "generated_at": datetime.now().isoformat()
            }
            
            # Сохранение в базу данных
            await self._save_image_metadata(task.id, metadata)
            
            self.logger.info(f"Изображение сохранено: {filepath}")
            
            return {
                "status": "success",
                "image_path": filepath,
                "filename": filename,
                "metadata": metadata
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации изображения: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _create_image_variation(self, task: Task) -> Dict[str, Any]:
        """Создание вариации изображения"""
        try:
            image_path = task.data.get("image_path")
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": "Изображение не найдено"}
            
            # Загрузка исходного изображения
            original_image = Image.open(image_path)
            
            # Создание вариации (упрощенная реализация)
            prompt = task.data.get("prompt", "variation of the image")
            strength = task.data.get("strength", 0.8)
            
            # Здесь можно использовать img2img пайплайн
            # Для простоты используем обычную генерацию с похожим промптом
            return await self._generate_image(task)
            
        except Exception as e:
            self.logger.error(f"Ошибка создания вариации: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _upscale_image(self, task: Task) -> Dict[str, Any]:
        """Увеличение разрешения изображения"""
        try:
            image_path = task.data.get("image_path")
            scale_factor = task.data.get("scale_factor", 2)
            
            if not image_path or not os.path.exists(image_path):
                return {"status": "error", "error": "Изображение не найдено"}
            
            # Загрузка изображения
            image = Image.open(image_path)
            
            # Простое увеличение разрешения (можно заменить на более продвинутые методы)
            new_size = (image.width * scale_factor, image.height * scale_factor)
            upscaled_image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Сохранение
            filename = f"upscaled_{task.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.output_path, filename)
            upscaled_image.save(filepath)
            
            return {
                "status": "success",
                "image_path": filepath,
                "original_size": (image.width, image.height),
                "new_size": new_size,
                "scale_factor": scale_factor
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка увеличения изображения: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _save_image_metadata(self, task_id: str, metadata: Dict[str, Any]):
        """Сохранение метаданных изображения в базу данных"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO generated_images 
                    (task_id, agent_name, prompt, image_path, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    task_id,
                    self.name,
                    metadata["prompt"],
                    metadata["filepath"],
                    metadata
                )
        except Exception as e:
            self.logger.error(f"Ошибка сохранения метаданных: {e}")
    
    async def _cleanup_agent(self):
        """Очистка ресурсов ImageAgent"""
        if self.pipeline:
            del self.pipeline
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        self.logger.info("ImageAgent очищен")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о модели"""
        return {
            "model_name": "Stable Diffusion 1.5",
            "device": self.device,
            "loaded": self.pipeline is not None,
            "output_path": self.output_path
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья агента"""
        return {
            "status": "healthy" if self.pipeline is not None else "error",
            "model_loaded": self.pipeline is not None,
            "device": self.device,
            "output_directory_exists": os.path.exists(self.output_path)
        }
