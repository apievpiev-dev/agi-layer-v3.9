#!/usr/bin/env python3
"""
Скрипт загрузки CPU-only моделей для AGI Layer v3.9
"""

import os
import sys
import argparse
import asyncio
import logging
from pathlib import Path
from typing import Dict, List
import requests
from tqdm import tqdm

# Добавление корневой директории в путь
sys.path.append(str(Path(__file__).parent.parent))

from config.models import MODELS, get_model_config, get_total_size_mb


class ModelDownloader:
    """Класс для загрузки моделей"""
    
    def __init__(self, models_path: str = "/app/models"):
        self.models_path = Path(models_path)
        self.models_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def download_model(self, model_name: str, force: bool = False) -> bool:
        """Загрузка конкретной модели"""
        try:
            model_config = get_model_config(model_name)
            model_dir = self.models_path / model_name
            
            # Проверка, существует ли модель
            if model_dir.exists() and not force:
                self.logger.info(f"Модель {model_name} уже существует")
                return True
            
            self.logger.info(f"Загрузка модели {model_name}...")
            model_dir.mkdir(exist_ok=True)
            
            # Загрузка через HuggingFace
            if model_name == "stable_diffusion_1_5":
                self._download_stable_diffusion(model_dir)
            elif model_name == "phi_2":
                self._download_phi2(model_dir)
            elif model_name == "blip2":
                self._download_blip2(model_dir)
            elif model_name == "easyocr":
                self._download_easyocr(model_dir)
            elif model_name == "sentence_transformers":
                self._download_sentence_transformers(model_dir)
            else:
                self.logger.error(f"Неизвестная модель: {model_name}")
                return False
            
            self.logger.info(f"Модель {model_name} успешно загружена")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели {model_name}: {e}")
            return False
    
    def _download_stable_diffusion(self, model_dir: Path):
        """Загрузка Stable Diffusion 1.5"""
        from diffusers import StableDiffusionPipeline
        
        self.logger.info("Загрузка Stable Diffusion 1.5...")
        pipeline = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype="float32",
            use_safetensors=True
        )
        
        pipeline.save_pretrained(model_dir)
        
        # Сохранение конфигурации
        config = {
            "model_name": "stable_diffusion_1_5",
            "type": "image_gen",
            "framework": "diffusers",
            "loaded": True
        }
        
        import json
        with open(model_dir / "config.json", "w") as f:
            json.dump(config, f, indent=2)
    
    def _download_phi2(self, model_dir: Path):
        """Загрузка Phi-2"""
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        self.logger.info("Загрузка Phi-2...")
        
        # Загрузка токенизатора
        tokenizer = AutoTokenizer.from_pretrained(
            "microsoft/phi-2",
            trust_remote_code=True
        )
        tokenizer.save_pretrained(model_dir)
        
        # Загрузка модели
        model = AutoModelForCausalLM.from_pretrained(
            "microsoft/phi-2",
            torch_dtype="float32",
            trust_remote_code=True,
            device_map="cpu"
        )
        model.save_pretrained(model_dir)
        
        # Сохранение конфигурации
        config = {
            "model_name": "phi_2",
            "type": "llm",
            "framework": "transformers",
            "loaded": True
        }
        
        import json
        with open(model_dir / "config.json", "w") as f:
            json.dump(config, f, indent=2)
    
    def _download_blip2(self, model_dir: Path):
        """Загрузка BLIP2"""
        from transformers import Blip2Processor, Blip2ForConditionalGeneration
        
        self.logger.info("Загрузка BLIP2...")
        
        # Загрузка процессора
        processor = Blip2Processor.from_pretrained(
            "Salesforce/blip2-opt-2.7b"
        )
        processor.save_pretrained(model_dir)
        
        # Загрузка модели
        model = Blip2ForConditionalGeneration.from_pretrained(
            "Salesforce/blip2-opt-2.7b",
            torch_dtype="float32",
            device_map="cpu"
        )
        model.save_pretrained(model_dir)
        
        # Сохранение конфигурации
        config = {
            "model_name": "blip2",
            "type": "vision",
            "framework": "transformers",
            "loaded": True
        }
        
        import json
        with open(model_dir / "config.json", "w") as f:
            json.dump(config, f, indent=2)
    
    def _download_easyocr(self, model_dir: Path):
        """Загрузка EasyOCR"""
        import easyocr
        
        self.logger.info("Загрузка EasyOCR...")
        
        # Инициализация EasyOCR для загрузки моделей
        reader = easyocr.Reader(
            ['en', 'ru'],
            gpu=False,
            model_storage_directory=str(model_dir)
        )
        
        # Сохранение конфигурации
        config = {
            "model_name": "easyocr",
            "type": "ocr",
            "framework": "easyocr",
            "languages": ["en", "ru"],
            "loaded": True
        }
        
        import json
        with open(model_dir / "config.json", "w") as f:
            json.dump(config, f, indent=2)
    
    def _download_sentence_transformers(self, model_dir: Path):
        """Загрузка SentenceTransformers"""
        from sentence_transformers import SentenceTransformer
        
        self.logger.info("Загрузка SentenceTransformers...")
        
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        model.save(model_dir)
        
        # Сохранение конфигурации
        config = {
            "model_name": "sentence_transformers",
            "type": "embedding",
            "framework": "sentence_transformers",
            "model_type": "all-MiniLM-L6-v2",
            "embedding_dimension": 384,
            "loaded": True
        }
        
        import json
        with open(model_dir / "config.json", "w") as f:
            json.dump(config, f, indent=2)
    
    def download_all_models(self, force: bool = False) -> Dict[str, bool]:
        """Загрузка всех моделей"""
        results = {}
        
        total_size = get_total_size_mb()
        print(f"📥 Загрузка всех моделей (общий размер: {total_size} MB)")
        
        for model_name in MODELS.keys():
            print(f"\n🔄 Загрузка {model_name}...")
            results[model_name] = self.download_model(model_name, force)
        
        return results
    
    def check_models(self) -> Dict[str, bool]:
        """Проверка наличия моделей"""
        results = {}
        
        for model_name in MODELS.keys():
            model_dir = self.models_path / model_name
            config_file = model_dir / "config.json"
            
            exists = model_dir.exists() and config_file.exists()
            results[model_name] = exists
            
            status = "✅" if exists else "❌"
            print(f"{status} {model_name}: {'Готов' if exists else 'Отсутствует'}")
        
        return results
    
    def get_disk_usage(self) -> Dict[str, int]:
        """Получение информации об использовании диска"""
        usage = {}
        
        for model_name in MODELS.keys():
            model_dir = self.models_path / model_name
            if model_dir.exists():
                total_size = sum(
                    f.stat().st_size 
                    for f in model_dir.rglob('*') 
                    if f.is_file()
                )
                usage[model_name] = total_size // (1024 * 1024)  # MB
            else:
                usage[model_name] = 0
        
        return usage


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Загрузка моделей AGI Layer v3.9")
    parser.add_argument("--models-path", default="/app/models", help="Путь к моделям")
    parser.add_argument("--model", help="Загрузить конкретную модель")
    parser.add_argument("--all", action="store_true", help="Загрузить все модели")
    parser.add_argument("--check", action="store_true", help="Проверить наличие моделей")
    parser.add_argument("--check-only", action="store_true", help="Только проверка без загрузки")
    parser.add_argument("--force", action="store_true", help="Принудительная загрузка")
    parser.add_argument("--usage", action="store_true", help="Показать использование диска")
    
    args = parser.parse_args()
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    downloader = ModelDownloader(args.models_path)
    
    if args.check or args.check_only:
        print("🔍 Проверка моделей:")
        results = downloader.check_models()
        
        if args.check_only:
            return
        
        missing_models = [name for name, exists in results.items() if not exists]
        if missing_models and args.all:
            print(f"\n📥 Загрузка отсутствующих моделей: {missing_models}")
            for model_name in missing_models:
                downloader.download_model(model_name, args.force)
    
    elif args.usage:
        print("💾 Использование диска:")
        usage = downloader.get_disk_usage()
        total = 0
        for model_name, size in usage.items():
            print(f"  {model_name}: {size} MB")
            total += size
        print(f"  Общий размер: {total} MB")
    
    elif args.model:
        print(f"📥 Загрузка модели {args.model}")
        success = downloader.download_model(args.model, args.force)
        if success:
            print(f"✅ Модель {args.model} успешно загружена")
        else:
            print(f"❌ Ошибка загрузки модели {args.model}")
            sys.exit(1)
    
    elif args.all:
        print("📥 Загрузка всех моделей")
        results = downloader.download_all_models(args.force)
        
        failed_models = [name for name, success in results.items() if not success]
        if failed_models:
            print(f"❌ Ошибка загрузки моделей: {failed_models}")
            sys.exit(1)
        else:
            print("✅ Все модели успешно загружены")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

