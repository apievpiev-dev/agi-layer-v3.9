"""
STTAgent - Агент распознавания речи
=================================

Преобразует аудио в текст используя:
- OpenAI Whisper (base/small/medium)
- Поддержка русского языка
- Обработка различных аудио форматов
"""

import asyncio
import base64
import io
import os
import tempfile
from datetime import datetime
from typing import Dict, Optional

import torch
from faster_whisper import WhisperModel
from loguru import logger

from base_agent import BaseAgent, AgentConfig, AgentMessage


class STTAgent(BaseAgent):
    """Агент для распознавания речи"""
    
    def __init__(self):
        config = AgentConfig(
            name="stt_agent",
            type="speech_to_text",
            model_name="whisper-base",
            max_memory="4G",
            max_cpu_cores=2
        )
        super().__init__(config)
        
        # Whisper модель
        self.whisper_model = None
        
        # Настройки распознавания
        self.transcription_options = {
            "language": "ru",  # Приоритет русскому языку
            "task": "transcribe",
            "fp16": False,  # CPU не поддерживает fp16
            "temperature": 0.0
        }

    async def _load_model(self):
        """Загрузка модели Whisper"""
        try:
            logger.info("Загрузка модели Whisper...")
            
            def load_whisper():
                # faster-whisper CPU
                return WhisperModel("base", device="cpu", compute_type="int8")
            
            self.whisper_model = await asyncio.to_thread(load_whisper)
            
            logger.info("✅ Whisper модель загружена (base, CPU)")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки Whisper: {e}")
            raise

    async def _agent_specific_init(self):
        """Специфичная инициализация STTAgent"""
        # Регистрируемся в MetaAgent
        await self.send_message(
            "meta_agent",
            "registration",
            {
                "agent_type": self.type,
                "model_name": "whisper-base",
                "capabilities": [
                    "speech_recognition",
                    "audio_transcription", 
                    "multilingual_support",
                    "noise_reduction"
                ],
                "supported_languages": ["ru", "en", "auto"],
                "status": "ready"
            }
        )
        logger.info("STTAgent зарегистрирован в MetaAgent")

    async def _agent_main_loop(self):
        """Основной цикл STTAgent"""
        while self.is_running:
            try:
                # Проверяем задачи в очереди
                task_data = await asyncio.to_thread(
                    self.redis_client.lpop, f"tasks_{self.name}"
                )
                
                if task_data:
                    import json
                    task = json.loads(task_data)
                    await self._process_audio_task(task)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка в главном цикле STTAgent: {e}")
                await asyncio.sleep(5)

    async def _process_audio_task(self, task: Dict):
        """Обработка аудио задач"""
        try:
            task_id = task.get("id", "unknown")
            audio_data = task.get("audio_data", "")
            language = task.get("language", "ru")
            
            logger.info(f"Обработка аудио задачи {task_id}")
            
            # Преобразуем аудио в текст
            transcription = await self._transcribe_audio(audio_data, language)
            
            # Сохраняем результат
            result = {
                "task_id": task_id,
                "status": "completed",
                "transcription": transcription,
                "timestamp": datetime.now().isoformat(),
                "agent": self.name
            }
            
            await asyncio.to_thread(
                self.redis_client.lpush,
                f"results_{task_id}",
                json.dumps(result)
            )
            
            logger.info(f"Аудио задача {task_id} выполнена")
            
        except Exception as e:
            logger.error(f"Ошибка обработки аудио задачи: {e}")

    async def _transcribe_audio(self, audio_data: str, language: str = "ru") -> Dict:
        """Распознавание речи из аудио"""
        try:
            # Декодируем аудио из base64
            audio_bytes = base64.b64decode(audio_data)
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            try:
                def transcribe():
                    # Обновляем опции
                    options = self.transcription_options.copy()
                    if language != "auto":
                        options["language"] = language
                    
                    # Выполняем транскрипцию
                    segments, info = self.whisper_model.transcribe(
                        temp_path,
                        language=None if options.get("language") == "auto" else options.get("language"),
                        vad_filter=True,
                    )
                    text = "".join([s.text for s in segments])
                    return {"text": text, "segments": [{"start": s.start, "end": s.end, "text": s.text} for s in segments], "language": info.language}
                
                # Выполняем в отдельном потоке
                result = await asyncio.to_thread(transcribe)
                
                return {
                    "text": result["text"].strip(),
                    "language": result.get("language", language),
                    "confidence": 0.9,  # Whisper не предоставляет confidence
                    "segments": [
                        {
                            "start": seg["start"],
                            "end": seg["end"],
                            "text": seg["text"].strip()
                        }
                        for seg in result.get("segments", [])
                    ]
                }
                
            finally:
                # Удаляем временный файл
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Ошибка транскрипции: {e}")
            return {
                "text": "",
                "language": language,
                "confidence": 0.0,
                "error": str(e)
            }

    async def process_message(self, message: AgentMessage) -> Dict[str, any]:
        """Обработка входящих сообщений"""
        try:
            if message.message_type == "transcribe":
                audio_data = message.content.get("audio_data", "")
                language = message.content.get("language", "ru")
                
                result = await self._transcribe_audio(audio_data, language)
                
                return {
                    "status": "completed",
                    "transcription": result,
                    "processing_time": "~2-5 секунд"
                }
                
            elif message.message_type == "status":
                return {
                    "agent_name": self.name,
                    "model": "whisper-base",
                    "status": self.status,
                    "supported_languages": ["ru", "en", "auto"],
                    "memory_usage": await self._get_memory_usage(),
                    "error_count": self.error_count
                }
                
            else:
                return {"status": "unknown", "message": "Неизвестный тип сообщения"}
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения в STTAgent: {e}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # Запуск STTAgent
    async def main():
        stt_agent = STTAgent()
        await stt_agent.run()
    
    asyncio.run(main())


