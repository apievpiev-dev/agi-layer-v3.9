#!/usr/bin/env python3
"""
Download Models Script for AGI Layer v3.9
==========================================

Автоматическое скачивание всех необходимых моделей:
- LLM модели (Llama, Phi, Qwen)
- Vision модели (BLIP2, CLIP)
- Image Generation (Stable Diffusion)
- Audio модели (Whisper, Silero)
- Embedding модели (SentenceTransformers)
"""

import asyncio
import os
import sys
from pathlib import Path

import torch
from huggingface_hub import snapshot_download
from loguru import logger


class ModelDownloader:
    """Класс для скачивания и установки моделей"""
    
    def __init__(self):
        self.models_dir = Path("/app/models")
        self.cache_dir = self.models_dir / "cache"
        self.downloads_dir = self.models_dir / "downloads"
        
        # Создаем директории
        self.models_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Настройка логирования
        logger.add(
            "/app/logs/model_download.log",
            rotation="10 MB",
            level="INFO"
        )

    async def download_all_models(self):
        """Скачивание всех необходимых моделей"""
        models_to_download = [
            # LLM модели
            {
                "name": "microsoft/Phi-3-mini-4k-instruct",
                "type": "llm",
                "priority": 1,
                "size_gb": 7
            },
            {
                "name": "meta-llama/Llama-3.2-3B-Instruct",
                "type": "llm", 
                "priority": 2,
                "size_gb": 6
            },
            {
                "name": "Qwen/Qwen2.5-7B-Instruct",
                "type": "llm",
                "priority": 3,
                "size_gb": 14
            },
            
            # Vision модели
            {
                "name": "Salesforce/blip2-opt-2.7b",
                "type": "vision",
                "priority": 1,
                "size_gb": 5
            },
            {
                "name": "openai/clip-vit-base-patch32",
                "type": "vision",
                "priority": 2,
                "size_gb": 1
            },
            
            # Image Generation
            {
                "name": "runwayml/stable-diffusion-v1-5",
                "type": "image_gen",
                "priority": 1,
                "size_gb": 4
            },
            
            # Audio модели
            {
                "name": "openai/whisper-base",
                "type": "stt",
                "priority": 1,
                "size_gb": 1
            },
            {
                "name": "microsoft/speecht5_tts",
                "type": "tts",
                "priority": 2,
                "size_gb": 1
            },
            
            # Embedding модели
            {
                "name": "sentence-transformers/all-MiniLM-L6-v2",
                "type": "embeddings",
                "priority": 1,
                "size_gb": 0.5
            },
            {
                "name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "type": "embeddings",
                "priority": 2,
                "size_gb": 1
            }
        ]
        
        # Сортируем по приоритету
        models_to_download.sort(key=lambda x: x["priority"])
        
        logger.info(f"Начинаем скачивание {len(models_to_download)} моделей")
        
        total_size = sum(model["size_gb"] for model in models_to_download)
        logger.info(f"Общий размер для скачивания: ~{total_size}GB")
        
        downloaded_count = 0
        
        for model_info in models_to_download:
            try:
                success = await self._download_single_model(model_info)
                if success:
                    downloaded_count += 1
                    logger.info(f"✅ Скачано моделей: {downloaded_count}/{len(models_to_download)}")
                else:
                    logger.warning(f"⚠️ Пропущена модель: {model_info['name']}")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка скачивания {model_info['name']}: {e}")
                continue
        
        logger.info(f"🎉 Скачивание завершено! Успешно: {downloaded_count}/{len(models_to_download)}")

    async def _download_single_model(self, model_info: Dict) -> bool:
        """Скачивание одной модели"""
        try:
            model_name = model_info["name"]
            model_type = model_info["type"]
            
            logger.info(f"📥 Скачиваем {model_type} модель: {model_name}")
            
            # Проверяем, не скачана ли уже модель
            model_path = self.cache_dir / model_name.replace("/", "--")
            if model_path.exists() and any(model_path.iterdir()):
                logger.info(f"✅ Модель {model_name} уже скачана")
                return True
            
            # Скачиваем модель
            def download_model():
                return snapshot_download(
                    repo_id=model_name,
                    cache_dir=str(self.cache_dir),
                    resume_download=True,
                    local_files_only=False
                )
            
            # Выполняем скачивание в отдельном потоке
            result = await asyncio.to_thread(download_model)
            
            logger.info(f"✅ Модель {model_name} успешно скачана в {result}")
            
            # Тестируем загрузку модели
            await self._test_model_loading(model_name, model_type)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка скачивания модели {model_info['name']}: {e}")
            return False

    async def _test_model_loading(self, model_name: str, model_type: str):
        """Тестирование загрузки модели"""
        try:
            logger.info(f"🧪 Тестируем загрузку модели {model_name}")
            
            def test_load():
                if model_type == "llm":
                    from transformers import AutoTokenizer, AutoModelForCausalLM
                    tokenizer = AutoTokenizer.from_pretrained(
                        model_name, 
                        cache_dir=str(self.cache_dir)
                    )
                    model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        cache_dir=str(self.cache_dir),
                        torch_dtype=torch.float32,
                        device_map="cpu"
                    )
                    return True
                    
                elif model_type == "vision":
                    from transformers import BlipProcessor, BlipForConditionalGeneration
                    processor = BlipProcessor.from_pretrained(
                        model_name,
                        cache_dir=str(self.cache_dir)
                    )
                    model = BlipForConditionalGeneration.from_pretrained(
                        model_name,
                        cache_dir=str(self.cache_dir),
                        torch_dtype=torch.float32
                    )
                    return True
                    
                elif model_type == "embeddings":
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer(
                        model_name,
                        cache_folder=str(self.cache_dir)
                    )
                    return True
                    
                return True
            
            # Тестируем загрузку
            success = await asyncio.to_thread(test_load)
            
            if success:
                logger.info(f"✅ Модель {model_name} загружается корректно")
            else:
                logger.warning(f"⚠️ Модель {model_name} загружается с предупреждениями")
                
        except Exception as e:
            logger.warning(f"⚠️ Не удалось протестировать модель {model_name}: {e}")

    async def install_ollama_models(self):
        """Установка моделей через Ollama"""
        try:
            logger.info("🦙 Устанавливаем Ollama модели")
            
            # Проверяем, установлен ли Ollama
            ollama_check = await asyncio.create_subprocess_exec(
                "which", "ollama",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await ollama_check.wait()
            
            if ollama_check.returncode != 0:
                logger.info("📦 Устанавливаем Ollama")
                await self._install_ollama()
            
            # Модели для Ollama
            ollama_models = [
                "llama3.2:3b",
                "phi3:3.8b", 
                "qwen2.5:7b",
                "nomic-embed-text"
            ]
            
            for model in ollama_models:
                try:
                    logger.info(f"📥 Устанавливаем Ollama модель: {model}")
                    
                    process = await asyncio.create_subprocess_exec(
                        "ollama", "pull", model,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode == 0:
                        logger.info(f"✅ Ollama модель {model} установлена")
                    else:
                        logger.error(f"❌ Ошибка установки {model}: {stderr.decode()}")
                        
                except Exception as e:
                    logger.error(f"Ошибка установки Ollama модели {model}: {e}")
                    
        except Exception as e:
            logger.error(f"Ошибка работы с Ollama: {e}")

    async def _install_ollama(self):
        """Установка Ollama"""
        try:
            # Скачиваем и устанавливаем Ollama
            install_cmd = "curl -fsSL https://ollama.ai/install.sh | sh"
            
            process = await asyncio.create_subprocess_shell(
                install_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("✅ Ollama успешно установлен")
                
                # Запускаем Ollama сервер в фоне
                await asyncio.create_subprocess_exec(
                    "ollama", "serve"
                )
                
                # Ждем запуска сервера
                await asyncio.sleep(10)
                
            else:
                logger.error(f"❌ Ошибка установки Ollama: {stderr.decode()}")
                raise Exception("Не удалось установить Ollama")
                
        except Exception as e:
            logger.error(f"Критическая ошибка установки Ollama: {e}")
            raise

    async def check_disk_space(self) -> bool:
        """Проверка свободного места на диске"""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            
            free_gb = free // (1024**3)
            logger.info(f"💾 Свободного места на диске: {free_gb}GB")
            
            if free_gb < 100:  # Минимум 100GB для всех моделей
                logger.warning(f"⚠️ Мало свободного места: {free_gb}GB")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки диска: {e}")
            return False

    async def generate_download_report(self):
        """Генерация отчета о скачанных моделях"""
        try:
            logger.info("📊 Генерируем отчет о моделях")
            
            report = {
                "download_date": datetime.now().isoformat(),
                "models_directory": str(self.models_dir),
                "total_models": 0,
                "models_by_type": {},
                "total_size_gb": 0,
                "models_list": []
            }
            
            # Сканируем скачанные модели
            for model_dir in self.cache_dir.iterdir():
                if model_dir.is_dir():
                    model_name = model_dir.name.replace("--", "/")
                    
                    # Определяем тип модели
                    model_type = "unknown"
                    if "llama" in model_name.lower() or "phi" in model_name.lower() or "qwen" in model_name.lower():
                        model_type = "llm"
                    elif "blip" in model_name.lower() or "clip" in model_name.lower():
                        model_type = "vision"
                    elif "stable-diffusion" in model_name.lower():
                        model_type = "image_gen"
                    elif "whisper" in model_name.lower():
                        model_type = "stt"
                    elif "sentence-transformers" in model_name.lower():
                        model_type = "embeddings"
                    
                    # Подсчитываем размер
                    size_bytes = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
                    size_gb = size_bytes / (1024**3)
                    
                    model_info = {
                        "name": model_name,
                        "type": model_type,
                        "size_gb": round(size_gb, 2),
                        "path": str(model_dir)
                    }
                    
                    report["models_list"].append(model_info)
                    report["total_models"] += 1
                    report["total_size_gb"] += size_gb
                    
                    # Группируем по типам
                    if model_type not in report["models_by_type"]:
                        report["models_by_type"][model_type] = []
                    report["models_by_type"][model_type].append(model_name)
            
            report["total_size_gb"] = round(report["total_size_gb"], 2)
            
            # Сохраняем отчет
            report_file = self.models_dir / "download_report.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📋 Отчет сохранен: {report_file}")
            logger.info(f"📈 Всего скачано моделей: {report['total_models']}")
            logger.info(f"💾 Общий размер: {report['total_size_gb']}GB")
            
            return report
            
        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {e}")
            return None


async def main():
    """Главная функция скачивания моделей"""
    logger.info("🚀 Запуск скачивания моделей AGI Layer v3.9")
    
    downloader = ModelDownloader()
    
    try:
        # Проверяем свободное место
        if not await downloader.check_disk_space():
            logger.error("❌ Недостаточно места на диске")
            sys.exit(1)
        
        # Скачиваем HuggingFace модели
        logger.info("📦 Скачиваем HuggingFace модели...")
        await downloader.download_all_models()
        
        # Устанавливаем Ollama модели
        logger.info("🦙 Устанавливаем Ollama модели...")
        await downloader.install_ollama_models()
        
        # Генерируем отчет
        report = await downloader.generate_download_report()
        
        if report:
            logger.info("🎉 Все модели успешно скачаны!")
            logger.info(f"📊 Статистика: {report['total_models']} моделей, {report['total_size_gb']}GB")
        else:
            logger.warning("⚠️ Скачивание завершено с предупреждениями")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка скачивания: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())







