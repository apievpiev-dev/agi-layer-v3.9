# 🤖 Ollama Chat - Веб-интерфейс для чата с ИИ

Веб-интерфейс для общения с локальными языковыми моделями через Ollama.

## 🚀 Быстрый запуск

### Windows (PowerShell)
```powershell
.\START_OLLAMA_CHAT.ps1
```

### Windows (Batch)
```batch
START_OLLAMA_CHAT.bat
```

### Linux/macOS
```bash
# Запуск через Docker Compose
docker-compose -f docker-compose-ollama.yml up -d

# Открыть в браузере
open http://localhost:8502
```

## 📋 Требования

- Docker и Docker Compose
- Минимум 8GB RAM (рекомендуется 16GB)
- GPU (опционально, для ускорения)

## 🔧 Установка и настройка

### 1. Запуск сервисов
```bash
docker-compose -f docker-compose-ollama.yml up -d
```

### 2. Загрузка модели
```bash
# Загрузка Llama2 (рекомендуется)
docker exec -it agi_ollama ollama pull llama2

# Загрузка других моделей
docker exec -it agi_ollama ollama pull llama3
docker exec -it agi_ollama ollama pull mistral
docker exec -it agi_ollama ollama pull codellama
```

### 3. Открытие веб-интерфейса
Откройте браузер и перейдите по адресу: http://localhost:8502

## 🎛️ Возможности

- **💬 Интерактивный чат** - общение с ИИ в реальном времени
- **🔄 Потоковый вывод** - ответы генерируются по частям
- **🎯 Выбор модели** - переключение между доступными моделями
- **⚙️ Настройка параметров** - температура, длина ответа, top-p
- **📱 Адаптивный дизайн** - работает на всех устройствах
- **🌐 WebSocket** - быстрая и стабильная связь

## 📊 Доступные модели

### Рекомендуемые модели:
- **llama2** - универсальная модель для общих задач
- **llama3** - улучшенная версия с лучшим пониманием
- **mistral** - быстрая и эффективная модель
- **codellama** - специализированная для программирования

### Загрузка моделей:
```bash
# Список доступных моделей
docker exec -it agi_ollama ollama list

# Загрузка конкретной модели
docker exec -it agi_ollama ollama pull <имя_модели>

# Удаление модели
docker exec -it agi_ollama ollama rm <имя_модели>
```

## 🛠️ Настройка параметров

### Температура (0.0 - 2.0)
- **0.0** - детерминированные ответы
- **0.7** - сбалансированная креативность (по умолчанию)
- **1.5+** - очень креативные ответы

### Максимум токенов (100 - 4000)
- **100-500** - короткие ответы
- **1000** - средние ответы (по умолчанию)
- **2000+** - длинные развернутые ответы

### Top-p (0.0 - 1.0)
- **0.9** - стандартное значение (по умолчанию)
- **0.5** - более фокусированные ответы
- **0.95** - более разнообразные ответы

## 🔧 Устранение неполадок

### Проблема: "Не удалось подключиться к Ollama"
**Решение:**
```bash
# Проверка статуса Ollama
docker-compose -f docker-compose-ollama.yml ps

# Перезапуск Ollama
docker-compose -f docker-compose-ollama.yml restart ollama

# Проверка логов
docker logs agi_ollama
```

### Проблема: "Нет доступных моделей"
**Решение:**
```bash
# Загрузка базовой модели
docker exec -it agi_ollama ollama pull llama2

# Проверка загруженных моделей
docker exec -it agi_ollama ollama list
```

### Проблема: Медленная генерация ответов
**Решения:**
1. Уменьшите параметр "Максимум токенов"
2. Используйте более легкую модель (mistral вместо llama3)
3. Убедитесь, что Docker имеет доступ к GPU (если доступно)

## 📁 Структура файлов

```
services/
├── ollama_web_chat.py      # Основной веб-интерфейс
├── ollama_chat.py          # Streamlit версия (альтернатива)
└── ...

docker-compose-ollama.yml   # Конфигурация Docker для Ollama
start_ollama_chat.py        # Python скрипт запуска
START_OLLAMA_CHAT.bat       # Windows batch скрипт
START_OLLAMA_CHAT.ps1       # Windows PowerShell скрипт
```

## 🌐 API Endpoints

### GET /api/models
Получение списка доступных моделей
```json
{
  "models": ["llama2", "mistral", "codellama"]
}
```

### POST /api/chat
Отправка сообщения и получение ответа
```json
{
  "message": "Привет, как дела?",
  "model": "llama2"
}
```

### WebSocket /ws
Потоковый чат в реальном времени

## 🔒 Безопасность

- Веб-интерфейс доступен только локально (localhost)
- Нет сохранения истории чатов
- Все данные обрабатываются локально
- Нет отправки данных в интернет

## 📈 Производительность

### Системные требования:
- **Минимум:** 8GB RAM, 4 CPU cores
- **Рекомендуется:** 16GB RAM, 8 CPU cores, GPU
- **Для больших моделей:** 32GB+ RAM, GPU с 8GB+ VRAM

### Оптимизация:
1. Используйте GPU для ускорения
2. Ограничьте длину контекста
3. Выберите подходящую модель для задачи

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker logs agi_ollama`
2. Перезапустите сервисы: `docker-compose -f docker-compose-ollama.yml restart`
3. Проверьте доступность портов: `netstat -an | grep 8502`

## 🔄 Обновление

```bash
# Остановка сервисов
docker-compose -f docker-compose-ollama.yml down

# Обновление образов
docker-compose -f docker-compose-ollama.yml pull

# Запуск обновленных сервисов
docker-compose -f docker-compose-ollama.yml up -d
```

---

**🎉 Готово! Теперь вы можете общаться с ИИ через удобный веб-интерфейс!**