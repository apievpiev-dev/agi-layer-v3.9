@echo off
chcp 65001 >nul
echo ========================================
echo    ИСПРАВЛЕНИЕ УСТАНОВКИ DOCKER
echo ========================================
echo.

echo 1. Завершаем зависшие процессы...
taskkill /f /im winget.exe 2>nul
taskkill /f /im "Docker Desktop.exe" 2>nul
echo ✅ Процессы завершены

echo.
echo 2. Очищаем временные файлы winget...
rmdir /s /q "%TEMP%\winget" 2>nul
echo ✅ Временные файлы очищены

echo.
echo 3. Проверяем текущую установку Docker...
docker --version 2>nul
if %errorlevel% == 0 (
    echo ✅ Docker уже установлен!
    goto :start_docker
)

echo.
echo 4. Варианты установки Docker:
echo.
echo A) Автоматическая установка через winget
echo B) Скачать вручную с официального сайта
echo C) Установить через Chocolatey
echo.

set /p choice="Выберите вариант (A/B/C): "

if /i "%choice%"=="A" goto :winget_install
if /i "%choice%"=="B" goto :manual_install  
if /i "%choice%"=="C" goto :choco_install
goto :manual_install

:winget_install
echo.
echo Устанавливаем Docker через winget...
winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements --silent
if %errorlevel% == 0 (
    echo ✅ Docker установлен через winget!
    goto :start_docker
) else (
    echo ❌ Ошибка установки через winget
    goto :manual_install
)

:choco_install
echo.
echo Проверяем Chocolatey...
choco --version 2>nul
if %errorlevel% neq 0 (
    echo Chocolatey не установлен. Устанавливаем...
    powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
)

echo Устанавливаем Docker через Chocolatey...
choco install docker-desktop -y
if %errorlevel% == 0 (
    echo ✅ Docker установлен через Chocolatey!
    goto :start_docker
) else (
    echo ❌ Ошибка установки через Chocolatey
    goto :manual_install
)

:manual_install
echo.
echo ========================================
echo    РУЧНАЯ УСТАНОВКА DOCKER
echo ========================================
echo.
echo 1. Откройте браузер и перейдите по ссылке:
echo    https://www.docker.com/products/docker-desktop/
echo.
echo 2. Скачайте Docker Desktop для Windows
echo.
echo 3. Запустите установочный файл
echo.
echo 4. После установки перезагрузите компьютер
echo.
echo 5. Запустите Docker Desktop
echo.
echo 6. Включите WSL2 если потребуется:
echo    wsl --install
echo.
goto :end

:start_docker
echo.
echo ========================================
echo    ЗАПУСК DOCKER DESKTOP
echo ========================================
echo.

echo Проверяем, запущен ли Docker Desktop...
tasklist /FI "IMAGENAME eq Docker Desktop.exe" 2>NUL | find /I /N "Docker Desktop.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo ✅ Docker Desktop уже запущен
) else (
    echo Запускаем Docker Desktop...
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        echo Ожидаем запуска Docker Desktop (60 секунд)...
        timeout /t 60 /nobreak >nul
    ) else (
        echo ❌ Docker Desktop не найден в стандартном расположении
        echo Запустите Docker Desktop вручную
        goto :end
    )
)

echo.
echo ========================================
echo    ТЕСТ DOCKER
echo ========================================
echo.

echo Тестируем Docker...
docker run --rm hello-world
if %errorlevel% == 0 (
    echo ✅ Docker работает корректно!
    echo.
    echo Теперь можно запустить AGI Layer v3.9:
    echo docker-compose up -d
) else (
    echo ❌ Docker не работает
    echo Проверьте, что Docker Desktop полностью загрузился
)

:end
echo.
echo ========================================
echo    ГОТОВО!
echo ========================================
pause

