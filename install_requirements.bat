@echo off
echo 🐍 Установка Python зависимостей для AGI Layer v3.9...
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.8+
    echo 📥 Скачайте с: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Обновление pip
echo 📦 Обновление pip...
python -m pip install --upgrade pip

REM Установка зависимостей
echo 📦 Установка зависимостей...
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей
    echo 🔧 Попробуйте установить зависимости из requirements-minimal.txt:
    echo    pip install -r requirements-minimal.txt
    pause
    exit /b 1
)

echo ✅ Зависимости установлены успешно!
echo.
echo 🎯 Следующий шаг: настройте .env файл и запустите Docker
pause
