# 🚀 БЫСТРЫЙ ЗАПУСК AGI Layer v3.9

## ❌ Проблема найдена:
Docker не установлен на системе. Бот работает, но система AGI Layer v3.9 не запущена.

## ✅ Решение:

### 1. Установите Docker Desktop
1. Скачайте Docker Desktop: https://www.docker.com/products/docker-desktop
2. Установите и запустите Docker Desktop
3. Дождитесь полной загрузки (зеленый статус)

### 2. Создайте .env файл
Создайте файл `.env` в папке проекта со следующим содержимым:

```env
# AGI Layer v3.9 - Configuration
PROJECT_NAME=AGI Layer v3.9
VERSION=3.9.0
DEBUG=false

# Database PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=agi_layer
POSTGRES_USER=agi_user
POSTGRES_PASSWORD=agi_password

# ChromaDB
CHROMA_HOST=chromadb
CHROMA_PORT=8000
CHROMA_COLLECTION=agi_memory

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# Telegram Bot
TELEGRAM_TOKEN=8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw
TELEGRAM_CHAT_ID=458589236

# Web UI
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=8501

# Models
MODELS_PATH=/app/models
DOWNLOAD_MODELS_ON_START=true

# Logging
LOG_LEVEL=INFO
LOG_PATH=/app/logs

# Security
SECRET_KEY=agi-layer-v39-secure-key-2024
ALLOWED_HOSTS=*

# Agents
AGENT_LOOP_INTERVAL=1.0
AGENT_TIMEOUT=300
MAX_CONCURRENT_TASKS=10

# Recovery settings
RECOVERY_INTERVAL=300
MAX_RECOVERY_AGE=3600

# Monitoring settings
HEALTH_CHECK_INTERVAL=30
RESTART_FAILED_AGENTS=true
```

### 3. Запустите систему
Откройте командную строку в папке проекта и выполните:

```cmd
# Создание директорий
mkdir logs models output output\images data data\chroma backups

# Запуск системы
docker-compose up -d
```

### 4. Проверьте работу
```cmd
# Статус контейнеров
docker-compose ps

# Логи системы
docker-compose logs -f
```

### 5. Тестируйте бота
Напишите боту в Telegram:
- `/start` - приветствие
- `/status` - статус системы
- `/generate beautiful sunset` - генерация изображения

## 🎯 Что произойдет после запуска:

1. **12 контейнеров** запустятся автоматически
2. **Telegram бот** начнет отвечать на команды
3. **Web UI** будет доступен по адресу http://localhost:8501
4. **API** будет доступен по адресу http://localhost:8001

## 📱 Доступные команды бота:

- `/start` - запуск системы
- `/status` - статус всех агентов
- `/generate [описание]` - генерация изображения
- `/report` - отчет о работе системы
- `/reboot` - перезапуск системы

## 🔧 Если что-то не работает:

```cmd
# Остановка системы
docker-compose down

# Перезапуск
docker-compose up -d

# Просмотр логов
docker-compose logs telegram_agent
```

## 🎉 Результат:
После выполнения всех шагов ваш бот @atlas_wb_bot будет полностью функционален и будет отвечать на все команды!

---

**Система AGI Layer v3.9 готова к работе! Нужно только установить Docker и запустить.** 🚀

