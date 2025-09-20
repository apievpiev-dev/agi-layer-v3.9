@echo off
echo 🤖 AGI Layer v3.9 - Запуск системы
echo.

echo 📝 Создание конфигурации...
call create_env_full.bat

echo.
echo 🚀 Запуск полной системы...
call START_FULL_SYSTEM.bat

echo.
echo 🎉 Система запущена! Проверьте статус:
echo docker-compose ps
echo.
pause
