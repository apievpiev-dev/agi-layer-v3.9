# 🧠 Ollama Chat с Памятью - Продвинутый веб-интерфейс

Веб-интерфейс для общения с локальными языковыми моделями через Ollama с полной системой памяти и контекстным поиском.

## 🚀 Быстрый запуск

### Windows (PowerShell)
```powershell
.\START_OLLAMA_MEMORY.ps1
```

### Windows (Batch)
```batch
START_OLLAMA_MEMORY.bat
```

### Linux/macOS
```bash
# Запуск через Docker Compose
docker-compose -f docker-compose-ollama-memory.yml up -d

# Открыть в браузере
open http://localhost:8503
```

### Без Docker
```bash
# Убедитесь, что PostgreSQL и ChromaDB запущены
python3 start_ollama_chat_memory.py
```

## 📋 Требования

- Docker и Docker Compose
- PostgreSQL 15+
- ChromaDB
- Ollama
- Минимум 8GB RAM (рекомендуется 16GB)
- GPU (опционально, для ускорения)

## 🎯 Возможности

### 🧠 Система памяти
- **История чатов** - сохранение всех разговоров в PostgreSQL
- **Векторный поиск** - поиск по смыслу через ChromaDB
- **Контекстные ответы** - использование предыдущих разговоров
- **Управление сессиями** - создание, загрузка, переключение между чатами

### 💬 Интерактивный чат
- **Потоковый вывод** - ответы генерируются в реальном времени
- **WebSocket** - быстрая и стабильная связь
- **Выбор модели** - переключение между доступными моделями
- **Настройка параметров** - температура, длина ответа, top-p

### 🔍 Поиск и навигация
- **Поиск в памяти** - нахождение релевантной информации
- **Боковая панель** - список всех чатов
- **Быстрое переключение** - между сессиями одним кликом

## 🏗️ Архитектура

### Компоненты системы:
1. **PostgreSQL** - хранение структурированных данных (сессии, сообщения)
2. **ChromaDB** - векторная база данных для семантического поиска
3. **Ollama** - локальный LLM сервер
4. **FastAPI** - веб-сервер с WebSocket поддержкой
5. **Sentence Transformers** - генерация эмбеддингов

### Схема данных:
```
ChatSession (id, name, created_at, updated_at)
    ↓
ChatMessage (id, session_id, role, content, metadata, created_at)
    ↓
ChatEmbedding (id, message_id, embedding_id, created_at)
```

## 🔧 Установка и настройка

### 1. Запуск всех сервисов
```bash
docker-compose -f docker-compose-ollama-memory.yml up -d
```

### 2. Проверка статуса
```bash
docker-compose -f docker-compose-ollama-memory.yml ps
```

### 3. Загрузка модели
```bash
# Загрузка Llama2
docker exec -it agi_ollama_memory ollama pull llama2

# Загрузка других моделей
docker exec -it agi_ollama_memory ollama pull llama3
docker exec -it agi_ollama_memory ollama pull mistral
```

### 4. Открытие веб-интерфейса
Откройте браузер: http://localhost:8503

## 🎮 Использование

### Создание нового чата
1. Нажмите кнопку "+ Новый чат" в боковой панели
2. Введите название чата
3. Начните общение

### Поиск в памяти
1. Введите запрос в поле поиска внизу боковой панели
2. Нажмите Enter
3. Просмотрите релевантные результаты

### Переключение между чатами
1. Выберите чат из списка в боковой панели
2. История сообщений загрузится автоматически
3. Продолжите общение в контексте выбранного чата

### Настройка параметров генерации
- **Температура** - креативность ответов (0.0-2.0)
- **Максимум токенов** - длина ответа (100-4000)
- **Top-p** - разнообразие ответов (0.0-1.0)

## 🔍 API Endpoints

### Сессии
- `GET /api/sessions` - список всех сессий
- `POST /api/sessions` - создание новой сессии
- `GET /api/sessions/{id}/messages` - сообщения сессии

### Модели
- `GET /api/models` - список доступных моделей

### WebSocket
- `WS /ws` - потоковый чат с поддержкой:
  - `chat` - отправка сообщения
  - `load_session` - загрузка сессии
  - `search_memory` - поиск в памяти

## 🛠️ Устранение неполадок

### Проблема: "Не удалось подключиться к PostgreSQL"
```bash
# Проверка статуса PostgreSQL
docker exec agi_postgres_memory pg_isready -U agi_user -d agi_layer

# Перезапуск PostgreSQL
docker-compose -f docker-compose-ollama-memory.yml restart postgres
```

