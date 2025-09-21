# 🤖 AGI Layer v3.9 - Чат с нейросетями в Telegram

## 💬 Telegram Чат-бот с нейросетями

**Готов к использованию!** Полноценный ИИ-ассистент в Telegram с поддержкой:
- 🧠 **Интеллектуального диалога** (Phi-2)
- 🎨 **Генерации изображений** (Stable Diffusion 1.5) 
- 👁️ **Анализа изображений** (BLIP2)

### 🚀 Быстрый запуск чат-бота:
```bash
# Windows
START_CHAT_BOT.bat

# Linux/Mac
./start_chat_bot.sh

# Тестирование без Telegram
python3 simple_chat_demo.py
```

**📖 Подробная документация:** [TELEGRAM_CHAT_GUIDE.md](TELEGRAM_CHAT_GUIDE.md)

---

## 🏗️ Архитектура AGI Layer

Headless AGI-инфраструктура с управлением через Telegram/Web UI, самообучением, памятью и рефлексией.

## Архитектура

### Основные компоненты:
- **MetaAgent** - координация всех агентов
- **RecoveryAgent** - восстановление из логов и ChromaDB
- **ImageAgent** - генерация изображений (Stable Diffusion 1.5)
- **TextAgent** - обработка текста (Phi-2)
- **VisionAgent** - анализ изображений (BLIP2)
- **OCRAgent** - распознавание текста (EasyOCR)
- **EmbeddingAgent** - векторизация (SentenceTransformers)

### CPU-Only модели:
- Stable Diffusion 1.5
- Phi-2 (LLM)
- BLIP2 (Vision)
- EasyOCR
- SentenceTransformers

### Хранение данных:
- **PostgreSQL** - краткосрочная память
- **ChromaDB** - векторная память
- **JSON-логи** - в /logs

### Управление:
- **Telegram Bot** - команды /start, /status, /generate, /report, /reboot
- **Web UI** - Streamlit/FastAPI интерфейс

## Структура проекта

```
agi-layer-v3.9/
├── agents/                 # Все агенты
│   ├── base_agent.py      # Базовый класс
│   ├── meta_agent.py      # Координатор
│   ├── recovery_agent.py  # Восстановление
│   ├── image_agent.py     # Генерация изображений
│   ├── text_agent.py      # Обработка текста
│   ├── vision_agent.py    # Анализ изображений
│   ├── ocr_agent.py       # OCR
│   └── embedding_agent.py # Векторизация
├── services/              # Вспомогательные сервисы
│   ├── database.py        # PostgreSQL
│   ├── vector_db.py       # ChromaDB
│   ├── telegram_bot.py    # Telegram интеграция
│   ├── web_ui.py          # Web интерфейс
│   └── watchdog.py        # Контроль контейнеров
├── config/                # Конфигурации
│   ├── settings.py        # Основные настройки
│   ├── models.py          # Конфигурация моделей
│   └── database.py        # БД настройки
├── templates/             # Шаблоны агентов
│   └── agent_template.py  # Шаблон для создания
├── scripts/               # Скрипты
│   ├── download_models.py # Загрузка моделей
│   ├── setup.sh          # Развертывание
│   └── backup.py         # Бэкапы
├── logs/                  # Логи
├── models/                # Загруженные модели
├── docker-compose.yml     # Контейнеризация
├── Dockerfile            # Основной образ
├── requirements.txt      # Зависимости
└── .env.example         # Пример конфигурации
```

## Быстрый старт

1. Клонировать репозиторий
2. Скопировать `.env.example` в `.env` и настроить
3. Запустить `./scripts/setup.sh`
4. Запустить `docker-compose up -d`

## Особенности

- **Полностью CPU** - работает без GPU
- **Автоматическое восстановление** - из логов и векторной БД
- **Модульная архитектура** - легкое добавление новых агентов
- **Telegram управление** - удаленное администрирование
- **Web мониторинг** - визуальный контроль состояния
- **Векторная память** - долгосрочное хранение знаний

