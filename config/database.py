"""
Конфигурация базы данных AGI Layer v3.9
"""

from config.settings import settings


# SQL схемы для PostgreSQL
CREATE_TABLES_SQL = """
-- Таблица агентов
CREATE TABLE IF NOT EXISTS agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'stopped',
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    memory_usage FLOAT DEFAULT 0.0,
    cpu_usage FLOAT DEFAULT 0.0,
    tasks_completed INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица задач
CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(100) PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    priority INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_name) REFERENCES agents(name)
);

-- Таблица результатов задач
CREATE TABLE IF NOT EXISTS task_results (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Таблица логов агентов
CREATE TABLE IF NOT EXISTS agent_logs (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    level VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица Telegram сообщений
CREATE TABLE IF NOT EXISTS telegram_messages (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    message_text TEXT,
    message_type VARCHAR(20),
    command VARCHAR(50),
    response TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сгенерированных изображений
CREATE TABLE IF NOT EXISTS generated_images (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    prompt TEXT NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- Таблица векторных вложений
CREATE TABLE IF NOT EXISTS vector_embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding_type VARCHAR(50) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица системных метрик
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100),
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблицы для чата с нейросетью
CREATE TABLE IF NOT EXISTS chat_conversations (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    user_name VARCHAR(255),
    message_text TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    is_user_message BOOLEAN DEFAULT TRUE,
    response_text TEXT,
    response_type VARCHAR(50),
    context_data JSONB,
    personality VARCHAR(100),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_time_ms INTEGER
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id BIGINT PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    personality VARCHAR(100) DEFAULT 'helpful_assistant',
    language VARCHAR(10) DEFAULT 'ru',
    context_length INTEGER DEFAULT 10,
    enable_images BOOLEAN DEFAULT TRUE,
    enable_voice BOOLEAN DEFAULT FALSE,
    custom_prompt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_statistics (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    messages_sent INTEGER DEFAULT 0,
    responses_generated INTEGER DEFAULT 0,
    images_processed INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    UNIQUE(chat_id, user_id, date)
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_tasks_agent_status ON tasks(agent_name, status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_agent_logs_agent_time ON agent_logs(agent_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_telegram_messages_chat_time ON telegram_messages(chat_id, created_at);
CREATE INDEX IF NOT EXISTS idx_generated_images_agent_time ON generated_images(agent_name, created_at);
CREATE INDEX IF NOT EXISTS idx_system_metrics_agent_time ON system_metrics(agent_name, timestamp);

-- Индексы для чата
CREATE INDEX IF NOT EXISTS idx_chat_conversations_chat_user ON chat_conversations(chat_id, user_id);
CREATE INDEX IF NOT EXISTS idx_chat_conversations_processed_at ON chat_conversations(processed_at);
CREATE INDEX IF NOT EXISTS idx_chat_statistics_user_date ON chat_statistics(user_id, date);

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""


# Настройки ChromaDB
CHROMA_COLLECTIONS = {
    "memory": {
        "name": "agi_memory",
        "metadata": {"hnsw:space": "cosine"}
    },
    "images": {
        "name": "image_embeddings", 
        "metadata": {"hnsw:space": "cosine"}
    },
    "texts": {
        "name": "text_embeddings",
        "metadata": {"hnsw:space": "cosine"}
    }
}


def get_database_url() -> str:
    """Получение URL для подключения к PostgreSQL"""
    return (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )


def get_async_database_url() -> str:
    """Получение async URL для подключения к PostgreSQL"""
    return (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )

