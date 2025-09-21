"""
Конфигурация чата с нейросетью для AGI Layer v3.9
"""

from typing import Dict, List, Any
import json
from .settings import settings


# Конфигурации персональностей для чата
PERSONALITY_CONFIGS = {
    "helpful_assistant": {
        "name": "Полезный помощник",
        "description": "Отвечаю четко, информативно и по делу",
        "system_prompt": "Ты полезный AI-помощник. Отвечай четко, информативно и по делу. Используй факты и логику.",
        "temperature": 0.7,
        "max_tokens": 512,
        "style_markers": ["четкость", "информативность", "конкретность"]
    },
    
    "friendly_companion": {
        "name": "Дружелюбный собеседник", 
        "description": "Общаюсь тепло, эмоционально, используя эмодзи",
        "system_prompt": "Ты дружелюбный собеседник. Общайся тепло, эмоционально, используй эмодзи. Будь открытым и понимающим.",
        "temperature": 0.8,
        "max_tokens": 512,
        "style_markers": ["эмоциональность", "теплота", "эмодзи", "понимание"]
    },
    
    "professional_expert": {
        "name": "Профессиональный эксперт",
        "description": "Даю экспертные советы и детальные объяснения", 
        "system_prompt": "Ты профессиональный эксперт. Давай экспертные советы, детальные объяснения и анализируй проблемы глубоко.",
        "temperature": 0.6,
        "max_tokens": 768,
        "style_markers": ["экспертность", "детальность", "анализ", "профессионализм"]
    },
    
    "creative_writer": {
        "name": "Творческий писатель",
        "description": "Отвечаю красиво, образно, используя метафоры",
        "system_prompt": "Ты творческий писатель. Отвечай красиво, образно, используй метафоры и яркие описания.",
        "temperature": 0.9,
        "max_tokens": 768,
        "style_markers": ["образность", "метафоры", "красота", "творчество"]
    },
    
    "technical_specialist": {
        "name": "Технический специалист", 
        "description": "Фокусируюсь на технических деталях и точности",
        "system_prompt": "Ты технический специалист. Фокусируйся на технических деталях, точности и практических решениях.",
        "temperature": 0.5,
        "max_tokens": 1024,
        "style_markers": ["техничность", "точность", "детали", "практичность"]
    }
}


# Настройки обработки изображений в чате
IMAGE_PROCESSING_CONFIG = {
    "enabled": settings.ENABLE_IMAGE_PROCESSING,
    "max_file_size_mb": 10,
    "supported_formats": ["jpg", "jpeg", "png", "webp", "gif"],
    "analysis_timeout": 30,
    "default_analysis_type": "detailed_description",
    "response_template": "🖼️ **Анализ изображения:**\n\n{analysis}\n\n{response}"
}


# Настройки голосовых сообщений
VOICE_PROCESSING_CONFIG = {
    "enabled": settings.ENABLE_VOICE_MESSAGES,
    "max_duration_seconds": 60,
    "supported_formats": ["ogg", "mp3", "wav", "m4a"],
    "transcription_timeout": 45,
    "auto_response": True
}


# Конфигурация контекста разговора
CONTEXT_CONFIG = {
    "max_messages": settings.MAX_CONTEXT_MESSAGES,
    "context_window_hours": 24,
    "include_system_messages": False,
    "summarize_old_context": True,
    "summary_threshold": 20  # Количество сообщений для суммаризации
}


# Настройки модерации контента
MODERATION_CONFIG = {
    "enabled": True,
    "check_user_messages": True,
    "check_ai_responses": True,
    "blocked_words": [],  # Список заблокированных слов
    "max_message_length": 4000,
    "rate_limit_messages_per_minute": 10,
    "rate_limit_images_per_hour": 20
}


# Настройки уведомлений и статистики
NOTIFICATION_CONFIG = {
    "send_daily_stats": True,
    "send_error_notifications": True,
    "stats_time": "09:00",  # Время отправки ежедневной статистики
    "admin_chat_ids": [],  # Чаты администраторов для уведомлений
    "maintenance_notifications": True
}


# Команды чата
CHAT_COMMANDS = {
    "start": {
        "description": "Начать общение с AGI Assistant",
        "usage": "/start",
        "category": "основные"
    },
    "help": {
        "description": "Показать справку по командам",
        "usage": "/help",
        "category": "основные"
    },
    "personality": {
        "description": "Выбрать стиль общения",
        "usage": "/personality [стиль]",
        "category": "настройки",
        "options": list(PERSONALITY_CONFIGS.keys())
    },
    "clear": {
        "description": "Очистить контекст разговора",
        "usage": "/clear",
        "category": "управление"
    },
    "settings": {
        "description": "Показать настройки пользователя",
        "usage": "/settings",
        "category": "настройки"
    },
    "stats": {
        "description": "Показать статистику использования",
        "usage": "/stats",
        "category": "информация"
    },
    "generate": {
        "description": "Генерация изображения",
        "usage": "/generate [описание]",
        "category": "творчество"
    },
    "analyze": {
        "description": "Анализ изображения (отправьте фото)",
        "usage": "Отправьте изображение",
        "category": "анализ"
    }
}


