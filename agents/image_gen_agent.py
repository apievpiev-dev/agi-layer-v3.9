"""
ImageGenAgent - Агент генерации изображений
==========================================

Создает изображения используя:
- Stable Diffusion 1.5 (CPU оптимизированная)
- Поддержка русских промптов
- Различные стили и разрешения
"""

import asyncio
import base64
import io
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import torch
from diffusers import StableDiffusionPipeline
from loguru import logger
from PIL import Image

from base_agent import BaseAgent, AgentConfig, AgentMessage


class ImageGenAgent(BaseAgent):
    """Агент для генерации изображений"""
    
    def __init__(self):
        config = AgentConfig(
            name="image_gen_agent",
            type="image_generation",
            model_name="runwayml/stable-diffusion-v1-5",
            max_memory="12G",
            max_cpu_cores=6
        )
        super().__init__(config)
        
        # Stable Diffusion pipeline
        self.pipeline = None
        
        # Настройки генерации
        self.generation_config = {
            "num_inference_steps": 20,  # Меньше шагов для CPU
            "guidance_scale": 7.5,
            "width": 512,
            "height": 512,
            "negative_prompt": "blurry, bad quality, distorted, ugly, low resolution"
        }

    async def _load_model(self):
        """Загрузка Stable Diffusion модели"""
        try:
            logger.info("Загрузка Stable Diffusion модели...")
            
            def load_pipeline():
                # Загружаем pipeline для CPU
                pipe = StableDiffusionPipeline.from_pretrained(
                    "runwayml/stable-diffusion-v1-5",
                    torch_dtype=torch.float32,
                    cache_dir=os.getenv("HF_HOME", "/app/models/cache"),
                    safety_checker=None,  # Отключаем для CPU
                    requires_safety_checker=False
                )
                
                # Настраиваем для CPU
                pipe.set_progress_bar_config(disable=True)
                pipe.enable_attention_slicing()  # Экономия памяти
                
                return pipe
            
            self.pipeline = await asyncio.to_thread(load_pipeline)
            
            logger.info("✅ Stable Diffusion модель загружена (CPU режим)")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки Stable Diffusion: {e}")
            raise

    async def _agent_specific_init(self):
        """Специфичная инициализация ImageGenAgent"""
        # Регистрируемся в MetaAgent
        await self.send_message(
            "meta_agent",
            "registration",
            {
                "agent_type": self.type,
                "model_name": "stable-diffusion-v1-5",
                "capabilities": [
                    "text_to_image",
                    "style_transfer",
                    "image_editing",
                    "prompt_enhancement"
                ],
                "supported_resolutions": ["512x512", "768x512", "512x768"],
                "status": "ready"
            }
        )
        logger.info("ImageGenAgent зарегистрирован в MetaAgent")

    async def _agent_main_loop(self):
        """Основной цикл ImageGenAgent"""
        while self.is_running:
            try:
                # Проверяем задачи в очереди
                task_data = await asyncio.to_thread(
                    self.redis_client.lpop, f"tasks_{self.name}"
                )
                
                if task_data:
                    task = json.loads(task_data)
                    await self._process_generation_task(task)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка в главном цикле ImageGenAgent: {e}")
                await asyncio.sleep(5)

    async def _process_generation_task(self, task: Dict):
        """Обработка задач генерации изображений"""
        try:
            task_id = task.get("id", "unknown")
            prompt = task.get("prompt", "")
            width = task.get("width", 512)
            height = task.get("height", 512)
            num_images = task.get("num_images", 1)
            
            logger.info(f"Генерация изображения {task_id}: '{prompt[:50]}...'")
            
            # Генерируем изображения
            images = await self._generate_images(
                prompt=prompt,
                width=width,
                height=height,
                num_images=num_images
            )
            
            # Конвертируем в base64
            image_data = []
            for i, image in enumerate(images):
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                img_str = base64.b64encode(buffer.getvalue()).decode()
                image_data.append({
                    "index": i,
                    "data": img_str,
                    "format": "PNG"
                })
            
            # Сохраняем результат
            result = {
                "task_id": task_id,
                "status": "completed",
                "images": image_data,
                "prompt": prompt,
                "generation_params": {
                    "width": width,
                    "height": height,
                    "num_images": num_images
                },
                "timestamp": datetime.now().isoformat(),
                "agent": self.name
            }
            
            await asyncio.to_thread(
                self.redis_client.lpush,
                f"results_{task_id}",
                json.dumps(result)
            )
            
            logger.info(f"Изображения {task_id} сгенерированы успешно")
            
        except Exception as e:
            logger.error(f"Ошибка генерации изображений: {e}")

    async def _generate_images(self, prompt: str, width: int = 512, height: int = 512, num_images: int = 1) -> List[Image.Image]:
        """Генерация изображений по текстовому описанию"""
        try:
            # Улучшаем промпт для лучшего качества
            enhanced_prompt = await self._enhance_prompt(prompt)
            
            def generate():
                # Обновляем конфигурацию
                config = self.generation_config.copy()
                config.update({
                    "width": width,
                    "height": height
                })
                
                # Генерируем изображения
                with torch.no_grad():
                    result = self.pipeline(
                        prompt=enhanced_prompt,
                        num_images_per_prompt=num_images,
                        **config
                    )
                
                return result.images
            
            # Выполняем генерацию в отдельном потоке
            images = await asyncio.to_thread(generate)
            
            logger.info(f"Сгенерировано {len(images)} изображений")
            return images
            
        except Exception as e:
            logger.error(f"Ошибка генерации изображений: {e}")
            raise

    async def _enhance_prompt(self, prompt: str) -> str:
        """Улучшение промпта для лучшего качества"""
        try:
            # Базовые улучшения для качества
            quality_terms = [
                "high quality",
                "detailed",
                "professional",
                "sharp focus",
                "8k resolution"
            ]
            
            # Проверяем язык промпта
            if any(ord(char) > 127 for char in prompt):  # Есть кириллица
                # Для русских промптов добавляем английские качественные термины
                enhanced = f"{prompt}, {', '.join(quality_terms[:3])}"
            else:
                # Для английских промптов добавляем все термины
                enhanced = f"{prompt}, {', '.join(quality_terms)}"
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Ошибка улучшения промпта: {e}")
            return prompt

    async def process_message(self, message: AgentMessage) -> Dict[str, any]:
        """Обработка входящих сообщений"""
        try:
            if message.message_type == "generate_image":
                prompt = message.content.get("prompt", "")
                width = message.content.get("width", 512)
                height = message.content.get("height", 512)
                num_images = message.content.get("num_images", 1)
                
                if not prompt:
                    return {"status": "error", "message": "Промпт не указан"}
                
                # Генерируем изображения
                images = await self._generate_images(prompt, width, height, num_images)
                
                # Конвертируем первое изображение в base64 для быстрого ответа
                buffer = io.BytesIO()
                images[0].save(buffer, format="PNG")
                img_str = base64.b64encode(buffer.getvalue()).decode()
                
                return {
                    "status": "completed",
                    "image_data": img_str,
                    "prompt": prompt,
                    "total_images": len(images),
                    "generation_time": "~30-60 секунд на CPU"
                }
                
            elif message.message_type == "status":
                return {
                    "agent_name": self.name,
                    "model": "stable-diffusion-v1-5",
                    "status": self.status,
                    "supported_resolutions": ["512x512", "768x512", "512x768", "1024x1024"],
                    "memory_usage": await self._get_memory_usage(),
                    "error_count": self.error_count
                }
                
            else:
                return {"status": "unknown", "message": "Неизвестный тип сообщения"}
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения в ImageGenAgent: {e}")
            return {"status": "error", "message": str(e)}

    async def generate_image_from_text(self, prompt: str, width: int = 512, height: int = 512) -> str:
        """Публичный метод для генерации изображения"""
        try:
            images = await self._generate_images(prompt, width, height, 1)
            
            # Конвертируем в base64
            buffer = io.BytesIO()
            images[0].save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            # Сохраняем в память для истории
            await self.save_memory(
                f"generated_image_{int(asyncio.get_event_loop().time())}",
                {"prompt": prompt, "image_data": img_str[:100] + "...", "timestamp": datetime.now().isoformat()}
            )
            
            return img_str
            
        except Exception as e:
            logger.error(f"Ошибка генерации изображения: {e}")
            return ""


if __name__ == "__main__":
    # Запуск ImageGenAgent
    async def main():
        image_gen_agent = ImageGenAgent()
        await image_gen_agent.run()
    
    asyncio.run(main())


