#!/bin/bash

# AGI Layer v3.9 - Автоматическая установка
# Поддерживает Ubuntu/Debian, CentOS/RHEL, macOS

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  AGI Layer v3.9 - Автоматическая установка"
    echo "  Мультиагентная система с ИИ"
    echo "=============================================="
    echo -e "${NC}"
}

# Определение операционной системы
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
            print_info "Обнаружена Debian/Ubuntu система"
        elif [ -f /etc/redhat-release ]; then
            OS="rhel"
            print_info "Обнаружена RHEL/CentOS система"
        else
            OS="linux"
            print_info "Обнаружена Linux система"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_info "Обнаружена macOS система"
    else
        print_error "Неподдерживаемая операционная система: $OSTYPE"
        exit 1
    fi
}

# Проверка прав root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Скрипт запущен от root. Рекомендуется запуск от обычного пользователя."
        read -p "Продолжить? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Обновление системы
update_system() {
    print_info "Обновление системы..."
    
    case $OS in
        "debian")
            sudo apt update && sudo apt upgrade -y
            ;;
        "rhel")
            sudo yum update -y || sudo dnf update -y
            ;;
        "macos")
            print_info "Обновите macOS через System Preferences"
            ;;
    esac
    
    print_success "Система обновлена"
}

# Установка базовых зависимостей
install_dependencies() {
    print_info "Установка базовых зависимостей..."
    
    case $OS in
        "debian")
            sudo apt install -y \
                curl \
                wget \
                git \
                build-essential \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev \
                libpq-dev \
                libgl1-mesa-glx \
                libglib2.0-0 \
                fonts-dejavu-core \
                ca-certificates \
                gnupg \
                lsb-release
            ;;
        "rhel")
            sudo yum install -y \
                curl \
                wget \
                git \
                gcc \
                gcc-c++ \
                python3 \
                python3-pip \
                python3-devel \
                postgresql-devel \
                mesa-libGL \
                glib2 \
                dejavu-fonts-common
            ;;
        "macos")
            # Проверяем Homebrew
            if ! command -v brew &> /dev/null; then
                print_info "Установка Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            
            brew install python3 git curl wget postgresql
            ;;
    esac
    
    print_success "Базовые зависимости установлены"
}

# Проверка и создание swap
setup_swap() {
    print_info "Настройка swap для работы с моделями ИИ..."
    
    # Проверяем текущий swap
    CURRENT_SWAP=$(free -h | grep Swap | awk '{print $2}')
    
    if [[ "$CURRENT_SWAP" == "0B" ]]; then
        print_info "Создание swap файла 4GB..."
        
        # Создаем swap файл
        sudo fallocate -l 4G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1024 count=4194304
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        
        # Добавляем в fstab для автоматического монтирования
        if ! grep -q "/swapfile" /etc/fstab; then
            echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
        fi
        
        print_success "Swap 4GB создан и активирован"
    else
        print_info "Swap уже настроен: $CURRENT_SWAP"
    fi
}

# Установка Docker
install_docker() {
    print_info "Установка Docker..."
    
    if command -v docker &> /dev/null; then
        print_info "Docker уже установлен"
        docker --version
        return
    fi
    
    case $OS in
        "debian")
            # Удаляем старые версии
            sudo apt remove -y docker docker-engine docker.io containerd runc || true
            
            # Добавляем репозиторий Docker
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Устанавливаем Docker
            sudo apt update
            sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        "rhel")
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        "macos")
            print_info "Для macOS скачайте Docker Desktop с https://www.docker.com/products/docker-desktop"
            print_warning "Установите Docker Desktop и запустите его перед продолжением"
            read -p "Docker Desktop установлен и запущен? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
            ;;
    esac
    
    # Добавляем пользователя в группу docker
    if [[ "$OS" != "macos" ]]; then
        sudo usermod -aG docker $USER
        sudo systemctl enable docker
        sudo systemctl start docker
    fi
    
    print_success "Docker установлен"
}

# Установка Docker Compose
install_docker_compose() {
    print_info "Установка Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        print_info "Docker Compose уже установлен"
        docker-compose --version
        return
    fi
    
    # Для новых версий Docker, compose встроен как плагин
    if docker compose version &> /dev/null; then
        print_info "Docker Compose (plugin) уже установлен"
        return
    fi
    
    # Устанавливаем standalone версию
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    print_success "Docker Compose установлен"
}

# Клонирование репозитория (если нужно)
setup_project() {
    print_info "Настройка проекта AGI Layer v3.9..."
    
    # Если мы уже в директории проекта, пропускаем клонирование
    if [[ -f "docker-compose.yml" && -d "agents" ]]; then
        print_info "Проект уже настроен в текущей директории"
        return
    fi
    
    # Создаем директорию проекта
    PROJECT_DIR="$HOME/agi-layer"
    
    if [[ ! -d "$PROJECT_DIR" ]]; then
        print_info "Создание директории проекта: $PROJECT_DIR"
        mkdir -p "$PROJECT_DIR"
    fi
    
    cd "$PROJECT_DIR"
    
    # Создаем необходимые директории
    mkdir -p {agents,models,data,logs,memory,config,services,scripts,templates}
    
    print_success "Структура проекта создана"
}