# Шаблоны сообщений
MESSAGE_TEMPLATES = {
    "welcome": """🤖 Привет, {user_name}! 

Я - AGI Assistant на базе нейросети Phi-2. Готов к общению!

🔥 Мои возможности:
• 💬 Естественное общение на русском и английском
• 🖼️ Анализ изображений (отправь фото)
• 🎨 Генерация изображений (/generate описание)
• 📝 Помощь с текстами, кодом, переводом
• 🧠 Запоминаю контекст разговора

⚙️ Команды:
/help - справка по командам
/personality - выбрать стиль общения
/clear - очистить контекст
/settings - настройки
/stats - статистика

Просто пиши мне сообщения - отвечу как можно лучше! 😊""",

    "help": """🤖 AGI Assistant - Справка

📝 Основные команды:
/start - Начать общение
/help - Эта справка
/personality [стиль] - Выбрать стиль общения
/clear - Очистить контекст разговора
/settings - Настройки пользователя
/stats - Статистика использования
/generate [описание] - Генерация изображения

🎭 Доступные стили общения:
{personalities}

💬 Как использовать:
• Просто пишите сообщения - я отвечу в выбранном стиле
• Отправляйте изображения - я их проанализирую
• Задавайте любые вопросы - постараюсь помочь

🔧 Настройки:
• Длина контекста: до {max_context} сообщений
• Поддержка изображений: {'включена' if settings.ENABLE_IMAGE_PROCESSING else 'отключена'}
• Язык ответов: автоопределение""",

    "personality_changed": "✅ Стиль общения изменен на: **{personality_name}**\n\n{personality_description}",

    "context_cleared": "🧹 Контекст разговора очищен! Начинаем общение с чистого листа.",

    "error_general": "😔 Произошла ошибка при обработке сообщения. Попробуйте еще раз или обратитесь к администратору.",

    "error_timeout": "⏰ Превышено время ожидания ответа. Попробуйте еще раз.",

    "error_image_processing": "🖼️ Не удалось обработать изображение. Убедитесь, что файл не поврежден и имеет поддерживаемый формат.",

    "rate_limit": "⚠️ Слишком много сообщений! Подождите немного перед отправкой следующего.",

    "access_denied": "❌ Доступ запрещен. Обратитесь к администратору для получения разрешения."
}


def get_personality_config(personality: str) -> Dict[str, Any]:
    """Получить конфигурацию персональности"""
    return PERSONALITY_CONFIGS.get(personality, PERSONALITY_CONFIGS["helpful_assistant"])


def get_allowed_chat_ids() -> List[int]:
    """Получить список разрешенных чатов"""
    try:
        return json.loads(settings.TELEGRAM_ALLOWED_CHATS)
    except (json.JSONDecodeError, AttributeError):
        return []


def format_message_template(template_name: str, **kwargs) -> str:
    """Форматировать шаблон сообщения"""
    template = MESSAGE_TEMPLATES.get(template_name, "")
    
    # Добавление стандартных переменных
    kwargs.update({
        "max_context": settings.MAX_CONTEXT_MESSAGES,
        "personalities": "\n".join([
            f"• {k} - {v['description']}" 
            for k, v in PERSONALITY_CONFIGS.items()
        ])
    })
    
    try:
        return template.format(**kwargs)
    except KeyError as e:
        return f"Ошибка форматирования шаблона {template_name}: отсутствует переменная {e}"


def validate_chat_config() -> Dict[str, bool]:
    """Проверка конфигурации чата"""
    checks = {
        "telegram_token_set": bool(settings.TELEGRAM_TOKEN),
        "personalities_valid": all(
            isinstance(config, dict) and "system_prompt" in config 
            for config in PERSONALITY_CONFIGS.values()
        ),
        "image_processing_config": isinstance(IMAGE_PROCESSING_CONFIG, dict),
        "context_config_valid": CONTEXT_CONFIG["max_messages"] > 0,
        "moderation_enabled": MODERATION_CONFIG["enabled"]
    }
    
    return checks


# Экспорт основных конфигураций
__all__ = [
    "PERSONALITY_CONFIGS",
    "IMAGE_PROCESSING_CONFIG", 
    "VOICE_PROCESSING_CONFIG",
    "CONTEXT_CONFIG",
    "MODERATION_CONFIG",
    "NOTIFICATION_CONFIG",
    "CHAT_COMMANDS",
    "MESSAGE_TEMPLATES",
    "get_personality_config",
    "get_allowed_chat_ids",
    "format_message_template",
    "validate_chat_config"
]