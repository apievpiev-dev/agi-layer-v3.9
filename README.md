# 🤖 AGI Layer v3.9 - Multi-Agent AI System

Полнофункциональная мультиагентная система с искусственным интеллектом, работающая на CPU без GPU.

## 🎯 Возможности

### 🧠 Интеллектуальные агенты
- **MetaAgent** - координатор и диспетчер задач
- **TelegramAgent** - Telegram бот с естественным общением
- **ImageGenAgent** - генерация изображений (Stable Diffusion 1.5)
- **VisionAgent** - анализ изображений и OCR (BLIP2 + EasyOCR)
- **MemoryAgent** - векторная память и знания (ChromaDB)
- **ReportAgent** - создание отчетов и аналитика
- **WatchdogAgent** - мониторинг системы
- **RecoveryAgent** - восстановление после сбоев

### 🎨 ИИ модели (CPU-оптимизированные)
- **Stable Diffusion 1.5** - генерация изображений
- **Phi-2** - языковая модель для текста
- **BLIP2** - понимание изображений
- **EasyOCR** - распознавание текста
- **SentenceTransformers** - векторные эмбеддинги

### 🌐 Интерфейсы
- **Telegram Bot** - основной интерфейс пользователя
- **Web Dashboard** - мониторинг и управление (Streamlit)
- **REST API** - программный доступ

### 🗄️ Хранение данных
- **PostgreSQL** - реляционная БД для задач и логов
- **ChromaDB** - векторная БД для памяти и знаний
- **Файловое хранилище** - изображения и отчеты

## 🚀 Быстрый запуск

### Автоматическая установка (рекомендуется)

```bash
# Скачиваем и запускаем скрипт установки
curl -fsSL https://raw.githubusercontent.com/your-repo/agi-layer/main/install.sh | bash

# Или клонируем репозиторий
git clone https://github.com/your-repo/agi-layer.git
cd agi-layer
chmod +x install.sh
./install.sh
```

### Ручная установка

#### 1. Требования
- Docker и Docker Compose
- Python 3.11+
- Минимум 4GB RAM
- 10GB свободного места

#### 2. Клонирование и настройка
```bash
git clone https://github.com/your-repo/agi-layer.git
cd agi-layer

# Создание .env файла
cp .env.example .env
# Отредактируйте .env файл с вашими настройками
```

