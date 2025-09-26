#!/bin/bash
set -e

echo "🚀 AGI Layer v3.9 - Автоматическая установка"
echo "============================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Проверка root прав
if [[ $EUID -ne 0 ]]; then
   log_error "Этот скрипт должен запускаться с правами root"
   exit 1
fi

# Переходим в директорию проекта
cd /root/agi-layer-v3.9

log_step "1. Обновление системы и установка зависимостей"
apt-get update -y
apt-get upgrade -y
apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    python3-dev \
    python3-pip \
    python3-venv \
    docker.io \
    docker-compose \
    postgresql-client \
    redis-tools \
    htop \
    nginx \
    ufw \
    fail2ban

# Настройка Docker
log_step "2. Настройка Docker"
systemctl start docker
systemctl enable docker
usermod -aG docker root

# Настройка UFW (файрвол)
log_step "3. Настройка безопасности"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 8080/tcp  # API
ufw allow 8501/tcp  # Web UI
ufw --force enable

# Установка Ollama
log_step "4. Установка Ollama"
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
    log_info "Ollama установлен"
else
    log_info "Ollama уже установлен"
fi

# Создание виртуального окружения Python
log_step "5. Настройка Python окружения"
python3 -m venv /root/agi-venv
source /root/agi-venv/bin/activate

# Обновление pip
pip install --upgrade pip setuptools wheel

# Установка Python зависимостей
log_step "6. Установка Python зависимостей"
pip install -r requirements.txt

log_info "Установка основных зависимостей завершена"

# Установка дополнительных пакетов для CPU оптимизации
log_step "7. Установка CPU-оптимизированных библиотек"
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install intel-extension-for-pytorch

# Создание системных директорий
log_step "8. Создание системных директорий"
mkdir -p /var/log/agi-layer
mkdir -p /var/lib/agi-layer
mkdir -p /etc/agi-layer

# Копирование конфигурационных файлов
cp .env /etc/agi-layer/
chmod 600 /etc/agi-layer/.env

# Создание systemd сервисов
log_step "9. Создание systemd сервисов"

# Сервис для Docker Compose
cat > /etc/systemd/system/agi-layer.service << EOF
[Unit]
Description=AGI Layer v3.9
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/root/agi-layer-v3.9
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Сервис для Ollama
cat > /etc/systemd/system/ollama.service << EOF
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=root
Group=root
Restart=always
RestartSec=3
Environment="OLLAMA_HOST=0.0.0.0"

[Install]
WantedBy=default.target
EOF

# Перезагрузка systemd и включение сервисов
systemctl daemon-reload
systemctl enable agi-layer.service
systemctl enable ollama.service

log_step "10. Скачивание нейросетевых моделей"
source /root/agi-venv/bin/activate
python scripts/download_models.py

log_step "11. Первый запуск системы"
# Запускаем Ollama
systemctl start ollama
sleep 10

# Запускаем Docker контейнеры
docker-compose up -d

log_step "12. Проверка статуса сервисов"
sleep 30

# Проверяем статус
log_info "Статус Docker контейнеров:"
docker-compose ps

log_info "Статус systemd сервисов:"
systemctl status agi-layer --no-pager
systemctl status ollama --no-pager

log_step "13. Настройка автозапуска"
# Добавляем в crontab проверку и автоперезапуск
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/bin/docker-compose -f /root/agi-layer-v3.9/docker-compose.yml ps | grep -q 'Up' || /usr/bin/docker-compose -f /root/agi-layer-v3.9/docker-compose.yml up -d") | crontab -

echo ""
echo "🎉 AGI Layer v3.9 успешно установлен!"
echo "======================================"
echo ""
echo "📊 Доступные интерфейсы:"
echo "   • Web UI: http://$(hostname -I | awk '{print $1}'):8501"
echo "   • API: http://$(hostname -I | awk '{print $1}'):8080"
echo "   • Telegram Bot: настройте TELEGRAM_TOKEN в .env"
echo ""
echo "🔧 Управление:"
echo "   • Статус: docker-compose ps"
echo "   • Логи: docker-compose logs -f"
echo "   • Перезапуск: docker-compose restart"
echo "   • Остановка: docker-compose down"
echo ""
echo "📁 Конфигурация: /etc/agi-layer/.env"
echo "📝 Логи: /var/log/agi-layer/"
echo ""
log_info "Система готова к работе! 🤖"







