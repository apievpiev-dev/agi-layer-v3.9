#!/bin/bash
# Полное скачивание моделей AGI Layer v3.9

echo "🚀 Скачивание моделей для AGI Layer v3.9"

# Создание папок
mkdir -p models/phi_2
mkdir -p models/stable_diffusion  
mkdir -p models/blip2

echo "📦 Модели будут скачаны при первом запуске агентов"
echo "💾 Это может занять время в зависимости от интернет-соединения"

# Установка дополнительных зависимостей для моделей
pip install torch torchvision transformers diffusers accelerate

echo "✅ Подготовка завершена!"
echo "🤖 Запустите систему: python advanced_telegram_bot.py"
