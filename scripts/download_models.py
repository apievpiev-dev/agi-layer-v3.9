#!/usr/bin/env python3
"""
Скрипт загрузки всех моделей для AGI Layer v3.9
Загружает Stable Diffusion, Phi-2, BLIP2, OCR и другие модели
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BlipProcessor, BlipForConditionalGeneration
from diffusers import StableDiffusionPipeline
from sentence_transformers import SentenceTransformer
import easyocr
from tqdm import tqdm

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/logs/model_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ModelDownloader:
    """Загрузчик моделей для AGI Layer"""
    
    def __init__(self, models_path: str = "/workspace/models"):
        self.models_path = Path(models_path)
        self.models_path.mkdir(parents=True, exist_ok=True)
        
        # Конфигурация моделей
        self.models_config = {
            # Текстовые модели
            "text_models": {
                "phi-2": {
                    "name": "microsoft/phi-2",
                    "type": "causal_lm",
                    "size": "2.7B",
                    "description": "Компактная языковая модель от Microsoft"
                },
                "phi-2-instruct": {
                    "name": "microsoft/phi-2",
                    "type": "causal_lm", 
                    "size": "2.7B",
                    "description": "Phi-2 для инструкций"
                }
            },
            
            # Модели генерации изображений
            "image_models": {
                "stable-diffusion-v1-5": {
                    "name": "runwayml/stable-diffusion-v1-5",
                    "type": "diffusion",
                    "size": "4GB",
                    "description": "Stable Diffusion 1.5 для генерации изображений"
                }
            },
            
            # Модели анализа изображений
            "vision_models": {
                "blip2-base": {
                    "name": "Salesforce/blip-image-captioning-base",
                    "type": "vision_text",
                    "size": "990MB", 
                    "description": "BLIP2 для анализа изображений"
                },
                "blip2-large": {
                    "name": "Salesforce/blip-image-captioning-large",
                    "type": "vision_text",
                    "size": "1.9GB",
                    "description": "BLIP2 Large для детального анализа"
                }
            },
            
            # Модели эмбеддингов
            "embedding_models": {
                "sentence-transformer": {
                    "name": "sentence-transformers/all-MiniLM-L6-v2",
                    "type": "sentence_transformer",
                    "size": "90MB",
                    "description": "Модель для создания эмбеддингов"
                },
                "multilingual-e5": {
                    "name": "intfloat/multilingual-e5-small",
                    "type": "sentence_transformer", 
                    "size": "118MB",
                    "description": "Многоязычная модель эмбеддингов"
                }
            }
        }
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Устройство для загрузки моделей: {self.device}")
    
    async def download_all_models(self):
        """Загрузка всех моделей"""
        logger.info("🚀 Начинаем загрузку всех моделей AGI Layer v3.9")
        
        total_models = sum(len(models) for models in self.models_config.values())
        logger.info(f"Всего моделей к загрузке: {total_models}")
        
        # Создаем директории
        self._create_directories()
        
        # Загружаем модели по категориям
        for category, models in self.models_config.items():
            logger.info(f"\n📦 Загрузка категории: {category}")
            
            for model_key, model_info in models.items():
                try:
                    await self._download_model(category, model_key, model_info)
                except Exception as e:
                    logger.error(f"❌ Ошибка загрузки {model_key}: {e}")
        
        # Загружаем дополнительные компоненты
        await self._download_additional_components()
        
        # Проверяем загруженные модели
        self._verify_models()
        
        logger.info("✅ Загрузка всех моделей завершена!")
    
    def _create_directories(self):
        """Создание директорий для моделей"""
        directories = [
            "text_models",
            "image_models", 
            "vision_models",
            "embedding_models",
            "ocr_models",
            "cache"
        ]
        
        for directory in directories:
            dir_path = self.models_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Создана директория: {dir_path}")
    
    async def _download_model(self, category: str, model_key: str, model_info: Dict):
        """Загрузка конкретной модели"""
        model_name = model_info["name"]
        model_type = model_info["type"]
        model_size = model_info["size"]
        
        logger.info(f"⬇️ Загрузка {model_key} ({model_size}): {model_name}")
        
        # Определяем путь сохранения
        save_path = self.models_path / category / model_key
        
        # Проверяем, не загружена ли модель уже
        if save_path.exists() and any(save_path.iterdir()):
            logger.info(f"✅ Модель {model_key} уже загружена, пропускаем")
            return
        
        try:
            if model_type == "causal_lm":
                await self._download_text_model(model_name, save_path)
            elif model_type == "diffusion":
                await self._download_diffusion_model(model_name, save_path)
            elif model_type == "vision_text":
                await self._download_vision_model(model_name, save_path)
            elif model_type == "sentence_transformer":
                await self._download_embedding_model(model_name, save_path)
            
            logger.info(f"✅ Модель {model_key} успешно загружена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели {model_key}: {e}")
            raise
    
    async def _download_text_model(self, model_name: str, save_path: Path):
        """Загрузка текстовой модели"""
        logger.info(f"📝 Загрузка текстовой модели: {model_name}")
        
        # Загружаем токенизатор
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            cache_dir=str(save_path)
        )
        
        # Загружаем модель
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,  # CPU совместимость
            trust_remote_code=True,
            cache_dir=str(save_path)
        )
        
        # Сохраняем локально
        tokenizer.save_pretrained(str(save_path))
        model.save_pretrained(str(save_path))
        
        logger.info(f"💾 Текстовая модель сохранена в {save_path}")
    
    async def _download_diffusion_model(self, model_name: str, save_path: Path):
        """Загрузка модели диффузии"""
        logger.info(f"🎨 Загрузка модели генерации изображений: {model_name}")
        
        # Загружаем pipeline
        pipeline = StableDiffusionPipeline.from_pretrained(
            model_name,
            torch_dtype=torch.float32,  # CPU совместимость
            safety_checker=None,
            requires_safety_checker=False,
            cache_dir=str(save_path)
        )
        
        # Сохраняем локально
        pipeline.save_pretrained(str(save_path))
        
        logger.info(f"💾 Модель диффузии сохранена в {save_path}")
    
    async def _download_vision_model(self, model_name: str, save_path: Path):
        """Загрузка модели анализа изображений"""
        logger.info(f"👁️ Загрузка модели анализа изображений: {model_name}")
        
        # Загружаем процессор и модель
        processor = BlipProcessor.from_pretrained(
            model_name,
            cache_dir=str(save_path)
        )
        
        model = BlipForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            cache_dir=str(save_path)
        )
        
        # Сохраняем локально
        processor.save_pretrained(str(save_path))
        model.save_pretrained(str(save_path))
        
        logger.info(f"💾 Модель анализа изображений сохранена в {save_path}")
    
    async def _download_embedding_model(self, model_name: str, save_path: Path):
        """Загрузка модели эмбеддингов"""
        logger.info(f"🔗 Загрузка модели эмбеддингов: {model_name}")
        
        # Загружаем модель sentence transformer
        model = SentenceTransformer(
            model_name,
            cache_folder=str(save_path)
        )
        
        # Сохраняем локально
        model.save(str(save_path))
        
        logger.info(f"💾 Модель эмбеддингов сохранена в {save_path}")
    
    async def _download_additional_components(self):
        """Загрузка дополнительных компонентов"""
        logger.info("📦 Загрузка дополнительных компонентов...")
        
        # EasyOCR модели
        try:
            logger.info("🔤 Инициализация EasyOCR...")
            ocr_path = self.models_path / "ocr_models"
            ocr_path.mkdir(exist_ok=True)
            
            # Инициализируем EasyOCR (это автоматически загрузит модели)
            reader = easyocr.Reader(
                ['en', 'ru'],  # Английский и русский языки
                model_storage_directory=str(ocr_path),
                download_enabled=True
            )
            
            logger.info("✅ EasyOCR модели загружены")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки EasyOCR: {e}")
    
    def _verify_models(self):
        """Проверка загруженных моделей"""
        logger.info("🔍 Проверка загруженных моделей...")
        
        verification_results = {}
        
        for category in self.models_config:
            category_path = self.models_path / category
            if category_path.exists():
                models_in_category = list(category_path.iterdir())
                verification_results[category] = len(models_in_category)
                logger.info(f"✅ {category}: {len(models_in_category)} моделей")
            else:
                verification_results[category] = 0
                logger.warning(f"⚠️ {category}: директория не найдена")
        
        # Проверяем общий размер
        total_size = sum(
            sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            for path in self.models_path.iterdir() if path.is_dir()
        )
        
        total_size_gb = total_size / (1024**3)
        logger.info(f"📊 Общий размер загруженных моделей: {total_size_gb:.2f} GB")
        
        # Сохраняем отчет
        self._save_verification_report(verification_results, total_size_gb)
    
    def _save_verification_report(self, results: Dict, total_size: float):
        """Сохранение отчета о загрузке"""
        report_path = self.models_path / "download_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("AGI Layer v3.9 - Отчет о загрузке моделей\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Дата загрузки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Устройство: {self.device}\n")
            f.write(f"Общий размер: {total_size:.2f} GB\n\n")
            
            f.write("Загруженные модели по категориям:\n")
            for category, count in results.items():
                f.write(f"  {category}: {count} моделей\n")
            
            f.write("\nДетали моделей:\n")
            for category, models in self.models_config.items():
                f.write(f"\n{category}:\n")
                for model_key, model_info in models.items():
                    f.write(f"  - {model_key}: {model_info['name']} ({model_info['size']})\n")
        
        logger.info(f"📄 Отчет сохранен: {report_path}")

    async def download_specific_models(self, model_list: List[str]):
        """Загрузка конкретных моделей"""
        logger.info(f"⬇️ Загрузка конкретных моделей: {model_list}")
        
        for model_key in model_list:
            found = False
            for category, models in self.models_config.items():
                if model_key in models:
                    model_info = models[model_key]
                    await self._download_model(category, model_key, model_info)
                    found = True
                    break
            
            if not found:
                logger.warning(f"⚠️ Модель {model_key} не найдена в конфигурации")

    def get_available_models(self) -> Dict:
        """Получение списка доступных моделей"""
        return self.models_config

    def get_download_status(self) -> Dict:
        """Получение статуса загрузки"""
        status = {}
        
        for category, models in self.models_config.items():
            status[category] = {}
            for model_key in models:
                model_path = self.models_path / category / model_key
                status[category][model_key] = {
                    "downloaded": model_path.exists() and any(model_path.iterdir()) if model_path.exists() else False,
                    "path": str(model_path)
                }
        
        return status


async def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Загрузчик моделей AGI Layer v3.9")
    parser.add_argument("--models-path", default="/workspace/models", help="Путь для сохранения моделей")
    parser.add_argument("--specific", nargs="+", help="Загрузить только конкретные модели")
    parser.add_argument("--list", action="store_true", help="Показать список доступных моделей")
    parser.add_argument("--status", action="store_true", help="Показать статус загрузки")
    
    args = parser.parse_args()
    
    downloader = ModelDownloader(args.models_path)
    
    if args.list:
        print("\n📋 Доступные модели:")
        models = downloader.get_available_models()
        for category, category_models in models.items():
            print(f"\n{category}:")
            for model_key, model_info in category_models.items():
                print(f"  - {model_key}: {model_info['name']} ({model_info['size']})")
        return
    
    if args.status:
        print("\n📊 Статус загрузки:")
        status = downloader.get_download_status()
        for category, category_models in status.items():
            print(f"\n{category}:")
            for model_key, model_status in category_models.items():
                status_icon = "✅" if model_status["downloaded"] else "❌"
                print(f"  {status_icon} {model_key}")
        return
    
    if args.specific:
        await downloader.download_specific_models(args.specific)
    else:
        await downloader.download_all_models()


if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(main())