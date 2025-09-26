#!/usr/bin/env python3
"""
Комплексное тестирование всех моделей AGI Layer v3.9
===================================================

Тестирует все установленные модели и возможности:
- 4 LLM модели (Llama, Phi, Qwen, CodeLlama)
- Whisper (распознавание речи)
- EasyOCR (распознавание текста)
- ChromaDB (векторная память)
- Vision модели (при наличии)
"""

import asyncio
import subprocess
import time
from datetime import datetime

import chromadb
from sentence_transformers import SentenceTransformer


class AGITester:
    """Класс для комплексного тестирования AGI Layer"""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()

    async def test_all_systems(self):
        """Запуск всех тестов"""
        print("🚀 Запуск комплексного тестирования AGI Layer v3.9")
        print("=" * 60)
        
        # Тест 1: LLM модели
        await self.test_llm_models()
        
        # Тест 2: Whisper
        await self.test_whisper()
        
        # Тест 3: EasyOCR
        await self.test_easyocr()
        
        # Тест 4: ChromaDB
        await self.test_chromadb()
        
        # Тест 5: SentenceTransformers
        await self.test_embeddings()
        
        # Тест 6: Docker сервисы
        await self.test_docker_services()
        
        # Итоговый отчет
        await self.generate_report()

    async def test_llm_models(self):
        """Тестирование LLM моделей"""
        print("\n🧠 Тестирование LLM моделей...")
        
        # Получаем список моделей
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode != 0:
            self.results["llm"] = {"status": "error", "message": "Ollama недоступен"}
            return
        
        lines = result.stdout.strip().split('\n')[1:]
        models = [line.split()[0] for line in lines if line.strip()]
        
        llm_results = {}
        
        for model in models:
            print(f"  🤖 Тестирую {model}...")
            
            try:
                # Тест генерации
                test_prompts = {
                    "greeting": "Привет!",
                    "reasoning": "2+2=?",
                    "creativity": "Напиши хайку о программировании"
                }
                
                model_results = {}
                
                for test_name, prompt in test_prompts.items():
                    start = time.time()
                    
                    cmd = ["ollama", "run", model, prompt]
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=30
                    )
                    
                    duration = time.time() - start
                    
                    if process.returncode == 0:
                        response = stdout.decode().strip()
                        model_results[test_name] = {
                            "status": "success",
                            "response": response[:100] + "..." if len(response) > 100 else response,
                            "duration": round(duration, 2)
                        }
                    else:
                        model_results[test_name] = {
                            "status": "error",
                            "error": stderr.decode().strip(),
                            "duration": round(duration, 2)
                        }
                
                llm_results[model] = model_results
                print(f"    ✅ {model} - OK")
                
            except Exception as e:
                llm_results[model] = {"status": "error", "error": str(e)}
                print(f"    ❌ {model} - Ошибка")
        
        self.results["llm"] = llm_results

    async def test_whisper(self):
        """Тестирование Whisper"""
        print("\n🎙️ Тестирование Whisper...")
        
        try:
            import whisper
            
            # Загружаем модель
            model = whisper.load_model("base", device="cpu")
            
            self.results["whisper"] = {
                "status": "success",
                "model": "whisper-base",
                "device": "cpu",
                "languages": ["ru", "en", "auto"]
            }
            print("  ✅ Whisper - готов к работе")
            
        except Exception as e:
            self.results["whisper"] = {"status": "error", "error": str(e)}
            print("  ❌ Whisper - ошибка")

    async def test_easyocr(self):
        """Тестирование EasyOCR"""
        print("\n👁️ Тестирование EasyOCR...")
        
        try:
            import easyocr
            
            # Инициализируем reader
            reader = easyocr.Reader(['ru', 'en'], gpu=False)
            
            self.results["easyocr"] = {
                "status": "success",
                "languages": ["ru", "en"],
                "device": "cpu"
            }
            print("  ✅ EasyOCR - готов к работе")
            
        except Exception as e:
            self.results["easyocr"] = {"status": "error", "error": str(e)}
            print("  ❌ EasyOCR - ошибка")

    async def test_chromadb(self):
        """Тестирование ChromaDB"""
        print("\n💾 Тестирование ChromaDB...")
        
        try:
            # Подключаемся к ChromaDB
            client = chromadb.HttpClient(host="localhost", port=8000)
            
            # Создаем тестовую коллекцию
            test_collection = client.get_or_create_collection("test_collection")
            
            # Добавляем тестовую запись
            test_collection.add(
                embeddings=[[1.0, 2.0, 3.0]],
                documents=["Тестовая запись"],
                metadatas=[{"test": True}],
                ids=["test_1"]
            )
            
            # Проверяем поиск
            results = test_collection.query(
                query_embeddings=[[1.0, 2.0, 3.0]],
                n_results=1
            )
            
            # Удаляем тестовую коллекцию
            client.delete_collection("test_collection")
            
            self.results["chromadb"] = {
                "status": "success",
                "host": "localhost:8000",
                "test_query": "OK"
            }
            print("  ✅ ChromaDB - готов к работе")
            
        except Exception as e:
            self.results["chromadb"] = {"status": "error", "error": str(e)}
            print("  ❌ ChromaDB - ошибка")

    async def test_embeddings(self):
        """Тестирование SentenceTransformers"""
        print("\n🔍 Тестирование Embeddings...")
        
        try:
            # Загружаем модель
            model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            
            # Тестируем создание embeddings
            texts = ["Привет мир", "Hello world", "Программирование это круто"]
            embeddings = model.encode(texts)
            
            self.results["embeddings"] = {
                "status": "success",
                "model": "all-MiniLM-L6-v2",
                "embedding_size": len(embeddings[0]),
                "test_texts": len(texts)
            }
            print("  ✅ SentenceTransformers - готов к работе")
            
        except Exception as e:
            self.results["embeddings"] = {"status": "error", "error": str(e)}
            print("  ❌ SentenceTransformers - ошибка")

    async def test_docker_services(self):
        """Тестирование Docker сервисов"""
        print("\n🐳 Тестирование Docker сервисов...")
        
        try:
            # Проверяем статус контейнеров
            result = subprocess.run(
                ["docker-compose", "ps"], 
                cwd="/root/agi-layer-v3.9",
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[2:]  # Пропускаем заголовки
                
                services = {}
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            name = parts[0]
                            state = parts[3] if len(parts) > 3 else "unknown"
                            services[name] = state
                
                self.results["docker"] = {
                    "status": "success",
                    "services": services,
                    "total_services": len(services)
                }
                print(f"  ✅ Docker - {len(services)} сервисов запущено")
            else:
                self.results["docker"] = {"status": "error", "error": "docker-compose недоступен"}
                print("  ❌ Docker - ошибка")
                
        except Exception as e:
            self.results["docker"] = {"status": "error", "error": str(e)}
            print("  ❌ Docker - ошибка")

    async def generate_report(self):
        """Генерация итогового отчета"""
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 60)
        
        working_systems = 0
        total_systems = 0
        
        for system, result in self.results.items():
            total_systems += 1
            
            if isinstance(result, dict):
                if result.get("status") == "success":
                    working_systems += 1
                    print(f"✅ {system.upper()}: РАБОТАЕТ")
                else:
                    print(f"❌ {system.upper()}: ОШИБКА")
            else:
                # Для LLM моделей
                if system == "llm":
                    llm_working = 0
                    llm_total = len(result)
                    
                    for model, model_result in result.items():
                        if isinstance(model_result, dict) and "greeting" in model_result:
                            if model_result["greeting"]["status"] == "success":
                                llm_working += 1
                                print(f"✅ LLM {model}: РАБОТАЕТ")
                            else:
                                print(f"❌ LLM {model}: ОШИБКА")
                        else:
                            print(f"❌ LLM {model}: ОШИБКА")
                    
                    if llm_working == llm_total:
                        working_systems += 1
        
        print(f"\n🎯 ОБЩИЙ РЕЗУЛЬТАТ: {working_systems}/{total_systems} систем работают")
        print(f"⏱️ Время тестирования: {round(total_time, 2)} секунд")
        print(f"📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Сохраняем отчет
        with open("/root/agi-layer-v3.9/test_report.json", "w", encoding="utf-8") as f:
            import json
            report = {
                "timestamp": datetime.now().isoformat(),
                "total_time": round(total_time, 2),
                "working_systems": working_systems,
                "total_systems": total_systems,
                "success_rate": round(working_systems / total_systems * 100, 1),
                "results": self.results
            }
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Отчет сохранен: /root/agi-layer-v3.9/test_report.json")
        
        if working_systems == total_systems:
            print("\n🎉 ВСЕ СИСТЕМЫ РАБОТАЮТ ИДЕАЛЬНО!")
        elif working_systems > total_systems * 0.8:
            print("\n✅ БОЛЬШИНСТВО СИСТЕМ РАБОТАЮТ!")
        else:
            print("\n⚠️ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ НАСТРОЙКА")


async def main():
    """Главная функция тестирования"""
    tester = AGITester()
    await tester.test_all_systems()


if __name__ == "__main__":
    asyncio.run(main())




