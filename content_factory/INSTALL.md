# 📦 Установка контент-завода

## Системные требования

- Python 3.8 или выше
- 2+ ГБ свободного места на диске
- 4+ ГБ RAM (для локальных AI моделей)

## Установка

### 1. Клонирование/копирование

Если проект уже в вашей системе, перейдите в папку `content_factory`.

### 2. Установка зависимостей

```bash
# Базовые зависимости (обязательно)
pip install streamlit pydantic python-dotenv requests Pillow

# Для работы с AI (опционально, но рекомендуется)
pip install transformers sentence-transformers torch

# Для работы с данными (опционально)
pip install pandas numpy
```

Или установите все сразу:

```bash
pip install -r requirements.txt
```

### 3. Инициализация системы

```bash
python content_factory/main.py --mode init
```

Это создаст:
- Базу данных SQLite
- Необходимые директории
- Структуру таблиц

### 4. Настройка (опционально)

Создайте файл `.env` в корне проекта:

```env
# API ключи (опционально)
OPENAI_API_KEY=your_key_here
YANDEX_GPT_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here

# Настройки (опционально)
DEBUG=False
LOG_LEVEL=INFO
```

## Запуск

### Веб-интерфейс (рекомендуется)

```bash
python content_factory/main.py --mode web
```

Откройте браузер: http://localhost:8502

### CLI режим

```bash
python content_factory/main.py --mode cli
```

## Проверка установки

Запустите пример:

```bash
python content_factory/example_usage.py
```

Если все работает, вы увидите пример полного цикла производства контента.

## Устранение проблем

### Ошибка импорта модулей

Убедитесь, что вы находитесь в корневой директории проекта:

```bash
cd /workspace
python content_factory/main.py --mode init
```

### Ошибка с AI моделями

Если локальные модели не загружаются:
1. Проверьте подключение к интернету (модели загружаются автоматически)
2. Укажите API ключи в `.env` для использования внешних API
3. Или используйте систему без AI (ограниченный функционал)

### Ошибка с базой данных

Удалите базу данных и переинициализируйте:

```bash
rm content_factory/data/content_factory.db
python content_factory/main.py --mode init
```

## Дополнительная настройка

### Использование локальных AI моделей

Модели загружаются автоматически при первом использовании. Для ускорения можно скачать заранее:

```python
from transformers import pipeline
pipeline("text-generation", model="microsoft/phi-2")
```

### Интеграция с внешними сервисами

Для публикации на реальных платформах нужно:
1. Настроить API ключи в соответствующих модулях
2. Обновить методы публикации в `modules/distribution.py`

## Следующие шаги

1. Прочитайте [QUICK_START.md](QUICK_START.md) для быстрого старта
2. Изучите [README.md](README.md) для полной документации
3. Посмотрите [STRUCTURE.md](STRUCTURE.md) для понимания архитектуры
