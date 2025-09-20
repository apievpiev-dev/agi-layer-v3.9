@echo off
echo Инициализация Git репозитория AGI Layer v3.9...

git init
git add .
git commit -m "Initial commit: AGI Layer v3.9 - CPU-only headless AGI infrastructure"

echo Git репозиторий инициализирован!
echo Папка проекта: %CD%
pause