# Создание .env файла
create_env_file() {
    print_info "Создание файла конфигурации .env..."
    
    if [[ -f ".env" ]]; then
        print_warning ".env файл уже существует"
        read -p "Перезаписать? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    # Запрашиваем Telegram токен
    echo
    print_info "Настройка Telegram бота..."
    read -p "Введите Telegram Bot Token (получить у @BotFather): " TELEGRAM_TOKEN
    read -p "Введите ваш Telegram Chat ID: " TELEGRAM_CHAT_ID
    
    # Создаем .env файл
    cat > .env << EOF
# AGI Layer v3.9 Configuration

# Telegram Bot Configuration
TELEGRAM_TOKEN=$TELEGRAM_TOKEN
TELEGRAM_CHAT_IDS=$TELEGRAM_CHAT_ID

# PostgreSQL Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=agi_layer
POSTGRES_USER=agi_user
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# ChromaDB Vector Database
CHROMA_HOST=chromadb
CHROMA_PORT=8000

# Models Configuration
MODELS_PATH=/workspace/models
DOWNLOAD_MODELS_ON_START=true

# System Configuration
LOG_LEVEL=INFO
MAX_WORKERS=4
MEMORY_LIMIT=4GB

# Security
API_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
ALLOWED_IPS=127.0.0.1,172.20.0.0/16

# Features
ENABLE_GPU=false
ENABLE_MONITORING=true
ENABLE_RECOVERY=true
ENABLE_WEB_UI=true

# Model Settings
IMAGE_MODEL=runwayml/stable-diffusion-v1-5
TEXT_MODEL=microsoft/phi-2
VISION_MODEL=Salesforce/blip-image-captioning-base
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Generation Settings
DEFAULT_IMAGE_SIZE=512
DEFAULT_STEPS=50
DEFAULT_GUIDANCE_SCALE=12.0
MAX_GENERATION_TIME=300

# Memory Settings
VECTOR_DIMENSION=384
MAX_MEMORY_SIZE=10000
MEMORY_CLEANUP_INTERVAL=3600
EOF
    
    print_success "Файл .env создан"
}

# Настройка автозапуска
setup_autostart() {
    print_info "Настройка автозапуска системы..."
    
    # Создаем systemd сервис
    sudo tee /etc/systemd/system/agi-layer.service > /dev/null << EOF
[Unit]
Description=AGI Layer v3.9 Multi-Agent System
After=docker.service
Requires=docker.service

[Service]
Type=forking
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Активируем сервис
    sudo systemctl daemon-reload
    sudo systemctl enable agi-layer.service
    
    print_success "Автозапуск настроен"
}

# Настройка брандмауэра
setup_firewall() {
    print_info "Настройка брандмауэра..."
    
    if command -v ufw &> /dev/null; then
        # Разрешаем необходимые порты
        sudo ufw allow ssh
        sudo ufw allow 8501/tcp  # Web UI
        sudo ufw allow 8001:8008/tcp  # Агенты
        
        # Активируем UFW если не активен
        sudo ufw --force enable
        
        print_success "UFW настроен"
    elif command -v firewall-cmd &> /dev/null; then
        # Для CentOS/RHEL
        sudo firewall-cmd --permanent --add-service=ssh
        sudo firewall-cmd --permanent --add-port=8501/tcp
        sudo firewall-cmd --permanent --add-port=8001-8008/tcp
        sudo firewall-cmd --reload
        
        print_success "Firewalld настроен"
    else
        print_warning "Брандмауэр не найден, настройте вручную"
    fi
}

# Загрузка и сборка образов
build_images() {
    print_info "Сборка Docker образов..."
    
    # Проверяем, что мы в правильной директории
    if [[ ! -f "docker-compose.yml" ]]; then
        print_error "docker-compose.yml не найден"
        exit 1
    fi
    
    # Собираем образы
    docker-compose build --no-cache
    
    print_success "Docker образы собраны"
}

# Запуск системы
start_system() {
    print_info "Запуск AGI Layer v3.9..."
    
    # Запускаем в фоновом режиме
    docker-compose up -d
    
    # Ждем запуска
    print_info "Ожидание запуска всех сервисов..."
    sleep 30
    
    # Проверяем статус
    print_info "Статус сервисов:"
    docker-compose ps
    
    print_success "AGI Layer v3.9 запущен!"
}

# Показать информацию о доступе
show_access_info() {
    print_success "=============================================="
    print_success "  AGI Layer v3.9 успешно установлен!"
    print_success "=============================================="
    echo
    print_info "Доступ к системе:"
    echo "  🌐 Web Dashboard: http://localhost:8501"
    echo "  💬 Telegram Bot: активен и готов к работе"
    echo "  📊 MetaAgent API: http://localhost:8001"
    echo
    print_info "Управление системой:"
    echo "  Запуск:    docker-compose up -d"
    echo "  Остановка: docker-compose down"
    echo "  Логи:      docker-compose logs -f"
    echo "  Статус:    docker-compose ps"
    echo
    print_info "Загрузка моделей:"
    echo "  python scripts/download_models.py"
    echo
    print_warning "Первый запуск может занять время для загрузки моделей ИИ"
    echo
}

# Основная функция
main() {
    print_header
    
    # Проверки
    detect_os
    check_root
    
    # Установка
    print_info "Начинаем установку AGI Layer v3.9..."
    
    update_system
    install_dependencies
    setup_swap
    install_docker
    install_docker_compose
    
    # Настройка проекта
    setup_project
    create_env_file
    
    # Сборка и запуск
    build_images
    
    # Настройка системы
    setup_firewall
    setup_autostart
    
    # Запуск
    start_system
    
    # Информация
    show_access_info
    
    print_success "Установка завершена успешно!"
}

# Обработка сигналов
trap 'print_error "Установка прервана"; exit 1' INT TERM

# Запуск
main "$@"