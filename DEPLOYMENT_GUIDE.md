# 🚀 AGI Layer v3.9 - Руководство по развертыванию

## 📋 Быстрый старт

### 1. Подготовка системы

**Требования:**
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM минимум (рекомендуется 16GB)
- 20GB свободного места на диске
- CPU с поддержкой AVX2 (для моделей)

**Проверка системы:**
```bash
# Проверка Docker
docker --version
docker-compose --version

# Проверка ресурсов
free -h
df -h
```

### 2. Настройка проекта

```bash
# Клонирование проекта
git clone <repository-url>
cd agi-layer-v3.9

# Создание конфигурации
cp env.example .env

# Редактирование настроек
nano .env
```

**Обязательные настройки в .env:**
```env
# Telegram Bot (получить у @BotFather)
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Безопасность
SECRET_KEY=your_very_secure_secret_key_here

# При необходимости изменить пароли БД
POSTGRES_PASSWORD=your_secure_password
```

### 3. Развертывание

```bash
# Установка прав доступа
chmod +x scripts/*.sh
chmod +x docker-entrypoint.sh

# Создание директорий
mkdir -p logs models output/images data/chroma backups

# Развертывание (без моделей)
./scripts/setup.sh

# ИЛИ развертывание с автоматической загрузкой моделей
./scripts/setup.sh --with-models
```

### 4. Проверка развертывания

```bash
# Статус контейнеров
docker-compose ps

# Логи системы
docker-compose logs -f

# Проверка Web UI
curl http://localhost:8501

# Проверка MetaAgent API
curl http://localhost:8001/health
```

## 🔧 Детальная настройка

### Настройка Telegram Bot

1. **Создание бота:**
   - Написать @BotFather в Telegram
   - Команда `/newbot`
   - Выбрать имя и username
   - Получить токен

2. **Получение Chat ID:**
   - Написать боту любое сообщение
   - Перейти на `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Найти `chat.id` в ответе

3. **Настройка .env:**
   ```env
   TELEGRAM_TOKEN=1234567890:ABCDEFghijklmnopqrstuvwxyz
   TELEGRAM_CHAT_ID=123456789
   ```

### Настройка моделей

**Автоматическая загрузка:**
```bash
# Загрузка всех моделей
docker-compose exec meta_agent python scripts/download_models.py --all

# Проверка моделей
docker-compose exec meta_agent python scripts/download_models.py --check
```

**Ручная загрузка:**
```bash
# Загрузка конкретной модели
docker-compose exec meta_agent python scripts/download_models.py --model stable_diffusion_1_5

# Информация об использовании диска
docker-compose exec meta_agent python scripts/download_models.py --usage
```

### Настройка безопасности

1. **Изменение паролей:**
   ```env
   POSTGRES_PASSWORD=very_secure_password_123
   SECRET_KEY=your_very_long_and_secure_secret_key_here
   ```

2. **Настройка UFW (Ubuntu/Debian):**
   ```bash
   sudo ufw allow ssh
   sudo ufw allow 8501  # Web UI
   sudo ufw enable
   ```

3. **Ограничение доступа:**
   ```env
   # Только ваш IP для Web UI
   ALLOWED_HOSTS=192.168.1.100,127.0.0.1
   ```

## 📊 Мониторинг и управление

### Web UI
- **URL:** http://localhost:8501
- **Функции:** Дашборд, управление агентами, просмотр логов, настройки

### Telegram команды
- `/start` - Информация о системе
- `/status` - Статус всех агентов
- `/generate [prompt]` - Генерация изображения
- `/report` - Отчет о работе системы
- `/reboot` - Перезапуск системы

### API endpoints

**MetaAgent (http://localhost:8001):**
```bash
# Статус системы
curl http://localhost:8001/status

# Создание задачи
curl -X POST http://localhost:8001/create_task \
  -H "Content-Type: application/json" \
  -d '{"task_type": "image_generation", "data": {"prompt": "beautiful landscape"}}'

# Перезапуск агента
curl -X POST http://localhost:8001/restart_agent \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "image_agent"}'
```

### Логи и диагностика

```bash
# Логи всех сервисов
docker-compose logs -f

# Логи конкретного агента
docker-compose logs -f image_agent

# Логи базы данных
docker-compose logs -f postgres

# Проверка использования ресурсов
docker stats

# Проверка дискового пространства
docker system df
```

## 🔄 Обслуживание

### Обновление системы

```bash
# Остановка системы
docker-compose down

# Обновление кода
git pull

# Пересборка образов
docker-compose build

