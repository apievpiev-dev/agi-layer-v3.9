# 🤖 Веб-чат с Ollama - Руководство пользователя

## Описание

Веб-интерфейс для общения с локальными языковыми моделями через Ollama. Позволяет выбирать различные модели и вести диалог в удобном веб-интерфейсе.

## Возможности

- 🎯 Выбор из доступных моделей Ollama
- 💬 Интерактивный чат с потоковым выводом
- 🧠 Сохранение контекста диалога
- 🗑️ Очистка истории чата
- 📊 Информация о выбранной модели
- ✅ Проверка статуса Ollama сервера

## Быстрый запуск

### 1. Запуск через Docker (рекомендуется)

```bash
# Запуск веб-чата с Ollama
./START_OLLAMA_CHAT.bat

# Или вручную:
docker-compose -f docker-compose-ollama-chat.yml up -d
```

### 2. Загрузка модели

```bash
# Загрузка популярных моделей
docker exec -it agi_ollama_chat ollama pull llama2
docker exec -it agi_ollama_chat ollama pull codellama
docker exec -it agi_ollama_chat ollama pull mistral
```

### 3. Открытие веб-интерфейса

Перейдите в браузере: http://localhost:8501

## Ручная установка (без Docker)

### 1. Установка Ollama

```bash
# Windows (PowerShell)
winget install Ollama.Ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# macOS
brew install ollama
```

### 2. Запуск Ollama

```bash
ollama serve
```

### 3. Загрузка модели

```bash
ollama pull llama2
```

### 4. Запуск веб-чата

```bash
# Установка зависимостей
pip install streamlit aiohttp

# Запуск
streamlit run start_ollama_chat.py
```

## Интеграция с основной системой

Веб-чат автоматически интегрирован в основную систему AGI Layer. Для доступа:

1. Запустите полную систему: `./START_FULL_SYSTEM.bat`
2. Откройте веб-интерфейс: http://localhost:8501
3. Перейдите на страницу "💬 Чат с Ollama"

## Доступные модели

### Рекомендуемые модели для CPU:

- **llama2:7b** - Универсальная модель (3.8GB)
- **codellama:7b** - Для программирования (3.8GB)
- **mistral:7b** - Быстрая и эффективная (4.1GB)
- **phi:2.7b** - Компактная модель (1.7GB)

### Команды для загрузки:

```bash
# Универсальные модели
ollama pull llama2:7b
ollama pull mistral:7b

# Для программирования
ollama pull codellama:7b
ollama pull deepseek-coder:6.7b

# Компактные модели
ollama pull phi:2.7b
ollama pull tinyllama:1.1b
```

## Использование

### Основные функции:

1. **Выбор модели** - Выберите модель из выпадающего списка
2. **Ввод сообщения** - Напишите вопрос в поле ввода
3. **Потоковый ответ** - Ответ генерируется по частям
4. **История чата** - Все сообщения сохраняются в сессии
5. **Очистка чата** - Кнопка для сброса истории

### Советы по использованию:

- Используйте конкретные вопросы для лучших результатов
- Очищайте историю при смене темы
- Для программирования используйте codellama
- Для общих вопросов подойдет llama2 или mistral

## Устранение неполадок

### Ollama не запускается

```bash
# Проверка статуса
docker ps | grep ollama

# Просмотр логов
docker logs agi_ollama_chat

# Перезапуск
docker-compose -f docker-compose-ollama-chat.yml restart ollama
```

### Нет доступных моделей

```bash
# Проверка установленных моделей
docker exec -it agi_ollama_chat ollama list

# Загрузка базовой модели
docker exec -it agi_ollama_chat ollama pull llama2:7b
```

### Медленная работа

- Используйте меньшие модели (phi:2.7b, tinyllama:1.1b)
- Убедитесь, что достаточно оперативной памяти (минимум 8GB)
- Для GPU используйте модели с GPU поддержкой

### Ошибки подключения

```bash
# Проверка портов
netstat -an | findstr 11434
netstat -an | findstr 8501

# Проверка сети Docker
docker network ls
docker network inspect agi_layer_agi_network
```

## Конфигурация

### Переменные окружения:

- `OLLAMA_URL` - URL Ollama сервера (по умолчанию: http://localhost:11434)
- `WEB_UI_PORT` - Порт веб-интерфейса (по умолчанию: 8501)

### Настройка моделей:

```bash
# Создание кастомной модели
docker exec -it agi_ollama_chat ollama create mymodel -f Modelfile

# Удаление модели
docker exec -it agi_ollama_chat ollama rm model_name
```

## Безопасность

- Веб-чат доступен только локально
- Данные не передаются в интернет
- Все модели работают локально
- История чата хранится только в браузере

## Производительность

### Системные требования:

- **Минимум**: 8GB RAM, 4 CPU cores
- **Рекомендуется**: 16GB RAM, 8 CPU cores
- **GPU**: NVIDIA GPU с 8GB+ VRAM (опционально)

### Оптимизация:

```bash
# Ограничение использования CPU
docker run --cpus="4.0" ollama/ollama

# Ограничение памяти
docker run --memory="8g" ollama/ollama
```

## Поддержка

При возникновении проблем:

1. Проверьте логи: `docker logs agi_ollama_chat`
2. Убедитесь, что Ollama запущен: http://localhost:11434/api/tags
3. Проверьте доступность моделей: `ollama list`
4. Перезапустите сервисы: `docker-compose restart`

---

**Примечание**: Веб-чат интегрирован в основную систему AGI Layer и доступен через основной веб-интерфейс на порту 8501.