"""
TextAgent - обработка текста с помощью Phi-2 (CPU-only)
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from .base_agent import BaseAgent, Task


class TextAgent(BaseAgent):
    """Агент для обработки текста"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("text_agent", config)
        self.model_path = config.get('models_path', '/app/models')
        self.model_name = "microsoft/phi-2"
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForCausalLM] = None
        self.device = "cpu"  # CPU-only
        self.max_length = 2048
        
    async def _initialize_agent(self):
        """Инициализация TextAgent"""
        self.logger.info("Инициализация TextAgent")
        
        # Загрузка модели Phi-2
        await self._load_model()
        
        self.logger.info("TextAgent успешно инициализирован")
    
    async def _load_model(self):
        """Загрузка модели Phi-2"""
        try:
            model_file = os.path.join(self.model_path, "phi_2")
            
            self.logger.info(f"Загрузка Phi-2 из {model_file}")
            
            # Загрузка токенизатора
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_file if os.path.exists(model_file) else self.model_name,
                trust_remote_code=True
            )
            
            # Загрузка модели
            self.model = AutoModelForCausalLM.from_pretrained(
                model_file if os.path.exists(model_file) else self.model_name,
                torch_dtype=torch.float32,  # CPU совместимость
                trust_remote_code=True,
                device_map="cpu"
            )
            
            self.logger.info("Phi-2 загружен успешно")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {e}")
            raise
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Обработка задач обработки текста"""
        if task.task_type == "text_generation":
            return await self._generate_text(task)
        elif task.task_type == "text_completion":
            return await self._complete_text(task)
        elif task.task_type == "text_analysis":
            return await self._analyze_text(task)
        elif task.task_type == "text_summarization":
            return await self._summarize_text(task)
        elif task.task_type == "text_translation":
            return await self._translate_text(task)
        
        return {"status": "unknown_task_type"}
    
    async def _generate_text(self, task: Task) -> Dict[str, Any]:
        """Генерация текста"""
        try:
            prompt = task.data.get("prompt", "")
            max_length = task.data.get("max_length", self.max_length)
            temperature = task.data.get("temperature", 0.7)
            top_p = task.data.get("top_p", 0.9)
            do_sample = task.data.get("do_sample", True)
            
            if not prompt:
                return {"status": "error", "error": "Пустой промпт"}
            
            self.logger.info(f"Генерация текста для промпта: {prompt[:100]}...")
            
            # Токенизация
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            
            # Генерация
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=do_sample,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    no_repeat_ngram_size=3
                )
            
            # Декодирование
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Удаление исходного промпта из результата
            result_text = generated_text[len(prompt):].strip()
            
            return {
                "status": "success",
                "generated_text": result_text,
                "full_text": generated_text,
                "prompt": prompt,
                "metadata": {
                    "max_length": max_length,
                    "temperature": temperature,
                    "top_p": top_p,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации текста: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _complete_text(self, task: Task) -> Dict[str, Any]:
        """Завершение текста"""
        try:
            text = task.data.get("text", "")
            max_completion_length = task.data.get("max_completion_length", 200)
            
            if not text:
                return {"status": "error", "error": "Пустой текст"}
            
            # Добавление промпта для завершения
            prompt = f"Complete the following text:\n\n{text}\n\nCompletion:"
            
            return await self._generate_text(Task(
                id=task.id,
                agent_name=task.agent_name,
                task_type="text_generation",
                data={"prompt": prompt, "max_length": len(text) + max_completion_length}
            ))
            
        except Exception as e:
            self.logger.error(f"Ошибка завершения текста: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _analyze_text(self, task: Task) -> Dict[str, Any]:
        """Анализ текста"""
        try:
            text = task.data.get("text", "")
            analysis_type = task.data.get("analysis_type", "general")
            
            if not text:
                return {"status": "error", "error": "Пустой текст"}
            
            # Простой анализ текста
            word_count = len(text.split())
            char_count = len(text)
            sentence_count = text.count('.') + text.count('!') + text.count('?')
            
            # Определение тональности (упрощенная версия)
            positive_words = ['хорошо', 'отлично', 'прекрасно', 'замечательно', 'великолепно']
            negative_words = ['плохо', 'ужасно', 'отвратительно', 'кошмар', 'проблема']
            
            positive_score = sum(1 for word in positive_words if word.lower() in text.lower())
            negative_score = sum(1 for word in negative_words if word.lower() in text.lower())
            
            sentiment = "neutral"
            if positive_score > negative_score:
                sentiment = "positive"
            elif negative_score > positive_score:
                sentiment = "negative"
            
            return {
                "status": "success",
                "analysis": {
                    "word_count": word_count,
                    "character_count": char_count,
                    "sentence_count": sentence_count,
                    "sentiment": sentiment,
                    "positive_score": positive_score,
                    "negative_score": negative_score,
                    "average_word_length": char_count / word_count if word_count > 0 else 0
                },
                "metadata": {
                    "analysis_type": analysis_type,
                    "analyzed_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа текста: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _summarize_text(self, task: Task) -> Dict[str, Any]:
        """Суммаризация текста"""
        try:
            text = task.data.get("text", "")
            max_summary_length = task.data.get("max_summary_length", 150)
            
            if not text:
                return {"status": "error", "error": "Пустой текст"}
            
            # Промпт для суммаризации
            prompt = f"Summarize the following text in no more than {max_summary_length} words:\n\n{text}\n\nSummary:"
            
            result = await self._generate_text(Task(
                id=task.id,
                agent_name=task.agent_name,
                task_type="text_generation",
                data={"prompt": prompt, "max_length": max_summary_length + 100}
            ))
            
            if result["status"] == "success":
                result["summary"] = result["generated_text"]
                result["original_length"] = len(text.split())
                result["summary_length"] = len(result["generated_text"].split())
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка суммаризации: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _translate_text(self, task: Task) -> Dict[str, Any]:
        """Перевод текста"""
        try:
            text = task.data.get("text", "")
            target_language = task.data.get("target_language", "English")
            source_language = task.data.get("source_language", "Russian")
            
            if not text:
                return {"status": "error", "error": "Пустой текст"}
            
            # Промпт для перевода
            prompt = f"Translate the following text from {source_language} to {target_language}:\n\n{text}\n\nTranslation:"
            
            result = await self._generate_text(Task(
                id=task.id,
                agent_name=task.agent_name,
                task_type="text_generation",
                data={"prompt": prompt, "max_length": len(text) + 200}
            ))
            
            if result["status"] == "success":
                result["translation"] = result["generated_text"]
                result["source_language"] = source_language
                result["target_language"] = target_language
            
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка перевода: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _cleanup_agent(self):
        """Очистка ресурсов TextAgent"""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        self.logger.info("TextAgent очищен")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о модели"""
        return {
            "model_name": "Phi-2",
            "device": self.device,
            "loaded": self.model is not None,
            "max_length": self.max_length
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья агента"""
        return {
            "status": "healthy" if self.model is not None else "error",
            "model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None,
            "device": self.device
        }