# Запуск с новыми образами
docker-compose up -d
```

### Резервное копирование

```bash
# Создание бэкапа базы данных
docker-compose exec postgres pg_dump -U agi_user agi_layer > backup_$(date +%Y%m%d).sql

# Создание бэкапа моделей
tar -czf models_backup_$(date +%Y%m%d).tar.gz models/

# Создание бэкапа логов
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

### Восстановление

```bash
# Восстановление базы данных
docker-compose exec -T postgres psql -U agi_user agi_layer < backup_20231201.sql

# Восстановление моделей
tar -xzf models_backup_20231201.tar.gz
```

### Очистка системы

```bash
# Очистка неиспользуемых Docker ресурсов
docker system prune -a

# Очистка старых логов
docker-compose exec meta_agent python -c "
from agents.recovery_agent import RecoveryAgent
import asyncio
async def cleanup():
    agent = RecoveryAgent({})
    await agent._cleanup_old_data()
asyncio.run(cleanup())
"
```

## 🐛 Решение проблем

### Частые проблемы

**1. Контейнеры не запускаются:**
```bash
# Проверка логов
docker-compose logs

# Проверка портов
netstat -tulpn | grep :5432

# Перезапуск
docker-compose restart
```

**2. Модели не загружаются:**
```bash
# Проверка места на диске
df -h

# Очистка и повторная загрузка
docker-compose exec meta_agent python scripts/download_models.py --all --force
```

**3. Telegram бот не отвечает:**
```bash
# Проверка токена и Chat ID в .env
cat .env | grep TELEGRAM

# Проверка логов Telegram агента
docker-compose logs telegram_agent

# Перезапуск Telegram агента
docker-compose restart telegram_agent
```

**4. Высокое использование ресурсов:**
```bash
# Мониторинг ресурсов
docker stats

# Ограничение ресурсов в docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

### Диагностика

**Проверка здоровья системы:**
```bash
# Статус всех агентов
curl http://localhost:8001/status | jq

# Проверка базы данных
docker-compose exec postgres psql -U agi_user -d agi_layer -c "SELECT COUNT(*) FROM agents;"

# Проверка ChromaDB
curl http://localhost:8000/api/v1/heartbeat
```

**Логи ошибок:**
```bash
# Поиск ошибок в логах
docker-compose logs | grep -i error

# Анализ логов агентов
docker-compose exec meta_agent python -c "
import asyncio
from agents.recovery_agent import RecoveryAgent
async def check_errors():
    agent = RecoveryAgent({})
    errors = await agent._find_error_logs()
    print(f'Найдено ошибок: {len(errors)}')
asyncio.run(check_errors())
"
```

## 📈 Масштабирование

### Горизонтальное масштабирование

**Добавление дополнительных агентов:**
```yaml
# В docker-compose.yml
image_agent_2:
  build: .
  container_name: agi_image_agent_2
  environment:
    - AGENT_NAME=image_agent_2
  # ... остальная конфигурация
```

**Балансировка нагрузки:**
```bash
# Использование nginx для балансировки
docker run -d --name nginx -p 80:80 \
  -v $(pwd)/nginx.conf:/etc/nginx/nginx.conf \
  nginx
```

### Вертикальное масштабирование

**Увеличение ресурсов:**
```yaml
# В docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
    reservations:
      memory: 2G
      cpus: '1.0'
```

## 🔐 Безопасность в production

### Рекомендации по безопасности

1. **Изменение паролей по умолчанию**
2. **Использование HTTPS для Web UI**
3. **Настройка firewall**
4. **Регулярные обновления**
5. **Мониторинг логов безопасности**

### SSL/TLS настройка

```bash
# Генерация сертификатов
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Настройка nginx с SSL
# Добавить в docker-compose.yml
```

## 📞 Поддержка

### Логи и отчеты

**Сбор диагностической информации:**
```bash
# Создание отчета о системе
./scripts/create_system_report.sh

# Отправка отчета через Telegram
curl -X POST http://localhost:8002/send_report
```

### Мониторинг производительности

**Метрики для отслеживания:**
- Использование CPU/RAM
- Время отклика агентов
- Количество ошибок
- Размер логов
- Использование диска

**Настройка алертов:**
```bash
# Простой скрипт мониторинга
#!/bin/bash
if [ $(docker stats --no-stream --format "table {{.CPUPerc}}" image_agent | tail -n +2 | cut -d'%' -f1 | cut -d'.' -f1) -gt 90 ]; then
    curl -X POST http://localhost:8002/send_notification -d "CPU usage high!"
fi
```

---

**✅ Система готова к production использованию!**

Для получения дополнительной помощи обращайтесь к документации или создавайте issues в репозитории.

