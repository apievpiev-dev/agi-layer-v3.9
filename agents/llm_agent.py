"""
LLMAgent - Агент языковой модели
===============================

Обрабатывает текстовые запросы используя:
- Llama 3.2 (3B/8B/11B)
- Phi-3 (3.8B/7B/14B) 
- Qwen2.5 (7B/14B)
- Локальные CPU-оптимизированные модели
"""

import asyncio
import json
import os
from typing import Dict, List, Optional

import torch
from loguru import logger
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    pipeline
)

from base_agent import BaseAgent, AgentConfig, AgentMessage


class LLMAgent(BaseAgent):
    """Агент для работы с языковыми моделями"""
    
    def __init__(self):
        config = AgentConfig(
            name="llm_agent",
            type="language_model",
            model_name=os.getenv("DEFAULT_LLM_MODEL", "microsoft/Phi-3-mini-4k-instruct"),
            max_memory="16G",
            max_cpu_cores=4
        )
        super().__init__(config)
        
        # Модель и токенизатор
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        
        # Настройки генерации
        self.generation_config = {
            "max_new_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True,
            "pad_token_id": None  # Будет установлен после загрузки токенизатора
        }

    async def _load_model(self):
        """Загрузка языковой модели"""
        try:
            model_name = self.config.model_name
            logger.info(f"Загрузка модели {model_name}")
            
            # Настройки для CPU
            device_map = "cpu"
            torch_dtype = torch.float32
            
            # Загружаем токенизатор
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True,
                cache_dir="/app/models/cache"
            )
            
            # Устанавливаем pad_token если его нет
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.generation_config["pad_token_id"] = self.tokenizer.pad_token_id
            
            # Конфигурация квантизации для экономии памяти
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float32,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            ) if torch.cuda.is_available() else None
            
            # Загружаем модель
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch_dtype,
                device_map=device_map,
                trust_remote_code=True,
                cache_dir="/app/models/cache",
                quantization_config=quantization_config,
                low_cpu_mem_usage=True
            )
            
            # Создаем pipeline для удобной генерации
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device_map=device_map,
                torch_dtype=torch_dtype
            )
            
            logger.info(f"Модель {model_name} успешно загружена")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            raise

    async def _agent_specific_init(self):
        """Специфичная инициализация LLMAgent"""
        # Регистрируемся в MetaAgent
        await self.send_message(
            "meta_agent",
            "registration", 
            {
                "agent_type": self.type,
                "model_name": self.config.model_name,
                "capabilities": ["text_generation", "conversation", "code_generation", "analysis"],
                "status": "ready"
            }
        )
        logger.info("LLMAgent зарегистрирован в MetaAgent")

    async def _agent_main_loop(self):
        """Основной цикл LLMAgent"""
        while self.is_running:
            try:
                # Проверяем наличие задач в очереди
                task_data = await asyncio.to_thread(
                    self.redis_client.lpop, f"tasks_{self.name}"
                )
                
                if task_data:
                    task = json.loads(task_data)
                    await self._process_task(task)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка в главном цикле LLMAgent: {e}")
                await asyncio.sleep(5)

    async def _process_task(self, task: Dict):
        """Обработка задачи генерации текста"""
        try:
            task_id = task.get("id", "unknown")
            prompt = task.get("prompt", "")
            max_tokens = task.get("max_tokens", 512)
            temperature = task.get("temperature", 0.7)
            
            logger.info(f"Обработка задачи {task_id}: генерация текста")
            
            # Генерируем ответ
            response = await self._generate_text(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Сохраняем результат
            result = {
                "task_id": task_id,
                "status": "completed",
                "result": response,
                "timestamp": datetime.now().isoformat(),
                "agent": self.name
            }
            
            # Отправляем результат обратно
            await asyncio.to_thread(
                self.redis_client.lpush,
                f"results_{task_id}",
                json.dumps(result)
            )
            
            logger.info(f"Задача {task_id} выполнена успешно")
            
        except Exception as e:
            logger.error(f"Ошибка обработки задачи: {e}")
            
            # Сохраняем ошибку
            error_result = {
                "task_id": task.get("id", "unknown"),
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "agent": self.name
            }
            
            await asyncio.to_thread(
                self.redis_client.lpush,
                f"results_{task.get('id', 'unknown')}",
                json.dumps(error_result)
            )

    async def _generate_text(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Генерация текста с помощью модели"""
        try:
            # Обновляем конфигурацию генерации
            generation_config = self.generation_config.copy()
            generation_config.update({
                "max_new_tokens": max_tokens,
                "temperature": temperature
            })
            
            # Генерируем в отдельном потоке для не блокирования
            def generate():
                outputs = self.pipeline(
                    prompt,
                    **generation_config,
                    return_full_text=False
                )
                return outputs[0]["generated_text"]
            
            result = await asyncio.to_thread(generate)
            
            logger.debug(f"Сгенерирован текст длиной {len(result)} символов")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка генерации текста: {e}")
            raise

    async def process_message(self, message: AgentMessage) -> Dict[str, any]:
        """Обработка входящих сообщений"""
        try:
            if message.message_type == "task":
                # Добавляем задачу в очередь
                await asyncio.to_thread(
                    self.redis_client.lpush,
                    f"tasks_{self.name}",
                    json.dumps(message.content)
                )
                return {"status": "queued", "message": "Задача добавлена в очередь"}
                
            elif message.message_type == "generate":
                # Прямая генерация текста
                prompt = message.content.get("prompt", "")
                max_tokens = message.content.get("max_tokens", 512)
                temperature = message.content.get("temperature", 0.7)
                
                result = await self._generate_text(prompt, max_tokens, temperature)
                
                return {
                    "status": "completed",
                    "generated_text": result,
                    "prompt_length": len(prompt),
                    "response_length": len(result)
                }
                
            elif message.message_type == "status":
                # Запрос статуса
                return {
                    "agent_name": self.name,
                    "model": self.config.model_name,
                    "status": self.status,
                    "memory_usage": await self._get_memory_usage(),
                    "error_count": self.error_count
                }
                
            else:
                return {"status": "unknown", "message": "Неизвестный тип сообщения"}
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения в LLMAgent: {e}")
            return {"status": "error", "message": str(e)}

    async def generate_response(self, user_input: str, context: Optional[str] = None) -> str:
        """Публичный метод для генерации ответа"""
        try:
            # Формируем промпт с контекстом
            if context:
                prompt = f"Контекст: {context}\n\nВопрос: {user_input}\n\nОтвет:"
            else:
                prompt = f"Вопрос: {user_input}\n\nОтвет:"
            
            response = await self._generate_text(prompt, max_tokens=1024)
            
            # Сохраняем в память для контекста
            await self.save_memory(
                f"conversation_{int(asyncio.get_event_loop().time())}",
                {"user_input": user_input, "response": response}
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return f"Извините, произошла ошибка при генерации ответа: {str(e)}"


if __name__ == "__main__":
    # Запуск LLMAgent
    async def main():
        llm_agent = LLMAgent()
        await llm_agent.run()
    
    asyncio.run(main())



