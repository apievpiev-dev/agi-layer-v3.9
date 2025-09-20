@echo off
echo ========================================
echo    УСТАНОВКА DOCKER ДЛЯ WINDOWS
echo ========================================
echo.

echo Проверяем, установлен ли Docker...
docker --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Docker уже установлен!
    docker --version
    echo.
    echo Проверяем Docker Desktop...
    tasklist /FI "IMAGENAME eq Docker Desktop.exe" 2>NUL | find /I /N "Docker Desktop.exe">NUL
    if "%ERRORLEVEL%"=="0" (
        echo ✅ Docker Desktop запущен
    ) else (
        echo ⚠️  Docker Desktop не запущен
        echo Запускаем Docker Desktop...
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        echo Подождите 30 секунд для запуска...
        timeout /t 30 /nobreak >nul
    )
    goto :test_docker
)

echo ❌ Docker не установлен
echo.

echo ========================================
echo    ИНСТРУКЦИЯ ПО УСТАНОВКЕ DOCKER
echo ========================================
echo.

echo 1. Скачайте Docker Desktop для Windows:
echo    https://www.docker.com/products/docker-desktop/
echo.

echo 2. Или через winget:
echo    winget install Docker.DockerDesktop
echo.

echo 3. После установки перезагрузите компьютер
echo.

echo 4. Запустите Docker Desktop
echo.

echo 5. Включите WSL2 (если не включен):
echo    wsl --install
echo.

echo ========================================
echo    АВТОМАТИЧЕСКАЯ УСТАНОВКА
echo ========================================
echo.

set /p choice="Попробовать автоматическую установку через winget? (y/n): "
if /i "%choice%"=="y" (
    echo Устанавливаем Docker через winget...
    winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
    
    if %errorlevel% == 0 (
        echo ✅ Docker установлен успешно!
        echo Перезагрузите компьютер и запустите Docker Desktop
    ) else (
        echo ❌ Ошибка установки через winget
        echo Скачайте вручную с официального сайта
    )
) else (
    echo Скачайте Docker вручную с https://www.docker.com/products/docker-desktop/
)

goto :end

:test_docker
echo.
echo ========================================
echo    ТЕСТИРОВАНИЕ DOCKER
echo ========================================
echo.

echo Запускаем тестовый контейнер...
docker run --rm hello-world

if %errorlevel% == 0 (
    echo ✅ Docker работает корректно!
) else (
    echo ❌ Проблема с Docker
    echo Проверьте, что Docker Desktop запущен
)

:end
echo.
echo ========================================
echo    ГОТОВО!
echo ========================================
echo.
echo Теперь можно запустить AGI Layer v3.9:
echo docker-compose up -d
echo.
pause

