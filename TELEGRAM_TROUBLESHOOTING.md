# 🔧 Диагностика проблем с Telegram ботом

## 🤖 Ваши настройки
- **Токен:** `8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw`
- **Chat ID:** `458589236`

## ❌ Возможные причины проблем

### 1. Бот не запущен
**Проблема:** Бот создан, но не запущен
**Решение:** 
- Перейдите к @BotFather в Telegram
- Отправьте `/mybots`
- Выберите вашего бота
- Нажмите "Start Bot"

### 2. Неверный токен
**Проблема:** Токен неправильный или устарел
**Решение:**
- Получите новый токен у @BotFather
- Команда `/newtoken`
- Обновите токен в конфигурации

### 3. Неверный Chat ID
**Проблема:** Chat ID не соответствует вашему чату
**Решение:**
- Напишите боту любое сообщение
- Перейдите на: `https://api.telegram.org/bot8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw/getUpdates`
- Найдите ваш `chat.id`

### 4. Бот не добавлен в чат
**Проблема:** Бот не добавлен в ваш чат
**Решение:**
- Найдите бота в Telegram
- Нажмите "Start" или "Запустить"
- Напишите `/start`

### 5. Система не запущена
**Проблема:** AGI Layer v3.9 не запущен
**Решение:**
```bash
# Запуск системы
./scripts/setup.sh

# Проверка статуса
docker-compose ps
```

## 🧪 Тесты для проверки

### Тест 1: Проверка бота
```bash
python simple_telegram_test.py
```

### Тест 2: Полная диагностика
```bash
python telegram_diagnostics.py
```

### Тест 3: Ручная проверка API
1. Откройте в браузере:
   `https://api.telegram.org/bot8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw/getMe`
2. Должен вернуться JSON с информацией о боте

### Тест 4: Проверка чата
1. Откройте в браузере:
   `https://api.telegram.org/bot8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw/getChat?chat_id=458589236`
2. Должен вернуться JSON с информацией о чате

## 🔍 Пошаговая диагностика

### Шаг 1: Проверка токена
```python
import requests

TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
url = f"https://api.telegram.org/bot{TOKEN}/getMe"
response = requests.get(url)
print(response.json())
```

### Шаг 2: Проверка Chat ID
```python
import requests

TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
CHAT_ID = "458589236"
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
data = {"chat_id": CHAT_ID, "text": "Тест"}
response = requests.post(url, json=data)
print(response.json())
```

### Шаг 3: Проверка обновлений
```python
import requests

TOKEN = "8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw"
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
response = requests.get(url)
print(response.json())
```

## 🚀 Быстрое решение

### Если бот не отвечает:

1. **Проверьте бота в Telegram:**
   - Найдите бота по username
   - Нажмите "Start"
   - Напишите `/start`

2. **Запустите систему:**
   ```bash
   # Создать .env файл
   echo "TELEGRAM_TOKEN=8325306099:AAG6hk3tG2-XmiJPgegzYFzQcY6WJaEbRxw" > .env
   echo "TELEGRAM_CHAT_ID=458589236" >> .env
   
   # Запустить систему
   ./scripts/setup.sh
   ```

3. **Проверьте логи:**
   ```bash
   docker-compose logs telegram_agent
   ```

## 📱 Команды для тестирования

После исправления проблем используйте:

- `/start` - запуск системы
- `/status` - статус агентов
- `/generate beautiful sunset` - генерация изображения
- `/report` - отчет системы

## 🆘 Если ничего не помогает

1. Создайте нового бота у @BotFather
2. Получите новый токен
3. Обновите настройки
4. Перезапустите систему

**Система AGI Layer v3.9 полностью готова, нужно только правильно настроить Telegram бота!**

