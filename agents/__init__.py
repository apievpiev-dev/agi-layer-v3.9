"""
AGI Layer v3.9 - Agents Module
================================

Модуль содержит все агенты AI системы:
- BaseAgent: Базовый класс для всех агентов
- MetaAgent: Координатор агентов
- LLMAgent: Языковая модель
- VisionAgent: Компьютерное зрение
- ImageGenAgent: Генерация изображений
- TTSAgent: Синтез речи
- STTAgent: Распознавание речи
- RecoveryAgent: Восстановление системы
- CreatorAgent: Создание новых агентов
"""

from base_agent import BaseAgent
from meta_agent import MetaAgent

__version__ = "3.9.0"
__author__ = "AGI Layer Team"

__all__ = [
    "BaseAgent",
    "MetaAgent",
]






