@echo off
echo 🚀 Создание нового GitHub репозитория для AGI Layer v3.9...

REM Удаление старого .git
if exist ".git" (
    echo Удаление старого .git...
    rmdir /s /q .git
)

REM Инициализация нового репозитория
echo 📦 Инициализация Git...
git init

REM Настройка пользователя
echo 👤 Настройка пользователя...
git config user.name "AGI Developer"
git config user.email "agi@example.com"

REM Добавление файлов
echo 📁 Добавление файлов...
git add .

REM Первый коммит
echo 💾 Создание коммита...
git commit -m "🚀 AGI Layer v3.9 - CPU-only headless AGI infrastructure

✅ Модульная архитектура агентов
✅ Telegram бот интеграция
✅ Docker контейнеризация
✅ CPU-only AI модели
✅ Web UI мониторинг
✅ Автоматическое восстановление

Готово к продакшену! 🎉"

REM Настройка главной ветки
echo 🌿 Настройка ветки main...
git branch -M main

echo ✅ Локальный репозиторий готов!
echo.
echo 📋 Следующие шаги:
echo 1. Идите на https://github.com/new
echo 2. Создайте репозиторий с названием: agi-layer-v3-9
echo 3. Выберите Public
echo 4. НЕ добавляйте README или .gitignore
echo 5. Нажмите Create repository
echo.
echo 6. Затем выполните:
echo    git remote add origin https://github.com/apievpiev-dev/agi-layer-v3-9.git
echo    git push -u origin main
echo.
pause
