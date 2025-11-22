"""
Настройки контент-завода
"""

import os
from typing import Dict, Any, List
from pydantic import BaseSettings


class ContentFactorySettings(BaseSettings):
    """Настройки контент-завода"""
    
    # Общие настройки
    PROJECT_NAME: str = "Контент-завод"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Пути
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    OUTPUT_DIR: str = os.path.join(BASE_DIR, "output")
    TEMPLATES_DIR: str = os.path.join(BASE_DIR, "templates")
    STATIC_DIR: str = os.path.join(BASE_DIR, "static")
    
    # База данных
    DB_PATH: str = os.path.join(DATA_DIR, "content_factory.db")
    
    # AI модели (бесплатные, локальные)
    AI_MODELS: Dict[str, Dict[str, Any]] = {
        "text_generation": {
            "type": "local",
            "model": "microsoft/phi-2",  # Бесплатная локальная модель
            "fallback": "gpt-3.5-turbo",  # Если есть API ключ
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "text_embedding": {
            "type": "local",
            "model": "sentence-transformers/all-MiniLM-L6-v2"
        },
        "image_generation": {
            "type": "local",
            "model": "runwayml/stable-diffusion-v1-5",
            "fallback": "dall-e-2"  # Если есть API ключ
        },
        "seo_analysis": {
            "type": "local",
            "model": "microsoft/phi-2"
        }
    }
    
    # API ключи (опционально)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    YANDEX_GPT_API_KEY: str = os.getenv("YANDEX_GPT_API_KEY", "")
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    
    # Настройки контента
    DEFAULT_CONTENT_FORMATS: List[str] = ["article", "post", "video", "infographic"]
    DEFAULT_LANGUAGES: List[str] = ["ru", "en"]
    
    # Настройки планирования
    CONTENT_PLAN_DAYS_AHEAD: int = 90
    MIN_IDEAS_PER_TOPIC: int = 10
    
    # Настройки качества
    MIN_ARTICLE_LENGTH: int = 1000
    MAX_ARTICLE_LENGTH: int = 5000
    REQUIRED_SEO_ELEMENTS: List[str] = ["title", "meta_description", "h1", "keywords"]
    
    # Настройки дистрибуции
    SOCIAL_MEDIA_PLATFORMS: List[str] = ["telegram", "vk", "ok", "youtube"]
    AUTO_PUBLISH: bool = False
    SCHEDULE_PUBLISH: bool = True
    
    # Настройки аналитики
    ANALYTICS_ENABLED: bool = True
    METRICS_RETENTION_DAYS: int = 365
    
    # Веб-интерфейс
    WEB_HOST: str = "0.0.0.0"
    WEB_PORT: int = 8502
    
    # Логирование
    LOG_LEVEL: str = "INFO"
    LOG_PATH: str = os.path.join(BASE_DIR, "logs")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Глобальный экземпляр настроек
settings = ContentFactorySettings()

# Создание необходимых директорий
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
os.makedirs(settings.TEMPLATES_DIR, exist_ok=True)
os.makedirs(settings.STATIC_DIR, exist_ok=True)
os.makedirs(settings.LOG_PATH, exist_ok=True)
