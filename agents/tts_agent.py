"""
TTSAgent - Синтез речи (CPU)
============================

Использует Silero TTS для генерации речи на русском/английском.
"""

import asyncio
from typing import Dict

import torch
from loguru import logger

from base_agent import BaseAgent, AgentConfig, AgentMessage


class TTSAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="tts_agent",
            type="text_to_speech",
            model_name="silero-tts",
            max_memory="2G",
            max_cpu_cores=2,
        )
        super().__init__(config)

        self.model = None
        self.sample_rate = 48000

    async def _load_model(self):
        try:
            logger.info("Загрузка Silero TTS...")

            def load_silero():
                device = torch.device("cpu")
                torch.set_num_threads(2)
                model, example_text = torch.hub.load(
                    repo_or_dir="snakers4/silero-models",
                    model="silero_tts",
                    language="ru",
                )
                model.to(device)
                return model

            self.model = await asyncio.to_thread(load_silero)
            logger.info("✅ Silero TTS готов (CPU)")

        except Exception as e:
            logger.error(f"Ошибка загрузки Silero TTS: {e}")
            raise

    async def _agent_specific_init(self):
        await self.send_message(
            "meta_agent",
            "registration",
            {
                "agent_type": self.type,
                "model_name": "silero-tts",
                "capabilities": ["text_to_speech"],
                "status": "ready",
            },
        )

    async def _agent_main_loop(self):
        """Основной цикл обработки входящих сообщений"""
        while self.is_running:
            message = await self.receive_message()
            if message:
                response = await self.process_message(message)
                if response is not None:
                    await self.send_message(message.sender, "response", response)
            await asyncio.sleep(0.2)

    async def process_message(self, message: AgentMessage) -> Dict[str, any]:
        try:
            if message.message_type == "speak":
                text = message.content.get("text", "")
                speaker = message.content.get("speaker", "baya")

                if not text:
                    return {"status": "error", "message": "Текст пуст"}

                def synthesize():
                    with torch.no_grad():
                        audio = self.model.apply_tts(
                            text=text,
                            speaker=speaker,
                            sample_rate=self.sample_rate,
                        )
                        return audio.numpy()

                audio_np = await asyncio.to_thread(synthesize)
                # Возвращаем как простой список чисел (клиент сам решит, как сохранить)
                return {
                    "status": "completed",
                    "sample_rate": self.sample_rate,
                    "audio": audio_np.tolist(),
                }

            elif message.message_type == "status":
                return {
                    "agent_name": self.name,
                    "model": "silero-tts",
                    "status": self.status,
                    "memory_usage": await self._get_memory_usage(),
                    "error_count": self.error_count,
                }

            return {"status": "unknown", "message": "Неизвестный тип сообщения"}

        except Exception as e:
            logger.error(f"Ошибка в TTSAgent: {e}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    async def main():
        agent = TTSAgent()
        await agent.run()

    asyncio.run(main())