#### 3. Telegram бот
1. Создайте бота у [@BotFather](https://t.me/BotFather)
2. Получите токен бота
3. Узнайте ваш Chat ID у [@userinfobot](https://t.me/userinfobot)
4. Добавьте данные в `.env`:
```env
TELEGRAM_TOKEN=ваш_токен_бота
TELEGRAM_CHAT_IDS=ваш_chat_id
```

#### 4. Запуск системы
```bash
# Сборка и запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Проверка статуса
docker-compose ps
```

#### 5. Загрузка моделей ИИ
```bash
# Автоматическая загрузка всех моделей
python scripts/download_models.py

# Загрузка конкретных моделей
python scripts/download_models.py --specific phi-2 stable-diffusion-v1-5

# Просмотр доступных моделей
python scripts/download_models.py --list
```

## 📱 Использование

### Telegram команды

#### Основные команды
- `/start` - запуск и приветствие
- `/help` - справка по командам
- `/status` - статус всех агентов

#### Генерация изображений
```
/generate красивый закат над океаном
/generate портрет девушки в стиле ренессанс
```

#### Работа с памятью
```
/memory запомни что сегодня хорошая погода
/memory найди информацию о Python
```

#### Отчеты
```
/report создай системный отчет
/report статистика за неделю
```

### Естественное общение
Просто пишите боту как обычному собеседнику:
- "Нарисуй кота в космосе" → генерация изображения
- "Что на этом фото?" + фото → анализ изображения
- "Запомни мой любимый цвет - синий" → сохранение в память

### Web Dashboard
Откройте http://localhost:8501 для доступа к веб-интерфейсу:
- 📊 Мониторинг агентов
- 📈 Статистика задач
- 📝 Системные логи
- ⚡ Быстрые действия

## 🏗️ Архитектура

### Компоненты системы
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │  Web Dashboard  │    │   REST API      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴───────────┐
                    │      MetaAgent          │
                    │    (Координатор)        │
                    └─────────────┬───────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                       │                        │
┌───────▼────────┐    ┌─────────▼────────┐    ┌─────────▼────────┐
│  ImageGenAgent │    │   VisionAgent    │    │  MemoryAgent     │
│ (SD 1.5)       │    │ (BLIP2 + OCR)    │    │ (ChromaDB)       │
└────────────────┘    └──────────────────┘    └──────────────────┘
        │                       │                        │
┌───────▼────────┐    ┌─────────▼────────┐    ┌─────────▼────────┐
│  ReportAgent   │    │  WatchdogAgent   │    │ RecoveryAgent    │
│ (Analytics)    │    │ (Monitoring)     │    │ (Recovery)       │
└────────────────┘    └──────────────────┘    └──────────────────┘
        │                       │                        │
        └───────────────────────┼────────────────────────┘
                                │
                    ┌─────────────┴───────────┐
                    │     PostgreSQL          │
                    │   (Tasks & Logs)        │
                    └─────────────────────────┘
```

### Сетевая архитектура
- **Порт 8001** - MetaAgent API
- **Порт 8002** - TelegramAgent API
- **Порт 8003** - ImageGenAgent API
- **Порт 8004** - VisionAgent API
- **Порт 8005** - MemoryAgent API
- **Порт 8006** - ReportAgent API
- **Порт 8007** - WatchdogAgent API
- **Порт 8008** - RecoveryAgent API
- **Порт 8501** - Web Dashboard
- **Порт 5432** - PostgreSQL
- **Порт 8000** - ChromaDB

## 🔧 Управление системой

### Docker команды
```bash
# Запуск всех сервисов
docker-compose up -d

# Остановка
docker-compose down

# Перезапуск конкретного сервиса
docker-compose restart telegram_agent

# Просмотр логов
docker-compose logs -f meta_agent

# Просмотр статуса
docker-compose ps

# Обновление образов
docker-compose pull && docker-compose up -d
```

### Мониторинг
```bash
# Системные ресурсы
docker stats

# Логи конкретного агента
docker-compose logs -f image_gen_agent

# Статус здоровья
curl http://localhost:8001/status
```

### Резервное копирование
```bash
# Бэкап базы данных
docker-compose exec postgres pg_dump -U agi_user agi_layer > backup.sql

# Бэкап векторной БД
docker-compose exec chromadb tar -czf - /chroma > chromadb_backup.tar.gz

# Бэкап моделей
tar -czf models_backup.tar.gz models/
```

## 🛠️ Разработка

### Создание нового агента
1. Наследуйтесь от `BaseAgent`:
```python
from agents.base_agent import BaseAgent, Task

class MyAgent(BaseAgent):
    def __init__(self, config):
        super().__init__("my_agent", config)
    
    async def _initialize_agent(self):
        # Инициализация агента
        pass
    
    async def process_task(self, task: Task):
        # Обработка задач
        return {"status": "success"}
```

2. Добавьте в `docker-compose.yml`
3. Зарегистрируйте в `MetaAgent`

### Настройка моделей
Модели конфигурируются в `scripts/download_models.py`:
```python
self.models_config = {
    "text_models": {
        "my-model": {
            "name": "huggingface/model-name",
            "type": "causal_lm",
            "size": "1GB"
        }
    }
}
```

### API документация
- MetaAgent API: http://localhost:8001/docs
- Swagger UI доступен для всех агентов

## 📊 Мониторинг и логи

### Структура логов
```
logs/
├── meta_agent.log      # Координатор
├── telegram_agent.log  # Telegram бот
├── image_gen_agent.log # Генерация изображений
├── vision_agent.log    # Анализ изображений
└── system.log          # Общие системные логи
```

### Метрики
- Статус агентов
- Количество обработанных задач
- Время выполнения
- Использование ресурсов
- Ошибки и исключения

## 🔒 Безопасность

### Настройки безопасности
- Авторизация по Telegram Chat ID
- API ключи для внутренней связи
- Изоляция сервисов в Docker
- Ограничение доступа через UFW

### Рекомендации
1. Измените пароли в `.env`
2. Ограничьте доступ к портам
3. Регулярно обновляйте образы
4. Мониторьте логи на предмет подозрительной активности

## 🚨 Устранение неполадок

### Частые проблемы

#### Агент не запускается
```bash
# Проверьте логи
docker-compose logs agent_name

# Проверьте ресурсы
docker stats

# Перезапустите агента
docker-compose restart agent_name
```

#### Модели не загружаются
```bash
# Проверьте место на диске
df -h

# Запустите загрузку вручную
python scripts/download_models.py --specific model-name

# Проверьте интернет соединение
curl -I https://huggingface.co
```

#### Telegram бот не отвечает
1. Проверьте токен в `.env`
2. Убедитесь что Chat ID корректный
3. Проверьте логи `telegram_agent`

#### Медленная генерация изображений
1. Увеличьте swap файл
2. Уменьшите количество шагов в настройках
3. Используйте меньшее разрешение

### Диагностические команды
```bash
# Проверка всех сервисов
docker-compose ps

# Проверка сети
docker network ls

# Проверка томов
docker volume ls

# Тест API
curl http://localhost:8001/status
```

## 📈 Производительность

### Системные требования
- **Минимум**: 4GB RAM, 2 CPU ядра, 10GB диск
- **Рекомендуется**: 8GB RAM, 4 CPU ядра, 20GB диск
- **Оптимально**: 16GB RAM, 8 CPU ядер, 50GB SSD

### Оптимизация
- Используйте SSD для моделей
- Настройте swap для больших моделей
- Мониторьте использование памяти
- Регулярно очищайте логи

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для фичи
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🆘 Поддержка

- 📧 Email: support@agi-layer.com
- 💬 Telegram: [@agi_layer_support](https://t.me/agi_layer_support)
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/agi-layer/issues)
- 📖 Wiki: [GitHub Wiki](https://github.com/your-repo/agi-layer/wiki)

---

**AGI Layer v3.9** - Первая полнофункциональная мультиагентная система с ИИ для всех! 🚀