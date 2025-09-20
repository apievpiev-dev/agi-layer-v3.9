"""
Основные настройки AGI Layer v3.9
"""

import os
from typing import Dict, Any
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Основные настройки системы"""
    
    # Общие настройки
    PROJECT_NAME: str = "AGI Layer v3.9"
    VERSION: str = "3.9.0"
    DEBUG: bool = False
    
    # Настройки базы данных PostgreSQL
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "agi_layer"
    POSTGRES_USER: str = "agi_user"
    POSTGRES_PASSWORD: str = "agi_password"
    
    # Настройки ChromaDB
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION: str = "agi_memory"
    
    # Настройки Redis (для будущего расширения)
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    
    # Настройки Telegram
    TELEGRAM_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # Настройки Web UI
    WEB_UI_HOST: str = "0.0.0.0"
    WEB_UI_PORT: int = 8501
    
    # Настройки моделей
    MODELS_PATH: str = "/app/models"
    DOWNLOAD_MODELS_ON_START: bool = True
    
    # Настройки логирования
    LOG_LEVEL: str = "INFO"
    LOG_PATH: str = "/app/logs"
    
    # Настройки безопасности
    SECRET_KEY: str = "your-secret-key-here"
    ALLOWED_HOSTS: list = ["*"]
    
    # Настройки агентов
    AGENT_LOOP_INTERVAL: float = 1.0
    AGENT_TIMEOUT: int = 300
    MAX_CONCURRENT_TASKS: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Глобальный экземпляр настроек
settings = Settings()


def get_database_config() -> Dict[str, Any]:
    """Конфигурация PostgreSQL"""
    return {
        "host": settings.POSTGRES_HOST,
        "port": settings.POSTGRES_PORT,
        "database": settings.POSTGRES_DB,
        "user": settings.POSTGRES_USER,
        "password": settings.POSTGRES_PASSWORD
    }


def get_chroma_config() -> Dict[str, Any]:
    """Конфигурация ChromaDB"""
    return {
        "host": settings.CHROMA_HOST,
        "port": settings.CHROMA_PORT,
        "collection": settings.CHROMA_COLLECTION
    }


def get_redis_config() -> Dict[str, Any]:
    """Конфигурация Redis"""
    return {
        "host": settings.REDIS_HOST,
        "port": settings.REDIS_PORT,
        "password": settings.REDIS_PASSWORD
    }

