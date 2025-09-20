@echo off
echo 🔧 Исправление Docker + WSL проблем
echo.

echo 1️⃣ Обновление WSL...
wsl --update

echo.
echo 2️⃣ Перезапуск WSL...
wsl --shutdown
timeout /t 3 /nobreak >nul
wsl

echo.
echo 3️⃣ Проверка версии WSL...
wsl --version

echo.
echo 4️⃣ Запуск Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

echo.
echo ✅ Готово! Подождите 2-3 минуты пока Docker запустится
echo.
pause