### Проблема: "ChromaDB недоступен"
```bash
# Проверка статуса ChromaDB
docker logs agi_chromadb_memory

# Перезапуск ChromaDB
docker-compose -f docker-compose-ollama-memory.yml restart chromadb
```

### Проблема: "Ollama не отвечает"
```bash
# Проверка статуса Ollama
docker exec agi_ollama_memory ollama list

# Перезапуск Ollama
docker-compose -f docker-compose-ollama-memory.yml restart ollama
```

### Проблема: Медленная генерация ответов
1. Уменьшите параметр "Максимум токенов"
2. Используйте более легкую модель
3. Проверьте доступность GPU
4. Увеличьте лимиты ресурсов Docker

## 📊 Мониторинг и логи

### Просмотр логов
```bash
# Логи всех сервисов
docker-compose -f docker-compose-ollama-memory.yml logs

# Логи конкретного сервиса
docker logs agi_ollama_chat_memory
docker logs agi_postgres_memory
docker logs agi_chromadb_memory
```

### Мониторинг ресурсов
```bash
# Использование ресурсов
docker stats

# Проверка подключений к базам данных
docker exec agi_postgres_memory psql -U agi_user -d agi_layer -c "SELECT COUNT(*) FROM chat_sessions;"
```

## 🔒 Безопасность

- Веб-интерфейс доступен только локально
- Все данные хранятся локально
- Нет отправки данных в интернет
- Шифрование соединений через HTTPS (при настройке)

## 📈 Производительность

### Системные требования:
- **Минимум:** 8GB RAM, 4 CPU cores
- **Рекомендуется:** 16GB RAM, 8 CPU cores, GPU
- **Для больших моделей:** 32GB+ RAM, GPU с 8GB+ VRAM

### Оптимизация:
1. **GPU ускорение** - использование CUDA для Ollama
2. **Ограничение контекста** - настройка количества сообщений в памяти
3. **Кэширование** - эмбеддинги кэшируются автоматически
4. **Индексы БД** - автоматическое создание индексов

## 🔄 Обновление

```bash
# Остановка сервисов
docker-compose -f docker-compose-ollama-memory.yml down

# Обновление образов
docker-compose -f docker-compose-ollama-memory.yml pull

# Запуск обновленных сервисов
docker-compose -f docker-compose-ollama-memory.yml up -d
```

## 🧪 Тестирование

### Запуск тестов
```bash
# Тест всей системы
python3 test_ollama_memory.py

# Тест отдельных компонентов
python3 -c "
import asyncio
from services.ollama_chat_with_memory import ChatMemory
# Тест памяти
"
```

### Проверка функциональности
1. **Создание сессии** - создание нового чата
2. **Добавление сообщений** - отправка и получение ответов
3. **Поиск в памяти** - семантический поиск по истории
4. **Загрузка контекста** - использование предыдущих разговоров

## 📁 Структура файлов

```
services/
├── ollama_chat_with_memory.py    # Основной веб-интерфейс с памятью
├── ollama_web_chat.py           # Простая версия без памяти
└── ollama_chat.py               # Streamlit версия

docker-compose-ollama-memory.yml  # Docker конфигурация с памятью
docker-compose-ollama.yml         # Простая версия

start_ollama_chat_memory.py       # Скрипт запуска с памятью
start_ollama_chat.py              # Простой скрипт запуска

START_OLLAMA_MEMORY.bat/ps1       # Windows скрипты
START_OLLAMA_CHAT.bat/ps1         # Простые Windows скрипты

test_ollama_memory.py             # Тесты с памятью
test_ollama_chat.py               # Простые тесты
```

## 🆘 Поддержка

### Частые проблемы:
1. **Не запускается PostgreSQL** - проверьте порт 5432
2. **ChromaDB не отвечает** - проверьте порт 8000
3. **Ollama медленно работает** - загрузите более легкую модель
4. **Нет памяти** - увеличьте лимиты Docker

### Получение помощи:
1. Проверьте логи: `docker logs <container_name>`
2. Запустите тесты: `python3 test_ollama_memory.py`
3. Проверьте статус сервисов: `docker-compose ps`

---

**🎉 Готово! Теперь у вас есть полноценный чат с ИИ, который помнит все разговоры и может использовать эту информацию для более точных ответов!**