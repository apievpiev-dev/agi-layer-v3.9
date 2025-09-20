@echo off
echo Переинициализация Git репозитория...

REM Удаление старого .git (если есть)
if exist ".git" (
    echo Удаление старого .git...
    rmdir /s /q .git
)

REM Создание нового репозитория
echo Создание нового Git репозитория...
git init

REM Настройка пользователя
git config user.name "AGI Developer"
git config user.email "agi@example.com"

REM Добавление файлов
git add .

REM Коммит
git commit -m "🚀 Reinit: AGI Layer v3.9 - CPU-only headless AGI infrastructure"

REM Настройка ветки
git branch -M main

REM Подключение к существующему GitHub репозиторию
git remote add origin https://github.com/apievpiev-dev/agi-layer-v3.9.git

echo ✅ Git репозиторий переинициализирован!
echo 🔗 GitHub: https://github.com/apievpiev-dev/agi-layer-v3.9
echo.
echo Для отправки на GitHub выполните:
echo git push -f origin main
echo.
pause
