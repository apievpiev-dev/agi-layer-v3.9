# AGI Layer v3.9 - Multi-Agent System Dockerfile
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgcc-s1 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /workspace

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Создаем необходимые директории
RUN mkdir -p /workspace/{agents,models,data,logs,memory,config,services}

# Копируем исходный код
COPY agents/ /workspace/agents/
COPY services/ /workspace/services/
COPY config/ /workspace/config/
COPY scripts/ /workspace/scripts/

# Устанавливаем права доступа
RUN chmod +x /workspace/scripts/*.py || true

# Создаем пользователя для безопасности
RUN groupadd -r agi && useradd -r -g agi agi
RUN chown -R agi:agi /workspace
USER agi

# Переменные окружения
ENV PYTHONPATH="/workspace:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Команда по умолчанию
CMD ["python", "-m", "agents.meta_agent"]